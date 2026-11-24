import os

import redis
import json
import time
from pathlib import Path
from collections import defaultdict

PASTA_TPCH = Path(os.environ.get("TPCH_DIR", os.path.expanduser("~/Documentos/tpch-sf1")))
TAMANHO_LOTE = 5000

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

r.ping()
print("Conectado ao Redis!")


def localizar(nome):
    arquivos = list(PASTA_TPCH.rglob(nome))
    if not arquivos:
        raise FileNotFoundError(f"{nome} não encontrado")
    return arquivos[0]


inicio = time.perf_counter()

# 1. Identificar a região EUROPE
regioes = {}

with open(localizar("region.tbl"), encoding="utf-8") as f:
    for linha in f:
        c = linha.strip().split("|")
        regioes[int(c[0])] = c[1]

regioes_europa = {
    chave for chave, nome in regioes.items()
    if nome == "EUROPE"
}

# 2. Identificar as nações da EUROPE
nacoes = {}

with open(localizar("nation.tbl"), encoding="utf-8") as f:
    for linha in f:
        c = linha.strip().split("|")
        if int(c[2]) in regioes_europa:
            nacoes[int(c[0])] = c[1]

# 3. Identificar fornecedores da EUROPE
fornecedores = {}

with open(localizar("supplier.tbl"), encoding="utf-8") as f:
    for linha in f:
        c = linha.strip().split("|")

        nationkey = int(c[3])

        if nationkey in nacoes:
            fornecedores[int(c[0])] = {
                "s_name": c[1],
                "s_address": c[2],
                "s_phone": c[4],
                "s_acctbal": c[5],
                "s_comment": c[6],
                "n_name": nacoes[nationkey]
            }

# 4. Identificar peças de tamanho 15
# cujo tipo termina em BRASS
pecas = {}

with open(localizar("part.tbl"), encoding="utf-8") as f:
    for linha in f:
        c = linha.strip().split("|")

        if int(c[5]) == 15 and c[4].endswith("BRASS"):
            pecas[int(c[0])] = {
                "p_type": c[4],
                "p_name": c[1],
                "p_mfgr": c[2]
            }

print(f"Peças encontradas: {len(pecas)}")
print(f"Fornecedores da EUROPE: {len(fornecedores)}")

# 5. Cruzar PARTSUPP e inserir no Redis
lote = defaultdict(dict)
registros_lidos = 0
registros_inseridos = 0


def enviar_lote():
    global registros_inseridos

    if not lote:
        return

    pipe = r.pipeline(transaction=False)

    for chave, membros in lote.items():
        pipe.zadd(chave, membros)

    resultados = pipe.execute()
    registros_inseridos += sum(resultados)

    lote.clear()


with open(localizar("partsupp.tbl"), encoding="utf-8") as f:

    for linha in f:
        c = linha.strip().split("|")

        partkey = int(c[0])
        suppkey = int(c[1])

        registros_lidos += 1

        if partkey not in pecas:
            continue

        if suppkey not in fornecedores:
            continue

        p = pecas[partkey]
        s = fornecedores[suppkey]

        supplycost = c[3]

        dados = {
            "p_partkey": partkey,
            "p_type": p["p_type"],
            "p_name": p["p_name"],
            "p_mfgr": p["p_mfgr"],
            "ps_suppkey": suppkey,
            "ps_supplycost": supplycost,
            "s_name": s["s_name"],
            "s_address": s["s_address"],
            "s_phone": s["s_phone"],
            "s_acctbal": s["s_acctbal"],
            "s_comment": s["s_comment"],
            "n_name": s["n_name"]
        }

        chave = f"q2:15:{p['p_type']}:EUROPE"

        membro = json.dumps(
            dados,
            separators=(",", ":")
        )

        lote[chave][membro] = float(supplycost)

        if registros_lidos % TAMANHO_LOTE == 0:
            enviar_lote()
            print(f"PARTSUPP lidos: {registros_lidos:,}")

enviar_lote()

fim = time.perf_counter()

print("\n========== IMPORTAÇÃO Q2 ==========")
print(f"Registros PARTSUPP lidos: {registros_lidos:,}")
print(f"Registros inseridos: {registros_inseridos:,}")
print(f"Tipos de peças encontrados: {len(set(
    p['p_type'] for p in pecas.values()
))}")
print(f"Tempo de importação: {fim - inicio:.2f} segundos")

print("\nChaves criadas:")
for chave in sorted(r.scan_iter(match="q2:15:*:EUROPE")):
    print(f"{chave}: {r.zcard(chave):,} registros")
