#!/usr/bin/env bash
# Executa os scripts que carregam no Redis as estruturas das queries Q1, Q2 e Q3.
# Uso: ./carregar.sh
# Pasta dos .tbl: variável TPCH_DIR (padrão: ~/Documentos/tpch-sf1)
set -euo pipefail

cd "$(dirname "$0")"

# Usa o ambiente virtual do projeto, se existir
PYTHON=python3
VENV_PY="../../.venv/bin/python"
[ -x "$VENV_PY" ] && PYTHON="$VENV_PY"

SCRIPTS=(
    redis_importar_q1.py
    redis_importar_q2.py
    redis_importar_q3.py
)

for script in "${SCRIPTS[@]}"; do
    echo "=== ${script} ==="
    "$PYTHON" "$script"
done

echo "Carga no Redis concluída."
