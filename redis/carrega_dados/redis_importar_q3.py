
import redis
import json
import time
from pathlib import Path
from collections import defaultdict

PASTA_TPCH = Path(r"C:\Users\User\Desktop\TPC-H")
TAMANHO_LOTE = 3000

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

# 1. Clientes do segmento BUILDING
clientes = set()

with open(localizar("customer.tbl"), encoding="utf-8") as f:
    for linha in f:
        c = linha.strip().split("|")

        if c[6] == "BUILDING":
            clientes.add(int(c[0]))

print(f"Clientes BUILDING: {len(clientes):,}")

# 2. Pedidos dos clientes BUILDING anteriores a 15/03/1995
pedidos = {}

with open(localizar("orders.tbl"), encoding="utf-8") as f:
    for linha in f:
        c = linha.strip().split("|")

        orderkey = int(c[0])
        custkey = int(c[1])
        orderdate = c[4]

        if custkey in clientes and orderdate < "1995-03-15":
            pedidos[orderkey] = {
                "orderdate": orderdate,
                "shippriority": int(c[7])
            }

print(f"Pedidos candidatos: {len(pedidos):,}")

# 3. Calcular receita dos pedidos
receitas = defaultdict(float)
registros_lineitem = 0

with open(localizar("lineitem.tbl"), encoding="utf-8") as f:
    for linha in f:
        c = linha.strip().split("|")

        orderkey = int(c[0])
        shipdate = c[10]

        if orderkey not in pedidos:
            continue

        if shipdate > "1995-03-15":
            extendedprice = float(c[5])
            discount = float(c[6])

            receitas[orderkey] += (
                extendedprice * (1 - discount)
            )

            registros_lineitem += 1

print(f"Linhas LINEITEM consideradas: {registros_lineitem:,}")
print(f"Pedidos com receita: {len(receitas):,}")

# 4. Inserir os pedidos no Redis
lote = defaultdict(dict)
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


for orderkey, receita in receitas.items():

    pedido = pedidos[orderkey]

    ano = pedido["orderdate"][:4]
    mes = pedido["orderdate"][5:7]

    chave = f"q3:BUILDING:{ano}:{mes}"

    dados = {
        "orderkey": orderkey,
        "revenue": receita,
        "orderdate": pedido["orderdate"],
        "shippriority": pedido["shippriority"]
    }

    membro = json.dumps(
        dados,
        separators=(",", ":")
    )

    # Score = receita
    lote[chave][membro] = receita

    if registros_inseridos + sum(
        len(v) for v in lote.values()
    ) >= TAMANHO_LOTE:
        enviar_lote()

enviar_lote()

fim = time.perf_counter()

print("\n========== IMPORTAÇÃO Q3 ==========")
print(f"Pedidos inseridos: {registros_inseridos:,}")
print(f"Tempo de importação: {fim - inicio:.2f} segundos")

print("\nChaves criadas:")

for chave in sorted(r.scan_iter(match="q3:BUILDING:*")):
    print(f"{chave}: {r.zcard(chave):,} registros")
