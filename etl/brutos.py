# -*- coding: utf-8 -*-
"""Cache local em brutos/ para rodar o ETL sem chamar a API."""
from __future__ import annotations

import json
from pathlib import Path

BRUTOS_DIR = Path("brutos")


def salvar_brutos(nome: str, dados: list) -> Path:
    BRUTOS_DIR.mkdir(exist_ok=True)
    caminho = BRUTOS_DIR / f"{nome}.json"
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return caminho


def carregar_brutos(nome: str) -> list:
    caminho = BRUTOS_DIR / f"{nome}.json"
    if not caminho.is_file():
        raise FileNotFoundError(
            f"{caminho} nao existe; rode primeiro sem --brutos para gerar o cache"
        )
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)
