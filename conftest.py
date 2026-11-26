"""Conftest da raiz do projeto.

Existe para que o pytest, ao carregar este arquivo antes da colecao,
insira a raiz no sys.path — assim os testes podem importar
`etl.transformacoes` rodando `pytest` direto, sem `python -m pytest`.
"""
