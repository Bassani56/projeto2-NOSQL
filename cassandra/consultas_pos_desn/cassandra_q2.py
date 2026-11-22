
from cassandra.cluster import Cluster
from decimal import Decimal
from time import perf_counter

# Conexão com o Cassandra
cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("tpch")

# Tipos de peças com tamanho 15 e final BRASS
tipos_brass = [
    "ECONOMY BURNISHED BRASS",
    "MEDIUM BRUSHED BRASS",
    "ECONOMY PLATED BRASS",
    "PROMO PLATED BRASS",
    "LARGE ANODIZED BRASS",
    "STANDARD ANODIZED BRASS",
    "MEDIUM PLATED BRASS",
    "PROMO ANODIZED BRASS",
    "PROMO BRUSHED BRASS",
    "SMALL BURNISHED BRASS",
    "SMALL BRUSHED BRASS",
    "STANDARD BRUSHED BRASS",
    "PROMO BURNISHED BRASS",
    "ECONOMY POLISHED BRASS",
    "LARGE POLISHED BRASS",
    "LARGE PLATED BRASS",
    "MEDIUM ANODIZED BRASS",
    "ECONOMY BRUSHED BRASS",
    "SMALL ANODIZED BRASS",
    "MEDIUM BURNISHED BRASS",
    "SMALL POLISHED BRASS",
    "ECONOMY ANODIZED BRASS",
    "STANDARD PLATED BRASS",
    "STANDARD POLISHED BRASS",
    "LARGE BRUSHED BRASS",
    "STANDARD BURNISHED BRASS",
    "SMALL PLATED BRASS",
    "PROMO POLISHED BRASS",
    "LARGE BURNISHED BRASS",
    "MEDIUM POLISHED BRASS"
]

# Consulta por partição
consulta = session.prepare("""
    SELECT
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
    FROM q2_parts_supplier
    WHERE p_size = ?
      AND p_type = ?
      AND r_name = ?
""")

# Armazena o menor custo por peça
menores_custos = {}

# Armazena os fornecedores com menor custo
melhores_fornecedores = {}

total_lidos = 0

try:
    inicio = perf_counter()

    # Consulta os 30 tipos de peças
    for tipo in tipos_brass:
        linhas = session.execute(
            consulta,
            (15, tipo, "EUROPE")
        )

        for linha in linhas:
            total_lidos += 1

            partkey = linha.p_partkey
            custo = linha.ps_supplycost

            # Primeiro fornecedor encontrado para a peça
            if partkey not in menores_custos:

                menores_custos[partkey] = custo
                melhores_fornecedores[partkey] = [linha]

            # Encontrou um custo menor
            elif custo < menores_custos[partkey]:

                menores_custos[partkey] = custo
                melhores_fornecedores[partkey] = [linha]

            # Encontrou outro fornecedor com o mesmo custo mínimo
            elif custo == menores_custos[partkey]:

                melhores_fornecedores[partkey].append(linha)

    # Reúne os melhores fornecedores de todas as peças
    resultados = []

    for fornecedores in melhores_fornecedores.values():
        resultados.extend(fornecedores)

    # Ordenação conforme a Q2 original
    resultados.sort(
        key=lambda x: (
            -x.s_acctbal,
            x.n_name,
            x.s_name,
            x.p_partkey
        )
    )

    # Retorna somente os 100 primeiros
    resultados = resultados[:100]

    fim = perf_counter()

    print("\n========== RESULTADO Q2 - CASSANDRA ==========\n")

    for linha in resultados:
        print(
            f"Saldo: {linha.s_acctbal} | "
            f"Fornecedor: {linha.s_name} | "
            f"Nação: {linha.n_name} | "
            f"Peça: {linha.p_partkey} | "
            f"Fabricante: {linha.p_mfgr} | "
            f"Nome da peça: {linha.p_name} | "
            f"Endereço: {linha.s_address} | "
            f"Telefone: {linha.s_phone} | "
            f"Custo: {linha.ps_supplycost}"
        )

    print("\n========== DESEMPENHO ==========")
    print(f"Registros lidos: {total_lidos}")
    print(f"Peças avaliadas: {len(menores_custos)}")
    print(f"Resultados retornados: {len(resultados)}")
    print(f"Tempo de execução: {fim - inicio:.4f} segundos")

finally:
    cluster.shutdown()
