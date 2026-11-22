from cassandra.cluster import Cluster
from datetime import date
from time import perf_counter

cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("tpch")

consulta = session.prepare("""
    SELECT o_orderkey, o_orderdate, revenue, o_shippriority
    FROM q3_orders
    WHERE c_mktsegment = ?
      AND o_orderyear = ?
      AND o_ordermonth = ?
""")

resultado = []
total_lidos = 0

try:
    inicio = perf_counter()

    # A Q3 considera pedidos anteriores a 15/03/1995.
    # Portanto, precisamos consultar os anos de 1992 a 1995.
    for ano in range(1992, 1996):
        for mes in range(1, 13):

            linhas = session.execute(
                consulta,
                ("BUILDING", ano, mes)
            )

            for linha in linhas:
                total_lidos += 1

                resultado.append({
                    "orderkey": linha.o_orderkey,
                    "orderdate": linha.o_orderdate,
                    "revenue": linha.revenue,
                    "shippriority": linha.o_shippriority
                })

    # Ordenar conforme a Q3 original:
    # receita decrescente, data crescente e pedido crescente.
    resultado.sort(
        key=lambda x: (
            -x["revenue"],
            x["orderdate"]
        )
    )

    resultado = resultado[:10]

    fim = perf_counter()

    print("\n========== RESULTADO Q3 ==========")

    for item in resultado:
        print(
            f"Pedido: {item['orderkey']} | "
            f"Data: {item['orderdate']} | "
            f"Receita: {item['revenue']} | "
            f"Prioridade: {item['shippriority']}"
        )

    print(f"\nRegistros lidos: {total_lidos}")
    print(f"Resultados retornados: {len(resultado)}")
    print(f"Tempo de execução: {fim - inicio:.4f} segundos")

finally:
    cluster.shutdown()
