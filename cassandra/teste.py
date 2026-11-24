import os
from collections import Counter

arquivo = os.path.join(os.environ.get("TPCH_DIR", os.path.expanduser("~/Documentos/tpch-sf1")), "part.tbl")

tipos = Counter()

with open(arquivo, "r", encoding="utf-8") as f:
    for linha in f:
        dados = linha.strip().split("|")

        tamanho = int(dados[5])
        tipo = dados[4]

        if tamanho == 15 and tipo.endswith("BRASS"):
            tipos[tipo] += 1

for tipo, quantidade in tipos.items():
    print(tipo, quantidade)