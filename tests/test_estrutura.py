# -*- coding: utf-8 -*-
"""Garante que o pytest encontra os testes e que etl.transformacoes importa da raiz."""
from etl.transformacoes import converter_data


def test_importa_transformacoes_da_raiz():
    assert callable(converter_data)
