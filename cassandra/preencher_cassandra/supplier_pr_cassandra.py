import os

from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args
from decimal import Decimal
from datetime import date

ARQUIVO = os.path.join(os.environ.get("TPCH_DIR", os.path.expanduser("~/Documentos/tpch-sf1")), "supplier.tbl")

TAMANHO_LOTE = 10000
CONCORRENCIA = 100

cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("tpch")

insert = session.prepare("""
    INSERT INTO supplier (
        s_suppkey, s_name, s_address, s_nationkey, s_phone, s_acctbal, s_comment
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
""")


def converter_linha(linha):
    dados = linha.rstrip("\r\n").split("|")

    return (
        int(dados[0]),
        dados[1],
        dados[2],
        int(dados[3]),
        dados[4],
        Decimal(dados[5]),
        dados[6]
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
