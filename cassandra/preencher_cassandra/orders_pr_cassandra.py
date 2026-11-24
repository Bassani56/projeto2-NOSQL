import os

from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args
from decimal import Decimal
from datetime import date

ARQUIVO = os.path.join(os.environ.get("TPCH_DIR", os.path.expanduser("~/Documentos/tpch-sf1")), "orders.tbl")

TAMANHO_LOTE = 10000
CONCORRENCIA = 100

cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("tpch")

insert = session.prepare("""
    INSERT INTO orders (
        o_orderkey, o_custkey, o_orderstatus, o_totalprice, o_orderdate, o_orderpriority, o_clerk, o_shippriority, o_comment
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""")
def converter_linha(linha):
    dados = linha.rstrip("\r\n").split("|")

    return (
        int(dados[0]),
        int(dados[1]),
        dados[2],
        Decimal(dados[3]),
        date.fromisoformat(dados[4]),
        dados[5],
        dados[6],
        int(dados[7]),
        dados[8]
    )

lote = []
total = 0

try:
    with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            if not linha.strip():
                continue

            lote.append(converter_linha(linha))

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

    print(f"\nImportação concluída! Total: {total:,} registros.")

finally:
    cluster.shutdown()
