# -*- coding: utf-8 -*-
"""Conexao com o banco de destino do ETL Verdejar (PostgreSQL).

As credenciais sao lidas exclusivamente de variaveis de ambiente.
Nenhuma senha mora no codigo nem em arquivo versionado: o arquivo
.env (gitignore) e opcional e serve so para conveniencia local.
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg2

VAR_OBRIGATORIAS = (
    "VERDEJAR_DB_HOST",
    "VERDEJAR_DB_NAME",
    "VERDEJAR_DB_USER",
    "VERDEJAR_DB_PASSWORD",
)
PORTA_PADRAO = 5432


class ErroConexao(Exception):
    """Credenciais ausentes ou banco inacessivel, com mensagem clara."""


def _carregar_env_local() -> None:
    """Preenche os defaults do .env sem sobrescrever variaveis ja definidas.

    O .env esta no .gitignore; se nao existir, nada acontece.
    """
    caminho = Path(".env")
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and chave not in os.environ:
            os.environ[chave] = valor


def get_conexao() -> psycopg2.extensions.connection:
    """Abre conexao com os parametros das variaveis de ambiente.

    Variaveis obrigatorias: VERDEJAR_DB_HOST, VERDEJAR_DB_NAME,
    VERDEJAR_DB_USER, VERDEJAR_DB_PASSWORD.
    Opcional: VERDEJAR_DB_PORT (padrao 5432).
    """
    _carregar_env_local()

    faltando = [v for v in VAR_OBRIGATORIAS if not os.environ.get(v)]
    if faltando:
        raise ErroConexao(
            "variaveis de ambiente nao definidas: " + ", ".join(faltando)
        )

    try:
        porta = int(os.environ.get("VERDEJAR_DB_PORT", str(PORTA_PADRAO)))
    except ValueError:
        raise ErroConexao(
            f"VERDEJAR_DB_PORT invalida: {os.environ['VERDEJAR_DB_PORT']!r}"
        ) from None

    try:
        conn = psycopg2.connect(
            host=os.environ["VERDEJAR_DB_HOST"],
            port=porta,
            dbname=os.environ["VERDEJAR_DB_NAME"],
            user=os.environ["VERDEJAR_DB_USER"],
            password=os.environ["VERDEJAR_DB_PASSWORD"],
            connect_timeout=5,
        )
    except (psycopg2.Error, UnicodeDecodeError) as exc:
        if isinstance(exc, UnicodeDecodeError):
            # Servidores Windows emitem mensagens em latin-1.
            detalhe = exc.object.decode("latin-1", errors="replace")
        else:
            detalhe = exc.pgerror or str(exc)
        raise ErroConexao(
            f"falha ao conectar em {os.environ['VERDEJAR_DB_HOST']}: {detalhe}"
        ) from None

    conn.autocommit = False
    return conn
