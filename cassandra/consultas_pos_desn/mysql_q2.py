
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
        S_ACCTBAL,
        S_NAME,
        N_NAME,
        P_PARTKEY,
        P_MFGR,
        S_ADDRESS,
        S_PHONE,
        S_COMMENT
    FROM
        PART,
        SUPPLIER,
        PARTSUPP,
        NATION,
        REGION
    WHERE
        P_PARTKEY = PS_PARTKEY
        AND S_SUPPKEY = PS_SUPPKEY
        AND P_SIZE = 15
        AND P_TYPE LIKE '%BRASS'
        AND S_NATIONKEY = N_NATIONKEY
        AND N_REGIONKEY = R_REGIONKEY
        AND R_NAME = 'EUROPE'
        AND PS_SUPPLYCOST = (
            SELECT MIN(PS2.PS_SUPPLYCOST)
            FROM PARTSUPP PS2,
                 SUPPLIER S2,
                 NATION N2,
                 REGION R2
            WHERE
                P_PARTKEY = PS2.PS_PARTKEY
                AND S2.S_SUPPKEY = PS2.PS_SUPPKEY
                AND S2.S_NATIONKEY = N2.N_NATIONKEY
                AND N2.N_REGIONKEY = R2.R_REGIONKEY
                AND R2.R_NAME = 'EUROPE'
        )
    ORDER BY
        S_ACCTBAL DESC,
        N_NAME,
        S_NAME,
        P_PARTKEY
    LIMIT 100;
"""

try:
    inicio = perf_counter()

    cursor.execute(consulta)
    resultados = cursor.fetchall()

    fim = perf_counter()

    print("\n========== RESULTADO Q2 - MYSQL ==========\n")

    for linha in resultados:
        print(linha)

    print("\n========== DESEMPENHO ==========")
    print(f"Registros retornados: {len(resultados)}")
    print(f"Tempo de execução: {fim - inicio:.4f} segundos")

finally:
    cursor.close()
    conexao.close()
