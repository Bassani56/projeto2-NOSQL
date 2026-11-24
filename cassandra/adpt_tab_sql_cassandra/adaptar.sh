#!/usr/bin/env bash
# Executa os scripts que montam as tabelas desnormalizadas (Q1, Q2 e Q3) no Cassandra.
# Requer as tabelas q1_lineitem, q2_parts_supplier e q3_orders (create_tables/create_aux_tables.cql).
# Uso: ./adaptar.sh
# Pasta dos .tbl: variável TPCH_DIR (padrão: ~/Documentos/tpch-sf1)
set -euo pipefail

cd "$(dirname "$0")"

# Usa o ambiente virtual do projeto, se existir
PYTHON=python3
VENV_PY="../../.venv/bin/python"
[ -x "$VENV_PY" ] && PYTHON="$VENV_PY"

SCRIPTS=(
    adp_query1/create_aux_table.py
    adp_query2/apt_query2.py
    adp_query3/adp_query3.py
)

for script in "${SCRIPTS[@]}"; do
    echo "=== ${script} ==="
    "$PYTHON" "$script"
done

echo "Todas as tabelas auxiliares foram preenchidas."
