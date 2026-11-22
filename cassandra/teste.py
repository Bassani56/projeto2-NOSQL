from collections import Counter

arquivo = r"C:\Users\User\Desktop\TPC-H\7C3325E0-B869-4712-A2FF-D89F23465D20-TPC-H-Tool\TPC-H V3.0.1\dbgen\part.tbl"

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