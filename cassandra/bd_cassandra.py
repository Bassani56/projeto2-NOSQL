from cassandra.cluster import Cluster
from uuid import uuid4

# Conectar ao Cassandra
cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect()


QUERIES = [
    {
        "name": "Q1 - Pricing Summary",
        "sql": """
            SELECT L_RETURNFLAG, L_LINESTATUS,
                SUM(L_QUANTITY) AS sum_qty,
                SUM(L_EXTENDEDPRICE) AS sum_base_price,
                SUM(L_EXTENDEDPRICE*(1-L_DISCOUNT)) AS sum_disc_price,
                SUM(L_EXTENDEDPRICE*(1-L_DISCOUNT)*(1+L_TAX)) AS sum_charge,
                AVG(L_QUANTITY) AS avg_qty,
                AVG(L_EXTENDEDPRICE) AS avg_price,
                AVG(L_DISCOUNT) AS avg_disc,
                COUNT(*) AS count_order
            FROM lineitem
            WHERE L_SHIPDATE <= DATE_SUB('1998-12-01', INTERVAL 90 DAY)
            GROUP BY L_RETURNFLAG, L_LINESTATUS
            ORDER BY L_RETURNFLAG, L_LINESTATUS
        """,
    },
    {
        "name": "Q2 - Minimum Cost Supplier",
        "sql": """
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
            part, 
            supplier, 
            partsupp, 
            nation, 
            region
        WHERE 
            P_PARTKEY=PS_PARTKEY 
            AND S_SUPPKEY=PS_SUPPKEY
              AND P_SIZE=15 
              AND P_TYPE LIKE '%BRASS'
              AND S_NATIONKEY=N_NATIONKEY 
              AND N_REGIONKEY=R_REGIONKEY 
              AND R_NAME='EUROPE'
              AND PS_SUPPLYCOST=(
                  SELECT MIN(PS_SUPPLYCOST) FROM partsupp, supplier, nation, region
                  WHERE P_PARTKEY=PS_PARTKEY AND S_SUPPKEY=PS_SUPPKEY
                    AND S_NATIONKEY=N_NATIONKEY AND N_REGIONKEY=R_REGIONKEY AND R_NAME='EUROPE'
              )
            ORDER BY S_ACCTBAL DESC, N_NAME, S_NAME, P_PARTKEY LIMIT 100
        """,
    },
    {
        "name": "Q3 - Shipping Priority",
        "sql": """
            SELECT L_ORDERKEY, SUM(L_EXTENDEDPRICE*(1-L_DISCOUNT)) AS revenue,
                O_ORDERDATE, O_SHIPPRIORITY
            FROM customer, orders, lineitem
            WHERE C_MKTSEGMENT='BUILDING' AND C_CUSTKEY=O_CUSTKEY
              AND L_ORDERKEY=O_ORDERKEY AND O_ORDERDATE<'1995-03-15'
              AND L_SHIPDATE>'1995-03-15'
            GROUP BY L_ORDERKEY, O_ORDERDATE, O_SHIPPRIORITY
            ORDER BY revenue DESC, O_ORDERDATE LIMIT 10
        """,
    },
]




