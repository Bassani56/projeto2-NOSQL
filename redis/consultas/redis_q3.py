
import redis
import json
import time

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

r.ping()

inicio = time.perf_counter()

resultados = []
registros_lidos = 0

# Localiza as partições da Q3
chaves = sorted(r.scan_iter(match="q3:BUILDING:*"))

# Recupera os pedidos armazenados
for chave in chaves:

    for membro, score in r.zscan_iter(chave, count=1000):

        dados = json.loads(membro)

        resultados.append(dados)
        registros_lidos += 1

# Ordena por receita decrescente e data crescente
resultados.sort(
    key=lambda x: (
        -float(x["revenue"]),
        x["orderdate"]
    )
)

# Retorna os 10 primeiros
resultados = resultados[:10]

fim = time.perf_counter()

print("\n========== REDIS Q3 ==========")

for i, pedido in enumerate(resultados, start=1):

    print(f"\nResultado {i}")
    print(f"L_ORDERKEY: {pedido['orderkey']}")
    print(f"REVENUE: {pedido['revenue']:.4f}")
    print(f"O_ORDERDATE: {pedido['orderdate']}")
    print(f"O_SHIPPRIORITY: {pedido['shippriority']}")

print("\n========== DESEMPENHO ==========")
print(f"Chaves consultadas: {len(chaves)}")
print(f"Registros lidos: {registros_lidos:,}")
print(f"Resultados retornados: {len(resultados)}")
print(f"Tempo de execução: {fim - inicio:.4f} segundos")
