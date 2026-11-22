
import redis
import json
import time
from decimal import Decimal
from collections import defaultdict

# Conexão com Redis
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

r.ping()

DATA_LIMITE = 19980902
TAMANHO_LOTE = 10000

# Acumuladores por RETURNFLAG e LINESTATUS
grupos = defaultdict(lambda: {
    "sum_qty": Decimal("0"),
    "sum_base_price": Decimal("0"),
    "sum_disc_price": Decimal("0"),
    "sum_charge": Decimal("0"),
    "sum_discount": Decimal("0"),
    "count_order": 0
})

inicio = time.perf_counter()

registros_lidos = 0
registros_filtrados = 0

# Localiza as chaves da Q1
chaves = sorted(r.scan_iter(match="q1:*"))

for chave in chaves:

    # Percorre os registros em lotes, sem carregar
    # todos os dados simultaneamente na memória.
    for membro, score in r.zscan_iter(
        chave,
        count=TAMANHO_LOTE
    ):

        registros_lidos += 1

        # Aplica o filtro de data da consulta original
        if float(score) > DATA_LIMITE:
            continue

        dados = json.loads(membro)

        returnflag, linestatus = chave.split(":")[1:3]

        grupo = grupos[(returnflag, linestatus)]

        quantity = Decimal(dados["quantity"])
        extendedprice = Decimal(dados["extendedprice"])
        discount = Decimal(dados["discount"])
        tax = Decimal(dados["tax"])

        disc_price = extendedprice * (1 - discount)
        charge = disc_price * (1 + tax)

        grupo["sum_qty"] += quantity
        grupo["sum_base_price"] += extendedprice
        grupo["sum_disc_price"] += disc_price
        grupo["sum_charge"] += charge
        grupo["sum_discount"] += discount
        grupo["count_order"] += 1

        registros_filtrados += 1

fim = time.perf_counter()

# Exibe resultados ordenados
print("\n========== REDIS Q1 ==========")

for (returnflag, linestatus), grupo in sorted(grupos.items()):

    quantidade = grupo["count_order"]

    avg_qty = grupo["sum_qty"] / quantidade
    avg_price = grupo["sum_base_price"] / quantidade
    avg_disc = grupo["sum_discount"] / quantidade

    print(f"\nRETURNFLAG: {returnflag}")
    print(f"LINESTATUS: {linestatus}")
    print(f"SUM_QTY: {grupo['sum_qty']:.2f}")
    print(f"SUM_BASE_PRICE: {grupo['sum_base_price']:.2f}")
    print(f"SUM_DISC_PRICE: {grupo['sum_disc_price']:.4f}")
    print(f"SUM_CHARGE: {grupo['sum_charge']:.6f}")
    print(f"AVG_QTY: {avg_qty:.6f}")
    print(f"AVG_PRICE: {avg_price:.6f}")
    print(f"AVG_DISC: {avg_disc:.6f}")
    print(f"COUNT_ORDER: {quantidade}")

print("\n========== DESEMPENHO ==========")
print(f"Registros examinados: {registros_lidos:,}")
print(f"Registros após filtro: {registros_filtrados:,}")
print(f"Tempo de execução: {fim - inicio:.4f} segundos")
