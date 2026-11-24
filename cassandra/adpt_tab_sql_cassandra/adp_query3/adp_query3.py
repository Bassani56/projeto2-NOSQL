import os

from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args
from datetime import date
from decimal import Decimal

PASTA = os.environ.get("TPCH_DIR", os.path.expanduser("~/Documentos/tpch-sf1"))

ARQUIVO_CUSTOMER = PASTA + "/customer.tbl"
ARQUIVO_ORDERS = PASTA + "/orders.tbl"
ARQUIVO_LINEITEM = PASTA + "/lineitem.tbl"

DATA_CORTE = date(1995, 3, 15)

TAMANHO_LOTE = 10000
CONCORRENCIA = 100

# 1. Carregar clientes do segmento BUILDING
print("Carregando clientes BUILDING...")

clientes = set()

with open(ARQUIVO_CUSTOMER, "r", encoding="utf-8") as arquivo:
    for linha in arquivo:
        dados = linha.rstrip("\r\n").split("|")

        if dados[6] == "BUILDING":
            clientes.add(int(dados[0]))

print(f"{len(clientes):,} clientes carregados.")


# 2. Carregar pedidos desses clientes anteriores à data de corte
print("\nCarregando pedidos...")

pedidos = {}

with open(ARQUIVO_ORDERS, "r", encoding="utf-8") as arquivo:
    for linha in arquivo:
        dados = linha.rstrip("\r\n").split("|")

        orderkey = int(dados[0])
        custkey = int(dados[1])
        orderdate = date.fromisoformat(dados[4])

        if custkey in clientes and orderdate < DATA_CORTE:
            pedidos[orderkey] = {
                "data": orderdate,
                "ano": orderdate.year,
                "mes": orderdate.month,
                "prioridade": int(dados[7]),
                "receita": Decimal("0")
            }

print(f"{len(pedidos):,} pedidos encontrados.")


# 3. Percorrer lineitem e calcular a receita dos pedidos
print("\nCalculando receitas...")

with open(ARQUIVO_LINEITEM, "r", encoding="utf-8") as arquivo:
    for linha in arquivo:
        dados = linha.rstrip("\r\n").split("|")

        orderkey = int(dados[0])

        if orderkey not in pedidos:
            continue

        shipdate = date.fromisoformat(dados[10])

        if shipdate > DATA_CORTE:
            extendedprice = Decimal(dados[5])
            discount = Decimal(dados[6])

            receita = extendedprice * (Decimal("1") - discount)

            pedidos[orderkey]["receita"] += receita

print("Cálculo das receitas concluído.")


# 4. Conectar ao Cassandra
cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("tpch")

insert = session.prepare("""
    INSERT INTO q3_orders (
        c_mktsegment,
        o_orderyear,
        o_ordermonth,
        o_orderdate,
        o_orderkey,
        revenue,
        o_shippriority
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
""")


# 5. Inserir pedidos agregados no Cassandra
print("\nIniciando inserção no Cassandra...")

lote = []
total = 0

try:
    for orderkey, pedido in pedidos.items():

        # Pedidos sem linhas elegíveis não entram no resultado da Q3
        if pedido["receita"] == 0:
            continue

        lote.append((
            "BUILDING",
            pedido["ano"],
            pedido["mes"],
            pedido["data"],
            orderkey,
            pedido["receita"],
            pedido["prioridade"]
        ))

        if len(lote) >= TAMANHO_LOTE:
            execute_concurrent_with_args(
                session,
                insert,
                lote,
                concurrency=CONCORRENCIA,
                raise_on_first_error=True
            )

            total += len(lote)
            print(f"{total:,} registros inseridos")
            lote.clear()

    if lote:
        execute_concurrent_with_args(
            session,
            insert,
            lote,
            concurrency=CONCORRENCIA,
            raise_on_first_error=True
        )

        total += len(lote)

    print("\nImportação concluída!")
    print(f"Total de pedidos inseridos: {total:,}")

finally:
    cluster.shutdown()
