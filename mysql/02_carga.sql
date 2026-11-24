-- Carga dos .tbl do TPC-H. O container precisa ter a pasta dos .tbl montada em
-- /tpch (o setup_mysql.sh faz isso).
-- Cada linha do dbgen termina com "|", então há uma coluna extra lida em @fim.

USE tpch;

SET unique_checks = 0;
SET foreign_key_checks = 0;

LOAD DATA INFILE '/tpch/region.tbl' INTO TABLE region
FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n'
(r_regionkey, r_name, r_comment, @fim);

LOAD DATA INFILE '/tpch/nation.tbl' INTO TABLE nation
FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n'
(n_nationkey, n_name, n_regionkey, n_comment, @fim);

LOAD DATA INFILE '/tpch/supplier.tbl' INTO TABLE supplier
FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n'
(s_suppkey, s_name, s_address, s_nationkey, s_phone, s_acctbal, s_comment, @fim);

LOAD DATA INFILE '/tpch/customer.tbl' INTO TABLE customer
FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n'
(c_custkey, c_name, c_address, c_nationkey, c_phone, c_acctbal, c_mktsegment, c_comment, @fim);

LOAD DATA INFILE '/tpch/part.tbl' INTO TABLE part
FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n'
(p_partkey, p_name, p_mfgr, p_brand, p_type, p_size, p_container, p_retailprice, p_comment, @fim);

LOAD DATA INFILE '/tpch/partsupp.tbl' INTO TABLE partsupp
FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n'
(ps_partkey, ps_suppkey, ps_availqty, ps_supplycost, ps_comment, @fim);

LOAD DATA INFILE '/tpch/orders.tbl' INTO TABLE orders
FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n'
(o_orderkey, o_custkey, o_orderstatus, o_totalprice, o_orderdate, o_orderpriority, o_clerk, o_shippriority, o_comment, @fim);

LOAD DATA INFILE '/tpch/lineitem.tbl' INTO TABLE lineitem
FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n'
(l_orderkey, l_partkey, l_suppkey, l_linenumber, l_quantity, l_extendedprice, l_discount, l_tax,
 l_returnflag, l_linestatus, l_shipdate, l_commitdate, l_receiptdate, l_shipinstruct, l_shipmode, l_comment, @fim);

SET unique_checks = 1;
SET foreign_key_checks = 1;

SELECT 'region' AS tabela, COUNT(*) AS linhas FROM region
UNION ALL SELECT 'nation',   COUNT(*) FROM nation
UNION ALL SELECT 'supplier', COUNT(*) FROM supplier
UNION ALL SELECT 'customer', COUNT(*) FROM customer
UNION ALL SELECT 'part',     COUNT(*) FROM part
UNION ALL SELECT 'partsupp', COUNT(*) FROM partsupp
UNION ALL SELECT 'orders',   COUNT(*) FROM orders
UNION ALL SELECT 'lineitem', COUNT(*) FROM lineitem;
