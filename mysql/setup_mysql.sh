#!/usr/bin/env bash
# Sobe o MySQL em Docker, cria as 8 tabelas do TPC-H e carrega os .tbl.
# Uso: ./setup_mysql.sh
# Variáveis opcionais: MYSQL_CONTAINER (padrão: mysql), MYSQL_SENHA (padrão: 1234)
# Pasta dos .tbl: variável TPCH_DIR (padrão: ~/Documentos/tpch-sf1)
set -euo pipefail

cd "$(dirname "$0")"

TPCH_DIR="${TPCH_DIR:-$HOME/Documentos/tpch-sf1}"
CONTAINER="${MYSQL_CONTAINER:-mysql}"
SENHA="${MYSQL_SENHA:-1234}"   # padrão igual ao de cassandra/consultas_pos_desn/mysql_q*.py

if [ ! -f "$TPCH_DIR/lineitem.tbl" ]; then
    echo "Arquivos .tbl não encontrados em $TPCH_DIR" >&2
    exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    echo "Container '$CONTAINER' já existe. Iniciando..."
    docker start "$CONTAINER" >/dev/null
else
    echo "Criando container '$CONTAINER'..."
    docker run -d --name "$CONTAINER" -p 3306:3306 \
        -e MYSQL_ROOT_PASSWORD="$SENHA" \
        -v mysql_data:/var/lib/mysql \
        -v "$TPCH_DIR":/tpch:ro \
        mysql:8.0 --secure-file-priv="" >/dev/null
fi

echo "Aguardando o MySQL aceitar conexões..."
until docker exec "$CONTAINER" mysqladmin ping -uroot -p"$SENHA" --silent >/dev/null 2>&1; do
    sleep 2
done

if ! docker exec "$CONTAINER" test -f /tpch/lineitem.tbl; then
    echo "O container '$CONTAINER' não tem os .tbl em /tpch." >&2
    echo "Recrie-o com: -v \"$TPCH_DIR\":/tpch:ro" >&2
    exit 1
fi

echo "Criando tabelas..."
docker exec -i "$CONTAINER" mysql -uroot -p"$SENHA" < 01_schema.sql

echo "Carregando dados (o lineitem leva alguns minutos)..."
docker exec -i "$CONTAINER" mysql -uroot -p"$SENHA" < 02_carga.sql

echo "MySQL pronto."
