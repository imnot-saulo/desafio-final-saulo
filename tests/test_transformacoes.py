# -*- coding: utf-8 -*-
"""Testes das armadilhas A3, A4 e A5 de etl.transformacoes.

Dados mínimos escritos em cada teste; sem API, sem brutos/ e sem banco.
"""
from datetime import date
from decimal import Decimal

import pytest

from etl.transformacoes import (
    calcular_valor_itens,
    converter_data,
    converter_valor,
    padronizar_uf,
    remover_pedidos_repetidos,
    tratar_email,
)


@pytest.mark.parametrize(
    "bruto, esperada, flag",
    [
        ("2026-02-19", date(2026, 2, 19), False),
        ("19/02/2026", date(2026, 2, 19), True),
    ],
)
def test_a3_converte_data_e_acerta_flag(bruto, esperada, flag):
    pedido = {"id": 1, "data_pedido": bruto}
    novo, mudou = converter_data(pedido)
    assert novo["data_pedido"] == esperada
    assert mudou is flag


@pytest.mark.parametrize(
    "bruto",
    ["31/02/2026", "2026-13-01", "abc"],
)
def test_a3_levanta_valueerror_em_formato_invalido(bruto):
    pedido = {"id": 9, "data_pedido": bruto}
    with pytest.raises(ValueError, match=r"data_pedido invalida.*id=9"):
        converter_data(pedido)


@pytest.mark.parametrize(
    "bruto, esperado, era_texto",
    [
        ("125,84", Decimal("125.84"), True),
        ("125.84", Decimal("125.84"), True),
        (100, Decimal("100.00"), False),
    ],
)
def test_a4_converte_valor_para_decimal_com_duas_casas(bruto, esperado, era_texto):
    pedido = {"id": 2, "valor_total": bruto}
    novo, texto = converter_valor(pedido)
    assert isinstance(novo["valor_total"], Decimal)
    assert novo["valor_total"] == esperado
    assert novo["valor_total"].as_tuple().exponent == -2
    assert texto is era_texto


def test_a4_levanta_valueerror_em_valor_invalido():
    pedido = {"id": 3, "valor_total": "abc"}
    with pytest.raises(ValueError, match="valor_total invalido"):
        converter_valor(pedido)


def test_a5_mantem_a_primeira_ocorrencia_de_cada_id():
    pedidos = [
        {"id": 1, "origem": "primeira"},
        {"id": 2, "origem": "unica"},
        {"id": 1, "origem": "repetida"},
    ]
    unicos, descartados = remover_pedidos_repetidos(pedidos)
    assert [p["id"] for p in unicos] == [1, 2]
    assert unicos[0]["origem"] == "primeira"
    assert descartados == 1


@pytest.mark.parametrize(
    "ids, descartados_esperados",
    [
        ([1, 2, 3], 0),
        ([1, 2, 1], 1),
        ([1, 1, 2, 1, 3, 2], 3),
    ],
)
def test_a5_conta_descartados(ids, descartados_esperados):
    pedidos = [{"id": i} for i in ids]
    _, descartados = remover_pedidos_repetidos(pedidos)
    assert descartados == descartados_esperados


def test_a5_sem_repetidos_mantem_todos_e_nao_altera_a_lista():
    pedidos = [{"id": 1}, {"id": 2}, {"id": 3}]
    copia = [dict(p) for p in pedidos]
    unicos, descartados = remover_pedidos_repetidos(pedidos)
    assert unicos == pedidos
    assert descartados == 0
    assert pedidos == copia


@pytest.mark.parametrize(
    "email",
    [None, "", "   "],
)
def test_a1_email_nulo_permanece_nulo(email):
    registro = {"id": 1, "email": email}
    novo, flag = tratar_email(registro)
    assert novo["email"] is None
    assert flag is True


def test_a1_email_valido_nao_muda():
    registro = {"id": 2, "email": "ana@exemplo.com"}
    novo, flag = tratar_email(registro)
    assert novo["email"] == "ana@exemplo.com"
    assert flag is False


@pytest.mark.parametrize(
    "bruto, esperada, mudou",
    [
        ("rs", "RS", True),
        ("  rs  ", "RS", True),
        ("RS", "RS", False),
    ],
)
def test_a2_padroniza_uf(bruto, esperada, mudou):
    registro = {"estado": bruto}
    novo, flag = padronizar_uf(registro)
    assert novo["estado"] == esperada
    assert flag is mudou


@pytest.mark.parametrize(
    "itens, valor_total, valor_esperado, divergente_esperado",
    [
        ([{"quantidade": 2, "preco_unitario": 5}], Decimal("10.00"), Decimal("10.00"), False),
        ([{"quantidade": 2, "preco_unitario": 5}], Decimal("15.00"), Decimal("10.00"), True),
        ([{"quantidade": 2, "preco_unitario": 5}], Decimal("10.01"), Decimal("10.00"), False),
        ([{"quantidade": 1, "preco_unitario": 4.3}], Decimal("4.30"), Decimal("4.30"), False),
    ],
)
def test_a6_calcula_valor_itens_e_divergencia(
    itens, valor_total, valor_esperado, divergente_esperado
):
    pedido = {"id": 1, "valor_total": valor_total, "itens": itens}
    novo, flag = calcular_valor_itens(pedido)
    assert novo["valor_itens"] == valor_esperado
    assert novo["divergente"] is divergente_esperado
    assert flag is divergente_esperado


def test_a6_pedido_sem_itens_zera_valor_e_marca_divergente():
    pedido = {"id": 2, "valor_total": Decimal("50.00"), "itens": []}
    novo, flag = calcular_valor_itens(pedido)
    assert novo["valor_itens"] == Decimal("0.00")
    assert novo["divergente"] is True
    assert flag is True
