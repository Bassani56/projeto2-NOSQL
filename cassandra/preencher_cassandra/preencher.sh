#!/usr/bin/env bash
# Executa os scripts que preenchem o Cassandra (keyspace "tpch") com os .tbl do TPC-H.
# Uso: ./preencher.sh
# Pasta dos .tbl: variável TPCH_DIR (padrão: ~/Documentos/tpch-sf1)
set -euo pipefail

cd "$(dirname "$0")"

# Usa o ambiente virtual do projeto, se existir
PYTHON=python3
VENV_PY="../../.venv/bin/python"
[ -x "$VENV_PY" ] && PYTHON="$VENV_PY"

TABELAS=(region nation supplier customer part partsupp orders lineitem)

for tabela in "${TABELAS[@]}"; do
    echo "=== ${tabela} ==="
    "$PYTHON" "${tabela}_pr_cassandra.py"
done

echo "Todas as tabelas foram preenchidas."
