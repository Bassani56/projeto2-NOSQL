-- Keyspace e as 8 tabelas base do TPC-H (preenchidas por cassandra/preencher_cassandra/).
-- Tipos: String -> TEXT, Int -> INT, Decimal -> DECIMAL, Data -> DATE.
-- SimpleStrategy com replication_factor 1 serve para um único nó (Docker local).

CREATE KEYSPACE IF NOT EXISTS tpch
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE tpch;

CREATE TABLE IF NOT EXISTS region (
    r_regionkey INT PRIMARY KEY,
    r_name TEXT,
    r_comment TEXT
);

CREATE TABLE IF NOT EXISTS nation (
    n_nationkey INT PRIMARY KEY,
    n_name TEXT,
    n_regionkey INT,
    n_comment TEXT
);

CREATE TABLE IF NOT EXISTS supplier (
    s_suppkey INT PRIMARY KEY,
    s_name TEXT,
    s_address TEXT,
    s_nationkey INT,
    s_phone TEXT,
    s_acctbal DECIMAL,
    s_comment TEXT
);

CREATE TABLE IF NOT EXISTS customer (
    c_custkey INT PRIMARY KEY,
    c_name TEXT,
    c_address TEXT,
    c_nationkey INT,
    c_phone TEXT,
    c_acctbal DECIMAL,
    c_mktsegment TEXT,
    c_comment TEXT
);

CREATE TABLE IF NOT EXISTS part (
    p_partkey INT PRIMARY KEY,
    p_name TEXT,
    p_mfgr TEXT,
    p_brand TEXT,
    p_type TEXT,
    p_size INT,
    p_container TEXT,
    p_retailprice DECIMAL,
    p_comment TEXT
);

CREATE TABLE IF NOT EXISTS partsupp (
    ps_partkey INT,
    ps_suppkey INT,
    ps_availqty INT,
    ps_supplycost DECIMAL,
    ps_comment TEXT,
    PRIMARY KEY ((ps_partkey), ps_suppkey)
);

CREATE TABLE IF NOT EXISTS orders (
    o_orderkey INT PRIMARY KEY,
    o_custkey INT,
    o_orderstatus TEXT,
    o_totalprice DECIMAL,
    o_orderdate DATE,
    o_orderpriority TEXT,
    o_clerk TEXT,
    o_shippriority INT,
    o_comment TEXT
);

CREATE TABLE IF NOT EXISTS lineitem (
    l_orderkey INT,
    l_partkey INT,
    l_suppkey INT,
    l_linenumber INT,
    l_quantity DECIMAL,
    l_extendedprice DECIMAL,
    l_discount DECIMAL,
    l_tax DECIMAL,
    l_returnflag TEXT,
    l_linestatus TEXT,
    l_shipdate DATE,
    l_commitdate DATE,
    l_receiptdate DATE,
    l_shipinstruct TEXT,
    l_shipmode TEXT,
    l_comment TEXT,
    PRIMARY KEY ((l_orderkey), l_linenumber)
);
