-- Tabelas desnormalizadas das queries Q1, Q2 e Q3, alinhadas com os scripts de
-- cassandra/adpt_tab_sql_cassandra/ e com as consultas de cassandra/consultas_pos_desn/.
-- Requer o keyspace tpch (create_base_tables.cql).

USE tpch;

CREATE TABLE IF NOT EXISTS q1_lineitem (
    l_returnflag TEXT,
    l_linestatus TEXT,
    l_shipyear INT,
    l_shipdate DATE,
    l_orderkey INT,
    l_linenumber INT,
    l_quantity DECIMAL,
    l_extendedprice DECIMAL,
    l_discount DECIMAL,
    l_tax DECIMAL,
    PRIMARY KEY (
        (l_returnflag, l_linestatus, l_shipyear),
        l_shipdate,
        l_orderkey,
        l_linenumber
    )
);

CREATE TABLE IF NOT EXISTS q2_parts_supplier (
    p_size INT,
    p_type TEXT,
    r_name TEXT,
    ps_supplycost DECIMAL,
    p_partkey INT,
    ps_suppkey INT,
    p_name TEXT,
    p_mfgr TEXT,
    s_name TEXT,
    s_address TEXT,
    s_phone TEXT,
    s_acctbal DECIMAL,
    n_name TEXT,
    PRIMARY KEY (
        (p_size, p_type, r_name),
        ps_supplycost,
        p_partkey,
        ps_suppkey
    )
) WITH CLUSTERING ORDER BY (ps_supplycost ASC);

CREATE TABLE IF NOT EXISTS q3_orders (
    c_mktsegment TEXT,
    o_orderyear INT,
    o_ordermonth INT,
    o_orderdate DATE,
    o_orderkey INT,
    revenue DECIMAL,
    o_shippriority INT,
    PRIMARY KEY (
        (c_mktsegment, o_orderyear, o_ordermonth),
        o_orderdate,
        o_orderkey
    )
);
