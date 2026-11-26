# desafio-final-saulo

ETL Verdejar: extração paginada da API local, transformação das armadilhas A1–A6, carga idempotente em PostgreSQL com reconciliação e consultas de validação.

## Banco de destino e biblioteca de conexão

- **Banco:** PostgreSQL — `insumos/schema.sql` é o schema de registro. O `insumos/schema_sqlite.sql` existe só como contingência e é o que os testes usam em memória.
- **Biblioteca:** `psycopg2-binary` (`pip install psycopg2-binary`).
- **Conexão:** `etl/banco.py::get_conexao()` lê exclusivamente as variáveis de ambiente `VERDEJAR_DB_HOST`, `VERDEJAR_DB_PORT` (opcional, padrão 5432), `VERDEJAR_DB_NAME`, `VERDEJAR_DB_USER` e `VERDEJAR_DB_PASSWORD`. Nenhuma senha no código: use as variáveis da sessão ou um arquivo `.env` na raiz (já está no `.gitignore`).

## Como rodar

### 1. API (fonte dos dados)

```powershell
python insumos/api_verdejar.py --dados insumos/dados
# API em http://127.0.0.1:8000 — deixe aberta em outro terminal
```

### 2. Banco (uma vez só)

```powershell
psql -U postgres -c "CREATE DATABASE verdejar;"
psql -U postgres -d verdejar -f insumos/schema.sql

# credenciais da sessão (não são versionadas)
$env:VERDEJAR_DB_HOST = "127.0.0.1"
$env:VERDEJAR_DB_PORT = "5432"
$env:VERDEJAR_DB_NAME = "verdejar"
$env:VERDEJAR_DB_USER = "postgres"
$env:VERDEJAR_DB_PASSWORD = "<sua senha>"
```

### 3. ETL

```powershell
python etl/main.py            # extrai da API e grava o cache em brutos/
python etl/main.py --brutos   # reaproveita o cache, sem API
```

No fim imprime os contadores A1–A6, as linhas por tabela e as verificações de reconciliação (`verificacao ...: OK`). Saída em texto simples, uma informação por linha.

### 4. Testes

```powershell
python -m pytest -v   # lista cada teste
python -m pytest -q   # só o resumo
```

32 testes, sem API, sem `brutos/` e sem banco real: a reconciliação roda em SQLite em memória com `insumos/schema_sqlite.sql`.

```
32 passed in 0.04s
```

## Estratégia de idempotência

A carga roda em uma única transação: primeiro `DELETE` nas quatro tabelas na ordem inversa das chaves estrangeiras (`itens_pedido`, `pedidos`, `clientes`, `produtos`) e depois `INSERT` na ordem das dependências (`produtos`, `clientes`, `pedidos`, `itens_pedido`). Como tudo acontece na mesma transação, um erro no meio desfaz tudo (rollback) e o banco nunca fica pela metade. Rodar o ETL duas vezes, portanto, deixa o destino com exatamente os mesmos registros — as contagens por tabela não mudam. A estratégia foi escolhida em vez de `ON CONFLICT DO NOTHING` porque o destino espelha a origem: linhas obsoletas de uma carga anterior quebrariam a reconciliação de contagens.

Para provar a idempotência, rode o ETL duas vezes e compare os contadores impressos ao fim de cada execução (função `contar_registros` em `etl/carga.py`):

```powershell
python etl/main.py --brutos
python etl/main.py --brutos
```

## Validação em SQL

```powershell
psql -U postgres -d verdejar -f consultas_validacao.sql
```

Resultados da execução com os dados completos do projeto (5000 pedidos únicos):

**(a) Total de vendas por mês** — e a conferência de que a soma dos totais mensais bate com o total geral:

| mes | qtd_pedidos | total_vendas |
|---|---:|---:|
| 2026-01 | 488 | 30449.02 |
| 2026-02 | 536 | 33923.86 |
| 2026-03 | 487 | 30678.70 |
| 2026-04 | 521 | 31253.96 |
| 2026-05 | 512 | 30890.02 |
| 2026-06 | 523 | 31627.73 |
| 2026-07 | 519 | 32796.17 |
| 2026-08 | 458 | 29328.04 |
| 2026-09 | 476 | 29995.71 |
| 2026-10 | 480 | 31104.54 |
| **total** | **5000** | **312047.75** |

Conferência: `total_geral = 312047.75`, `soma_mensal = 312047.75` → **OK**.

**(b) Quantidade de pedidos por estado:**

| estado | qtd_pedidos |
|---|---:|
| RS | 1543 |
| SC | 1127 |
| PR | 974 |
| SP | 880 |
| MG | 476 |

**(c) Pedidos divergentes:** **238** pedidos com `valor_total` ≠ `valor_itens` (diferenças de +10,00, −5,00 e +3,00) — bate com o contador A6 impresso pelo ETL.
