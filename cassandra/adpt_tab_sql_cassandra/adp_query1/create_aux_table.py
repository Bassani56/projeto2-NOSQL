from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args
from datetime import date
from decimal import Decimal

ARQUIVO = r"C:\Users\User\Desktop\TPC-H\7C3325E0-B869-4712-A2FF-D89F23465D20-TPC-H-Tool\TPC-H V3.0.1\dbgen\lineitem.tbl"

TAMANHO_LOTE = 10000
CONCORRENCIA = 100

cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("tpch")

insert = session.prepare("""
    INSERT INTO q1_lineitem (
        l_returnflag, l_linestatus, l_shipyear,
        l_shipdate, l_orderkey, l_linenumber,
        l_quantity, l_extendedprice, l_discount, l_tax
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""")

def converter_linha(linha):
    dados = linha.rstrip("\r\n").split("|")

    data_envio = date.fromisoformat(dados[10])

    return (
        dados[8],
        dados[9],
        data_envio.year,
        data_envio,
        int(dados[0]),
        int(dados[1]),
        Decimal(dados[4]),
        Decimal(dados[5]),
        Decimal(dados[6]),
        Decimal(dados[7])
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