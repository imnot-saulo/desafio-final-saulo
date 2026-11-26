# -*- coding: utf-8 -*-
"""Orquestração do ETL Verdejar: extração, transform, carga e reconciliação."""
from __future__ import annotations

import sys

from banco import get_conexao
from brutos import carregar_brutos, salvar_brutos
from carga import (
    achatar_itens,
    carregar,
    contar_registros,
    imprimir_contagens,
    reconciliar,
)
from extracao import extrair_clientes, extrair_pedidos, ler_produtos_csv
from transformacoes import aplicar_transformacoes, imprimir_contadores

BASE_URL = "http://127.0.0.1:8000"
PRODUTOS_CSV = "insumos/dados/produtos.csv"


def imprimir_resumo(
    paginas_clientes: int,
    registros_clientes: int,
    paginas_pedidos: int,
    registros_pedidos: int,
    registros_produtos: int,
) -> None:
    print(f"paginas_clientes: {paginas_clientes}")
    print(f"registros_clientes: {registros_clientes}")
    print(f"paginas_pedidos: {paginas_pedidos}")
    print(f"registros_pedidos: {registros_pedidos}")
    print(f"registros_produtos: {registros_produtos}")


def extrair_ou_reaproveitar(reaproveitar: bool) -> tuple[list[dict], list[dict]]:
    if reaproveitar:
        return carregar_brutos("clientes"), carregar_brutos("pedidos")
    clientes = extrair_clientes(BASE_URL)
    pedidos = extrair_pedidos(BASE_URL)
    salvar_brutos("clientes", clientes)
    salvar_brutos("pedidos", pedidos)
    return clientes, pedidos


def main(reaproveitar: bool = False) -> None:
    clientes, pedidos = extrair_ou_reaproveitar(reaproveitar)
    produtos = ler_produtos_csv(PRODUTOS_CSV)

    clientes_ok, pedidos_ok, contadores = aplicar_transformacoes(clientes, pedidos)
    imprimir_contadores(contadores)

    itens = achatar_itens(pedidos_ok)

    conn = get_conexao()
    try:
        carregar(conn, produtos, clientes_ok, pedidos_ok, itens)
        imprimir_contagens(contar_registros(conn))
        reconciliou = reconciliar(conn, pedidos_ok)
    finally:
        conn.close()

    if not reconciliou:
        sys.exit(1)


if __name__ == "__main__":
    main(reaproveitar="--brutos" in sys.argv)
