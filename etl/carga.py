# -*- coding: utf-8 -*-
"""Carga idempotente, contagem e reconciliação do ETL Verdejar (PostgreSQL).

Ordem de inserção obedece às chaves estrangeiras:
produtos e clientes (pais) -> pedidos -> itens_pedido.
A limpeza prévia usa a ordem inversa. Tudo em uma única transação.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import psycopg2
from psycopg2 import sql

TABELAS = ("produtos", "clientes", "pedidos", "itens_pedido")
CENTAVOS = Decimal("0.01")


def achatar_itens(pedidos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Desdobra pedidos[].itens em linhas de itens_pedido (linha 1..n)."""
    linhas: list[dict[str, Any]] = []
    for pedido in pedidos:
        for numero, item in enumerate(pedido["itens"], start=1):
            linhas.append(
                {
                    "pedido_id": pedido["id"],
                    "linha": numero,
                    "produto_id": item["produto_id"],
                    "quantidade": item["quantidade"],
                    "preco_unitario": Decimal(str(item["preco_unitario"])).quantize(
                        CENTAVOS
                    ),
                }
            )
    return linhas


def _linhas_produtos(produtos: list[dict[str, Any]]) -> list[tuple]:
    return [
        (
            int(p["produto_id"]),
            p["nome"],
            p["categoria"],
            Decimal(str(p["preco_base"])).quantize(CENTAVOS),
        )
        for p in produtos
    ]


def _linhas_clientes(clientes: list[dict[str, Any]]) -> list[tuple]:
    return [
        (c["id"], c["nome"], c["email"], c["cidade"], c["estado"], c["cadastro_em"])
        for c in clientes
    ]


def _linhas_pedidos(pedidos: list[dict[str, Any]]) -> list[tuple]:
    return [
        (
            p["id"],
            p["cliente_id"],
            p["data_pedido"],
            p["status"],
            p["valor_total"],
            p["valor_itens"],
            p["divergente"],
        )
        for p in pedidos
    ]


def _linhas_itens(itens: list[dict[str, Any]]) -> list[tuple]:
    return [
        (i["pedido_id"], i["linha"], i["produto_id"], i["quantidade"], i["preco_unitario"])
        for i in itens
    ]


def carregar(
    conn: psycopg2.extensions.connection,
    produtos: list[dict[str, Any]],
    clientes: list[dict[str, Any]],
    pedidos: list[dict[str, Any]],
    itens: list[dict[str, Any]],
) -> dict[str, int]:
    """Insere produtos, clientes, pedidos e itens_pedido em uma transação.

    Limpeza prévia (idempotência) na ordem inversa das FKs; inserção na
    ordem das FKs. Commit no sucesso, rollback em qualquer erro.
    """
    contagens = {
        "produtos": len(produtos),
        "clientes": len(clientes),
        "pedidos": len(pedidos),
        "itens_pedido": len(itens),
    }
    try:
        with conn.cursor() as cur:
            # Ordem inversa das FKs: filhos antes dos pais.
            cur.execute("DELETE FROM itens_pedido")
            cur.execute("DELETE FROM pedidos")
            cur.execute("DELETE FROM clientes")
            cur.execute("DELETE FROM produtos")

            cur.executemany(
                "INSERT INTO produtos (produto_id, nome, categoria, preco_base) "
                "VALUES (%s, %s, %s, %s)",
                _linhas_produtos(produtos),
            )
            cur.executemany(
                "INSERT INTO clientes (id, nome, email, cidade, estado, cadastro_em) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                _linhas_clientes(clientes),
            )
            cur.executemany(
                "INSERT INTO pedidos "
                "(id, cliente_id, data_pedido, status, valor_total, valor_itens, divergente) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                _linhas_pedidos(pedidos),
            )
            cur.executemany(
                "INSERT INTO itens_pedido "
                "(pedido_id, linha, produto_id, quantidade, preco_unitario) "
                "VALUES (%s, %s, %s, %s, %s)",
                _linhas_itens(itens),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return contagens


def contar_registros(conn: psycopg2.extensions.connection) -> dict[str, int]:
    """Conta linhas de cada tabela de destino (uma consulta por tabela)."""
    contagens: dict[str, int] = {}
    with conn.cursor() as cur:
        for tabela in TABELAS:
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(tabela))
            )
            contagens[tabela] = cur.fetchone()[0]
    return contagens


def imprimir_contagens(contagens: dict[str, int]) -> None:
    """Saida texto simples: uma tabela por linha, na ordem das FKs."""
    for tabela in TABELAS:
        print(f"{tabela}: {contagens[tabela]}")


def reconciliar(
    conn: psycopg2.extensions.connection,
    pedidos_transformados: list[dict[str, Any]],
) -> bool:
    """Compara origem (transformados) e destino (banco).

    (a) quantidade de pedidos unicos: origem vs COUNT;
    (b) soma de valor_itens: origem vs SUM, tolerancia de 0.01.
    Imprime uma linha por verificacao e devolve True so se ambas passam.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pedidos")
        destino_qtd = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(valor_itens), 0) FROM pedidos")
        destino_soma = cur.fetchone()[0]

    origem_qtd = len(pedidos_transformados)
    origem_soma = sum(
        (p["valor_itens"] for p in pedidos_transformados), start=Decimal("0.00")
    )

    ok_qtd = origem_qtd == destino_qtd
    ok_soma = abs(origem_soma - destino_soma) <= Decimal("0.01")

    rotulo_qtd = "qtd_pedidos"
    if ok_qtd:
        print(f"verificacao {rotulo_qtd}: OK")
    else:
        print(
            f"verificacao {rotulo_qtd}: FALHA "
            f"(origem={origem_qtd}, destino={destino_qtd})"
        )

    rotulo_soma = "soma_valor_itens"
    if ok_soma:
        print(f"verificacao {rotulo_soma}: OK")
    else:
        print(
            f"verificacao {rotulo_soma}: FALHA "
            f"(origem={origem_soma:.2f}, destino={destino_soma:.2f})"
        )

    return ok_qtd and ok_soma


__all__ = [
    "achatar_itens",
    "carregar",
    "contar_registros",
    "imprimir_contagens",
    "reconciliar",
]
