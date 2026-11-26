# -*- coding: utf-8 -*-
"""Testes de reconciliar e da carga idempotente com SQLite em memoria.

Nunca toca o banco verdejar: usa insumos/schema_sqlite.sql em :memory:.
"""
from decimal import Decimal
from pathlib import Path
import sqlite3

import pytest

from etl.carga import achatar_itens, carregar, reconciliar

SCHEMA_SQLITE = Path(__file__).resolve().parents[1] / "insumos" / "schema_sqlite.sql"

# O SQLite nao sabe ligar Decimal nativamente; o psycopg2 do banco real sabe.
sqlite3.register_adapter(Decimal, str)


class _CursorComParametrosPsycopg:
    """Cursor sqlite3 com a interface que o psycopg2 oferece (with + %s)."""

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        return self._cursor.execute(sql.replace("%s", "?"), params or [])

    def executemany(self, sql, sequencia):
        return self._cursor.executemany(sql.replace("%s", "?"), sequencia)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._cursor.close()
        return False


class _ConexaoComParametrosPsycopg:
    """Conexao sqlite3 com a interface de cursor que reconciliar/carregar esperam."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _CursorComParametrosPsycopg(self._conn.cursor())

    def execute(self, sql, params=None):
        return self._conn.execute(sql.replace("%s", "?"), params or [])

    def executemany(self, sql, sequencia):
        return self._conn.executemany(sql.replace("%s", "?"), sequencia)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()


@pytest.fixture
def conn():
    conexao = sqlite3.connect(":memory:")
    conexao.executescript(SCHEMA_SQLITE.read_text(encoding="utf-8"))
    yield _ConexaoComParametrosPsycopg(conexao)
    conexao.close()


def _inserir_cliente(conn, cliente_id=1):
    conn.execute(
        "INSERT INTO clientes (id, nome, email, cidade, estado, cadastro_em) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (cliente_id, "Ana", None, "Porto Alegre", "RS", "2026-01-01"),
    )
    conn.commit()


def _inserir_pedidos(conn, linhas):
    """linhas: (id, valor_itens). Grava pedido minimo com valor_total = valor_itens."""
    conn.executemany(
        "INSERT INTO pedidos "
        "(id, cliente_id, data_pedido, status, valor_total, valor_itens, divergente) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(i, 1, "2026-01-01", "entregue", v, v, 0) for i, v in linhas],
    )
    conn.commit()


def _origem(valores):
    return [{"valor_itens": v} for v in valores]


def _contagens(conn):
    return {
        "produtos": conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
        "clientes": conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0],
        "pedidos": conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
        "itens_pedido": conn.execute("SELECT COUNT(*) FROM itens_pedido").fetchone()[0],
    }


def test_reconciliar_retorna_true_quando_origem_e_destino_batem(conn):
    _inserir_cliente(conn)
    _inserir_pedidos(conn, [(1, Decimal("10.50")), (2, Decimal("20.25"))])
    origem = _origem([Decimal("10.50"), Decimal("20.25")])
    assert reconciliar(conn, origem) is True


def test_reconciliar_retorna_false_quando_soma_difere_mais_que_0_01(conn):
    _inserir_cliente(conn)
    _inserir_pedidos(conn, [(1, Decimal("10.50")), (2, Decimal("21.25"))])
    origem = _origem([Decimal("10.50"), Decimal("20.25")])
    assert reconciliar(conn, origem) is False


def test_reconciliar_retorna_false_quando_quantidade_de_pedidos_difere(conn):
    _inserir_cliente(conn)
    _inserir_pedidos(conn, [(1, Decimal("30.75"))])
    origem = _origem([Decimal("10.50"), Decimal("20.25")])
    assert reconciliar(conn, origem) is False


def test_reconciliar_aceita_diferenca_de_exatamente_0_01_na_soma(conn):
    _inserir_cliente(conn)
    _inserir_pedidos(conn, [(1, Decimal("10.50")), (2, Decimal("20.25"))])
    origem = _origem([Decimal("10.51"), Decimal("20.25")])
    assert reconciliar(conn, origem) is True


def test_carga_duas_vezes_nao_muda_as_contagens(conn):
    produtos = [
        {"produto_id": "1", "nome": "Alface", "categoria": "folhas", "preco_base": "3.5"}
    ]
    clientes = [
        {
            "id": 1,
            "nome": "Ana",
            "email": None,
            "cidade": "Porto Alegre",
            "estado": "RS",
            "cadastro_em": "2026-01-01",
        }
    ]
    pedidos = [
        {
            "id": 1,
            "cliente_id": 1,
            "data_pedido": "2026-01-05",
            "status": "entregue",
            "valor_total": Decimal("15.90"),
            "valor_itens": Decimal("15.90"),
            "divergente": False,
            "itens": [{"produto_id": 1, "quantidade": 2, "preco_unitario": 7.95}],
        }
    ]
    itens = achatar_itens(pedidos)

    carregar(conn, produtos, clientes, pedidos, itens)
    primeira = _contagens(conn)
    carregar(conn, produtos, clientes, pedidos, itens)
    segunda = _contagens(conn)

    esperado = {"produtos": 1, "clientes": 1, "pedidos": 1, "itens_pedido": 1}
    assert primeira == esperado
    assert segunda == esperado
