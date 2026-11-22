
import redis
import json
import time
from pathlib import Path
from collections import defaultdict

# Configurações
PASTA_TPCH = Path(r"C:\Users\User\Desktop\TPC-H")
TAMANHO_LOTE = 5000

# Conexão com Redis
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

r.ping()
print("Conectado ao Redis!")

# Localiza lineitem.tbl
arquivos = list(PASTA_TPCH.rglob("lineitem.tbl"))

if not arquivos:
    raise FileNotFoundError("lineitem.tbl não encontrado!")

ARQUIVO = arquivos[0]
print(f"Arquivo: {ARQUIVO}")

# Buffer para inserção em lotes
lote = defaultdict(dict)
registros_lidos = 0
registros_inseridos = 0

def enviar_lote():
    global registros_inseridos

    if not lote:
        return

    pipeline = r.pipeline(transaction=False)

    for chave, membros in lote.items():
        pipeline.zadd(chave, membros)

    resultados = pipeline.execute()
    registros_inseridos += sum(resultados)

    lote.clear()


inicio = time.perf_counter()

with open(ARQUIVO, "r", encoding="utf-8") as arquivo:

    for linha in arquivo:
        campos = linha.strip().split("|")

        if len(campos) < 11:
            continue

        orderkey = int(campos[0])
        linenumber = int(campos[3])

        quantity = campos[4]
        extendedprice = campos[5]
        discount = campos[6]
        tax = campos[7]

        returnflag = campos[8]
        linestatus = campos[9]
        shipdate = campos[10]

        # Score no formato YYYYMMDD
        score = int(shipdate.replace("-", ""))

        ano = shipdate[:4]

        # Chave agrupada por flag, status e ano
        chave = f"q1:{returnflag}:{linestatus}:{ano}"

        # Identificador único da linha
        identificador = f"{orderkey}:{linenumber}"

        # Dados necessários para os cálculos da Q1
        dados = {
            "orderkey": orderkey,
            "linenumber": linenumber,
            "quantity": quantity,
            "extendedprice": extendedprice,
            "discount": discount,
            "tax": tax
        }

        membro = json.dumps(dados, separators=(",", ":"))

        lote[chave][membro] = score
        registros_lidos += 1

        if registros_lidos % TAMANHO_LOTE == 0:
            enviar_lote()
            print(f"Registros processados: {registros_lidos:,}")

    # Envia registros restantes
    enviar_lote()

fim = time.perf_counter()

print("\n========== IMPORTAÇÃO Q1 ==========")
print(f"Registros lidos: {registros_lidos:,}")
print(f"Novos registros inseridos: {registros_inseridos:,}")
print(f"Tempo de importação: {fim - inicio:.2f} segundos")

print("\nChaves criadas:")
for chave in sorted(r.scan_iter(match="q1:*")):
    print(f"{chave}: {r.zcard(chave):,} registros")
