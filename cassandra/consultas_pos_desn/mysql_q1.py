
import mysql.connector
from time import perf_counter

conexao = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="1234",
    database="tpch"
)

cursor = conexao.cursor()

consulta = """
    SELECT
        L_RETURNFLAG,
        L_LINESTATUS,
        SUM(L_QUANTITY) AS SUM_QTY,
        SUM(L_EXTENDEDPRICE) AS SUM_BASE_PRICE,
        SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS SUM_DISC_PRICE,
        SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT) * (1 + L_TAX)) AS SUM_CHARGE,
        AVG(L_QUANTITY) AS AVG_QTY,
        AVG(L_EXTENDEDPRICE) AS AVG_PRICE,
        AVG(L_DISCOUNT) AS AVG_DISC,
        COUNT(*) AS COUNT_ORDER
    FROM lineitem
    WHERE L_SHIPDATE <= DATE_SUB('1998-12-01', INTERVAL 90 DAY)
    GROUP BY L_RETURNFLAG, L_LINESTATUS
    ORDER BY L_RETURNFLAG, L_LINESTATUS;
"""

try:
    inicio = perf_counter()

    cursor.execute(consulta)
    resultados = cursor.fetchall()

    fim = perf_counter()

    print("\n========== RESULTADO Q1 - MYSQL ==========\n")

    for linha in resultados:
        print(linha)

    print("\n========== DESEMPENHO ==========")
    print(f"Registros retornados: {len(resultados)}")
    print(f"Tempo de execução: {fim - inicio:.4f} segundos")

finally:
    cursor.close()
    conexao.close()
