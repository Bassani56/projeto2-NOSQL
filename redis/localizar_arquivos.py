import os
from pathlib import Path

PASTA_TPCH = Path(os.environ.get("TPCH_DIR", os.path.expanduser("~/Documentos/tpch-sf1")))

def localizar_arquivo(nome):
    arquivos = list(PASTA_TPCH.rglob(nome))

    if not arquivos:
        raise FileNotFoundError(f"Arquivo não encontrado: {nome}")

    return arquivos[0]

lineitem = localizar_arquivo("lineitem.tbl")

print("Arquivo encontrado:", lineitem)