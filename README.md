# desafio-final-saulo

## Carga idempotente

A carga roda em uma única transação: primeiro `DELETE` nas quatro tabelas na ordem inversa das chaves estrangeiras (`itens_pedido`, `pedidos`, `clientes`, `produtos`) e depois `INSERT` na ordem das dependências (`produtos`, `clientes`, `pedidos`, `itens_pedido`). Como tudo acontece na mesma transação, um erro no meio desfaz tudo (rollback) e o banco nunca fica pela metade. Rodar o ETL duas vezes, portanto, deixa o destino com exatamente os mesmos registros — as contagens por tabela não mudam. A estratégia foi escolhida em vez de `ON CONFLICT DO NOTHING` porque o destino espelha a origem: linhas obsoletas de uma carga anterior quebrariam a reconciliação de contagens.

Para provar a idempotência, rode o ETL duas vezes e compare os contadores impressos ao fim de cada execução (função `contar_registros` em `etl/carga.py`):

```powershell
python etl/main.py --brutos
python etl/main.py --brutos
```
