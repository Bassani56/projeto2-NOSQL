
import mysql.connector
from time import perf_counter

# Conexão com o MySQL
conexao = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="tpch"
)

cursor = conexao.cursor()

consulta = """
    SELECT
        L_ORDERKEY,
        SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS revenue,
        O_ORDERDATE,
        O_SHIPPRIORITY
    FROM customer, orders, lineitem
    WHERE C_MKTSEGMENT = 'BUILDING'
      AND C_CUSTKEY = O_CUSTKEY
      AND L_ORDERKEY = O_ORDERKEY
      AND O_ORDERDATE < '1995-03-15'
      AND L_SHIPDATE > '1995-03-15'
    GROUP BY
        L_ORDERKEY,
        O_ORDERDATE,
        O_SHIPPRIORITY
    ORDER BY
        revenue DESC,
        O_ORDERDATE
    LIMIT 10;
"""

try:
    inicio = perf_counter()

    cursor.execute(consulta)
    resultados = cursor.fetchall()

    fim = perf_counter()

    print("\n========== RESULTADO Q3 - MYSQL ==========\n")

    for linha in resultados:
        orderkey, revenue, orderdate, shippriority = linha

        print(
            f"Pedido: {orderkey} | "
            f"Receita: {revenue} | "
            f"Data: {orderdate} | "
            f"Prioridade: {shippriority}"
        )

    print("\n========== DESEMPENHO ==========")
    print(f"Registros retornados: {len(resultados)}")
    print(f"Tempo de execução: {fim - inicio:.4f} segundos")

finally:
    cursor.close()
    conexao.close()
