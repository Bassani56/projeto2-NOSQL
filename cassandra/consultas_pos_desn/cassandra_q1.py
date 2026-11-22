
from cassandra.cluster import Cluster
from decimal import Decimal
from datetime import date
from time import perf_counter

# Conexão com o Cassandra
cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("tpch")

# Data limite da Q1
data_limite = date(1998, 9, 2)

# Consulta por partição
consulta = session.prepare("""
    SELECT
        l_returnflag,
        l_linestatus,
        l_quantity,
        l_extendedprice,
        l_discount,
        l_tax
    FROM q1_lineitem
    WHERE l_returnflag = ?
      AND l_linestatus = ?
      AND l_shipyear = ?
      AND l_shipdate <= ?
""")

# Estrutura para armazenar as agregações
agregados = {}

try:
    inicio = perf_counter()

    # Percorre as combinações de flags e status
    for returnflag in ["A", "N", "R"]:
        for linestatus in ["F", "O"]:

            chave = (returnflag, linestatus)

            agregados[chave] = {
                "sum_qty": Decimal("0"),
                "sum_base_price": Decimal("0"),
                "sum_disc_price": Decimal("0"),
                "sum_charge": Decimal("0"),
                "sum_discount": Decimal("0"),
                "count": 0
            }

            # Percorre os anos existentes no TPC-H SF1
            for ano in range(1992, 1999):

                linhas = session.execute(
                    consulta,
                    (
                        returnflag,
                        linestatus,
                        ano,
                        data_limite
                    )
                )

                for linha in linhas:
                    quantidade = linha.l_quantity
                    preco = linha.l_extendedprice
                    desconto = linha.l_discount
                    imposto = linha.l_tax

                    agregado = agregados[chave]

                    agregado["sum_qty"] += quantidade
                    agregado["sum_base_price"] += preco

                    agregado["sum_disc_price"] += (
                        preco * (Decimal("1") - desconto)
                    )

                    agregado["sum_charge"] += (
                        preco
                        * (Decimal("1") - desconto)
                        * (Decimal("1") + imposto)
                    )

                    agregado["sum_discount"] += desconto
                    agregado["count"] += 1

    # Ordenação e cálculo das médias
    resultados = []

    for (returnflag, linestatus), dados in sorted(agregados.items()):

        quantidade_registros = dados["count"]

        if quantidade_registros == 0:
            continue

        resultados.append({
            "returnflag": returnflag,
            "linestatus": linestatus,
            "sum_qty": dados["sum_qty"],
            "sum_base_price": dados["sum_base_price"],
            "sum_disc_price": dados["sum_disc_price"],
            "sum_charge": dados["sum_charge"],
            "avg_qty": dados["sum_qty"] / quantidade_registros,
            "avg_price": dados["sum_base_price"] / quantidade_registros,
            "avg_disc": dados["sum_discount"] / quantidade_registros,
            "count_order": quantidade_registros
        })

    fim = perf_counter()

    print("\n========== RESULTADO Q1 - CASSANDRA ==========\n")

    for item in resultados:
        print(f"Return Flag: {item['returnflag']}")
        print(f"Line Status: {item['linestatus']}")
        print(f"SUM_QTY: {item['sum_qty']}")
        print(f"SUM_BASE_PRICE: {item['sum_base_price']}")
        print(f"SUM_DISC_PRICE: {item['sum_disc_price']}")
        print(f"SUM_CHARGE: {item['sum_charge']}")
        print(f"AVG_QTY: {item['avg_qty']}")
        print(f"AVG_PRICE: {item['avg_price']}")
        print(f"AVG_DISC: {item['avg_disc']}")
        print(f"COUNT_ORDER: {item['count_order']}")
        print("----------------------------------------")

    print("\n========== DESEMPENHO ==========")
    print(f"Grupos retornados: {len(resultados)}")
    print(f"Tempo de execução: {fim - inicio:.4f} segundos")

finally:
    cluster.shutdown()
