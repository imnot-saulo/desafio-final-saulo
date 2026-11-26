# -*- coding: utf-8 -*-
"""Transformacoes puras A1-A6 do ETL Verdejar (PostgreSQL).

Cada funcao de registro recebe dict e devolve (registro_novo, flag):
flag=True significa "houve algo a contar" (nulo, mudanca ou formato do trap).
O registro original nunca e mutado. Monetarios sempre Decimal.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


def tratar_email(registro: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """A1: e-mail nulo permanece nulo; flag indica nulo para o contador."""
    email = registro.get("email")
    eh_nulo = email is None or (isinstance(email, str) and email.strip() == "")
    novo = dict(registro)
    if eh_nulo:
        novo["email"] = None
    return novo, eh_nulo


def padronizar_uf(registro: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """A2: UF em maiusculas e sem espacos; flag indica houve mudanca."""
    uf_original = registro["estado"]
    uf_nova = uf_original.strip().upper()
    novo = dict(registro)
    novo["estado"] = uf_nova
    return novo, uf_nova != uf_original


def converter_data(pedido: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """A3: AAAA-MM-DD ou DD/MM/AAAA -> date; flag indica DD/MM/AAAA (trap).

    Formato invalido: ValueError claro (schema NOT NULL impede nulo).
    """
    bruto = pedido["data_pedido"]
    try:
        if "/" in bruto:
            data = date.fromisoformat(
                f"{bruto[6:10]}-{bruto[3:5]}-{bruto[0:2]}"
            )
            mudou = True
        else:
            data = date.fromisoformat(bruto)
            mudou = False
    except ValueError as exc:
        raise ValueError(
            f"data_pedido invalida: {bruto!r} (pedido id={pedido['id']})"
        ) from None
    novo = dict(pedido)
    novo["data_pedido"] = data
    return novo, mudou


def converter_valor(pedido: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """A4: numero ou texto com virgula -> Decimal(2); flag indica texto (trap).

    Valor invalido: ValueError claro (schema NOT NULL impede nulo).
    """
    bruto = pedido["valor_total"]
    texto = isinstance(bruto, str)
    try:
        valor = Decimal(bruto.replace(",", ".") if texto else str(bruto))
        valor = valor.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ValueError(
            f"valor_total invalido: {bruto!r} (pedido id={pedido['id']})"
        ) from None
    novo = dict(pedido)
    novo["valor_total"] = valor
    return novo, texto


def remover_pedidos_repetidos(
    pedidos: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """A5: mantem a primeira ocorrência de cada id; devolve (lista, descartados)."""
    vistos: set[Any] = set()
    unicos: list[dict[str, Any]] = []
    descartados = 0
    for pedido in pedidos:
        if pedido["id"] in vistos:
            descartados += 1
            continue
        vistos.add(pedido["id"])
        unicos.append(pedido)
    return unicos, descartados


def calcular_valor_itens(pedido: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """A6: valor_itens = soma(qtd * preco); divergente = |diff| > 0.01.

    Pedido sem itens: valor_itens = 0.00 e divergente=True (anomalia sinalizada);
    no dados reais nao existe tal caso.
    """
    soma = Decimal("0.00")
    for item in pedido["itens"]:
        qtd = Decimal(item["quantidade"])
        preco = Decimal(str(item["preco_unitario"]))
        soma += qtd * preco
    soma = soma.quantize(Decimal("0.01"))
    divergente = abs(soma - pedido["valor_total"]) > Decimal("0.01")
    novo = dict(pedido)
    novo["valor_itens"] = soma
    novo["divergente"] = divergente
    return novo, divergente


def aplicar_transformacoes(
    clientes: list[dict[str, Any]],
    pedidos: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Aplica A1-A6 na ordem; devolve (clientes, pedidos, contadores).

    Ordem nos pedidos: dedupe (A5) antes de contar; data/valor (A3/A4)
    antes de calcular a divergencia (A6).
    """
    contadores = {
        "pedidos_unicos": 0,
        "repetidos_descartados": 0,
        "emails_nulos": 0,
        "estados_padronizados": 0,
        "datas_convertidas": 0,
        "valores_convertidos": 0,
        "divergentes": 0,
    }

    clientes_ok = []
    for registro in clientes:
        registro, flag_email = tratar_email(registro)
        registro, flag_uf = padronizar_uf(registro)
        contadores["emails_nulos"] += flag_email
        contadores["estados_padronizados"] += flag_uf
        clientes_ok.append(registro)

    pedidos_unicos, descartados = remover_pedidos_repetidos(pedidos)
    contadores["repetidos_descartados"] = descartados
    contadores["pedidos_unicos"] = len(pedidos_unicos)

    pedidos_ok = []
    for pedido in pedidos_unicos:
        pedido, flag_data = converter_data(pedido)
        pedido, flag_valor = converter_valor(pedido)
        pedido, flag_divergente = calcular_valor_itens(pedido)
        contadores["datas_convertidas"] += flag_data
        contadores["valores_convertidos"] += flag_valor
        contadores["divergentes"] += flag_divergente
        pedidos_ok.append(pedido)

    return clientes_ok, pedidos_ok, contadores


def imprimir_contadores(contadores: dict[str, int]) -> None:
    """Saida texto simples: uma informacao por linha, na ordem pedida."""
    ordem = [
        "pedidos_unicos",
        "repetidos_descartados",
        "emails_nulos",
        "estados_padronizados",
        "datas_convertidas",
        "valores_convertidos",
        "divergentes",
    ]
    for chave in ordem:
        print(f"{chave}: {contadores[chave]}")
