#!/usr/bin/env bash
# Executa Q1, Q2 e Q3 no MySQL e mostra o tempo de cada uma.
# Uso: ./executar_queries.sh [q1 q2 q3]   (sem argumentos roda as três)
# Variáveis opcionais: MYSQL_CONTAINER (padrão: mysql), MYSQL_SENHA (padrão: 1234)
set -euo pipefail

cd "$(dirname "$0")"

CONTAINER="${MYSQL_CONTAINER:-mysql}"
SENHA="${MYSQL_SENHA:-1234}"
QUERIES=("$@")
[ ${#QUERIES[@]} -eq 0 ] && QUERIES=(q1 q2 q3)

for q in "${QUERIES[@]}"; do
    echo
    echo "========== ${q^^} - MYSQL =========="
    inicio=$(date +%s%N)
    docker exec -i "$CONTAINER" mysql -uroot -p"$SENHA" --table tpch < "consultas/${q}.sql"
    fim=$(date +%s%N)
    ms=$(( (fim - inicio) / 1000000 ))
    printf 'Tempo de execução (inclui o docker exec): %d.%03d segundos\n' $((ms / 1000)) $((ms % 1000))
done
