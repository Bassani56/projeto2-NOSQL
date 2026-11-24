import os
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args
from decimal import Decimal

PASTA = os.environ.get("TPCH_DIR", os.path.expanduser("~/Documentos/tpch-sf1"))

ARQUIVO_PART = PASTA + "/part.tbl"
ARQUIVO_SUPPLIER = PASTA + "/supplier.tbl"
ARQUIVO_NATION = PASTA + "/nation.tbl"
ARQUIVO_REGION = PASTA + "/region.tbl"
ARQUIVO_PARTSUPP = PASTA + "/partsupp.tbl"

TAMANHO_LOTE = 10000
CONCORRENCIA = 100


# 1. Carregar as peças
print("Carregando peças...")

parts = {}

with open(ARQUIVO_PART, "r", encoding="utf-8") as arquivo:
    for linha in arquivo:
        dados = linha.rstrip("\r\n").split("|")

        parts[int(dados[0])] = (
            dados[1],       # p_name
            dados[2],       # p_mfgr
            dados[4],       # p_type
            int(dados[5])   # p_size
        )

print(f"{len(parts):,} peças carregadas.")


# 2. Carregar os fornecedores
print("Carregando fornecedores...")

suppliers = {}

with open(ARQUIVO_SUPPLIER, "r", encoding="utf-8") as arquivo:
    for linha in arquivo:
        dados = linha.rstrip("\r\n").split("|")

        suppliers[int(dados[0])] = (
            dados[1],             # s_name
            dados[2],             # s_address
            int(dados[3]),        # s_nationkey
            dados[4],             # s_phone
            Decimal(dados[5])     # s_acctbal
        )

print(f"{len(suppliers):,} fornecedores carregados.")


# 3. Carregar as regiões
print("Carregando regiões...")

regions = {}

with open(ARQUIVO_REGION, "r", encoding="utf-8") as arquivo:
    for linha in arquivo:
        dados = linha.rstrip("\r\n").split("|")

        regions[int(dados[0])] = dados[1]


# 4. Relacionar nações com regiões
print("Carregando nações...")

nations = {}

with open(ARQUIVO_NATION, "r", encoding="utf-8") as arquivo:
    for linha in arquivo:
        dados = linha.rstrip("\r\n").split("|")

        nationkey = int(dados[0])
        nation_name = dados[1]
        regionkey = int(dados[2])

        nations[nationkey] = (
            nation_name,
            regions[regionkey]
        )

print(f"{len(nations):,} nações carregadas.")


# 5. Conectar ao Cassandra
cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("tpch")

insert = session.prepare("""
    INSERT INTO q2_parts_supplier (
        p_size,
        p_type,
        r_name,
        ps_supplycost,
        p_partkey,
        ps_suppkey,
        p_name,
        p_mfgr,
        s_name,
        s_address,
        s_phone,
        s_acctbal,
        n_name
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""")


# 6. Percorrer partsupp e montar os relacionamentos
print("\nIniciando inserção no Cassandra...")

lote = []
total = 0

try:
    with open(ARQUIVO_PARTSUPP, "r", encoding="utf-8") as arquivo:

        for linha in arquivo:
            if not linha.strip():
                continue

            dados = linha.rstrip("\r\n").split("|")

            partkey = int(dados[0])
            suppkey = int(dados[1])

            # Buscar a peça
            nome_peca, fabricante, tipo, tamanho = parts[partkey]

            # Buscar o fornecedor
            nome_fornecedor, endereco, nationkey, telefone, saldo = suppliers[suppkey]

            # Buscar nação e região
            nome_nacao, nome_regiao = nations[nationkey]

            lote.append((
                tamanho,
                tipo,
                nome_regiao,
                Decimal(dados[3]),
                partkey,
                suppkey,
                nome_peca,
                fabricante,
                nome_fornecedor,
                endereco,
                telefone,
                saldo,
                nome_nacao
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

    print(f"\nImportação concluída! Total: {total:,} registros.")

finally:
    cluster.shutdown()