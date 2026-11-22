
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args
from decimal import Decimal

ARQUIVO = r"C:\Users\User\Desktop\TPC-H\7C3325E0-B869-4712-A2FF-D89F23465D20-TPC-H-Tool\TPC-H V3.0.1\dbgen\part.tbl"

TAMANHO_LOTE = 10000
CONCORRENCIA = 100

cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("tpch")

insert = session.prepare("""
    INSERT INTO part (
        p_partkey, p_name, p_mfgr, p_brand,
        p_type, p_size, p_container,
        p_retailprice, p_comment
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""")

def converter_linha(linha):
    dados = linha.rstrip("\r\n").split("|")

    return (
        int(dados[0]),
        dados[1],
        dados[2],
        dados[3],
        dados[4],
        int(dados[5]),
        dados[6],
        Decimal(dados[7]),
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
