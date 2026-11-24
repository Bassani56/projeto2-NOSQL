#!/usr/bin/env bash
# Executa as consultas Q1, Q2 e Q3 no Redis.
# Uso: ./executar_consultas.sh [q1 q2 q3]   (sem argumentos roda as três)
set -euo pipefail

cd "$(dirname "$0")"

# Usa o ambiente virtual do projeto, se existir
PYTHON=python3
VENV_PY="../../.venv/bin/python"
[ -x "$VENV_PY" ] && PYTHON="$VENV_PY"

QUERIES=("$@")
[ ${#QUERIES[@]} -eq 0 ] && QUERIES=(q1 q2 q3)

for q in "${QUERIES[@]}"; do
    echo
    echo "=== redis_${q}.py ==="
    "$PYTHON" "redis_${q}.py"
done
