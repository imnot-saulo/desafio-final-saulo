# -*- coding: utf-8 -*-
"""Extração paginada da API local Verdejar (a11y: sem dependência de Flask)."""
from __future__ import annotations

import csv

import requests

TIMEOUT_SEGUNDOS = 5


class ErroExtracao(Exception):
    """Erro de extração com mensagem clara para o operador."""


def extrair_paginado(base_url: str, rota: str, page_size: int) -> tuple[list[dict], int]:
    """Percorre /{rota}?page=N&page_size=S até total_pages.

    Retorna (registros, paginas_lidas).
    """
    if page_size < 1 or page_size > 200:
        raise ErroExtracao(f"page_size invalido: {page_size} (a API aceita 1..200)")

    url = f"{base_url.rstrip('/')}/{rota.lstrip('/')}"
    registros: list[dict] = []
    pagina = 1
    total_paginas: int | None = None
    paginas_lidas = 0

    while total_paginas is None or pagina <= total_paginas:
        try:
            resp = requests.get(
                url,
                params={"page": pagina, "page_size": page_size},
                timeout=TIMEOUT_SEGUNDOS,
            )
        except requests.exceptions.Timeout:
            raise ErroExtracao(
                f"timeout apos {TIMEOUT_SEGUNDOS}s em {url}?page={pagina}"
            ) from None
        except requests.exceptions.ConnectionError:
            raise ErroExtracao(
                f"falha de conexao em {url} (a API esta rodando?)"
            ) from None

        if resp.status_code == 404:
            raise ErroExtracao(
                f"pagina {pagina} inexistente em {url} "
                f"(total_pages informado: {total_paginas})"
            )
        if resp.status_code != 200:
            raise ErroExtracao(f"HTTP {resp.status_code} em {url}?page={pagina}")

        try:
            corpo = resp.json()
        except ValueError:
            raise ErroExtracao(
                f"JSON invalido em {url}?page={pagina}"
            ) from None

        total_paginas = int(corpo["total_pages"])
        itens = corpo["items"]
        if not isinstance(itens, list):
            raise ErroExtracao(f"campo 'items' invalido em {url}?page={pagina}")

        registros.extend(itens)
        paginas_lidas += 1
        pagina += 1

    return registros, paginas_lidas


def extrair_clientes(base_url: str, page_size: int = 200) -> list[dict]:
    registros, _ = extrair_paginado(base_url, "clientes", page_size)
    return registros


def extrair_pedidos(base_url: str, page_size: int = 200) -> list[dict]:
    registros, _ = extrair_paginado(base_url, "pedidos", page_size)
    return registros


def ler_produtos_csv(caminho: str) -> list[dict]:
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
