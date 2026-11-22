
import redis
import json
import time
from decimal import Decimal

# Conexão com Redis
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

r.ping()

inicio = time.perf_counter()

# Armazena o menor custo encontrado para cada peça
menores_custos = {}

# Armazena os fornecedores que possuem o menor custo
melhores_fornecedores = {}

registros_lidos = 0

# Localiza as 30 chaves da Q2
chaves = sorted(r.scan_iter(match="q2:15:*:EUROPE"))

for chave in chaves:

    registros = r.zscan_iter(chave, count=1000)

    for membro, score in registros:

        dados = json.loads(membro)
        registros_lidos += 1

        partkey = dados["p_partkey"]
        custo = Decimal(dados["ps_supplycost"])

        if partkey not in menores_custos:

            menores_custos[partkey] = custo
            melhores_fornecedores[partkey] = [dados]

        elif custo < menores_custos[partkey]:

            menores_custos[partkey] = custo
            melhores_fornecedores[partkey] = [dados]

        elif custo == menores_custos[partkey]:

            melhores_fornecedores[partkey].append(dados)

# Reúne os fornecedores vencedores
resultados = []

for fornecedores in melhores_fornecedores.values():
    resultados.extend(fornecedores)

# Ordenação da consulta TPC-H Q2
resultados.sort(
    key=lambda x: (
        -Decimal(x["s_acctbal"]),
        x["n_name"],
        x["s_name"],
        x["p_partkey"]
    )
)

# Retorna os 100 primeiros
resultados = resultados[:100]

fim = time.perf_counter()

# Exibição
print("\n========== REDIS Q2 ==========")

for i, dados in enumerate(resultados, start=1):

    print(f"\nResultado {i}")
    print(f"S_ACCTBAL: {dados['s_acctbal']}")
    print(f"S_NAME: {dados['s_name']}")
    print(f"N_NAME: {dados['n_name']}")
    print(f"P_PARTKEY: {dados['p_partkey']}")
    print(f"P_MFGR: {dados['p_mfgr']}")
    print(f"S_ADDRESS: {dados['s_address']}")
    print(f"S_PHONE: {dados['s_phone']}")
    print(f"S_COMMENT: {dados['s_comment']}")

print("\n========== DESEMPENHO ==========")
print(f"Chaves consultadas: {len(chaves)}")
print(f"Registros lidos: {registros_lidos}")
print(f"Peças avaliadas: {len(menores_custos)}")
print(f"Resultados retornados: {len(resultados)}")
print(f"Tempo de execução: {fim - inicio:.4f} segundos")
