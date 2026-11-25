# -*- coding: utf-8 -*-
"""Orquestração do ETL Verdejar: extração, transform e carga."""


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
