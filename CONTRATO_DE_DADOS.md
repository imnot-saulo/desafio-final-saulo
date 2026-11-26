# Contrato de dados — ETL Verdejar

Fontes desta especificação: `insumos/schema.sql` (PostgreSQL), `insumos/dados/produtos.csv`, `brutos/clientes.json` e `brutos/pedidos.json` (1000 clientes; 5100 pedidos brutos = 5000 únicos + 100 repetidos).

## clientes

| campo | tipo | aceita nulo? | regra de transformação |
|---|---|---|---|
| id | INTEGER | não (PK) | Copiado como está. |
| nome | TEXT | não | Copiado como está. |
| email | TEXT | sim | A1: e-mail nulo (`null`) permanece nulo e entra no contador de e-mails nulos (81 de 1000 observados). |
| cidade | TEXT | não | Copiado como está. |
| estado | CHAR(2) | não | A2: padronizar para maiúsculas (`rs` → `RS`); 151 de 1000 observados em caixa baixa. |
| cadastro_em | DATE | não | Copiado como está; amostra observada apenas no formato `AAAA-MM-DD`. |

## produtos

| campo | tipo | aceita nulo? | regra de transformação |
|---|---|---|---|
| produto_id | INTEGER | não (PK) | Ler de `produtos.csv` (`csv.DictReader`, UTF-8) e converter para inteiro. |
| nome | TEXT | não | Copiado do CSV como está. |
| categoria | TEXT | não | Copiado do CSV como está. |
| preco_base | NUMERIC(10,2) | não | Converter para número com duas casas decimais; valores do CSV chegam como texto (ex.: `3.5`). |

## pedidos

| campo | tipo | aceita nulo? | regra de transformação |
|---|---|---|---|
| id | INTEGER | não (PK) | A5: remover pedidos repetidos pelo `id`, mantendo a primeira ocorrência (100 repetidos observados em 5100 brutos). |
| cliente_id | INTEGER | não (FK → clientes.id) | Copiado como está. |
| data_pedido | DATE | não | A3: converter `DD/MM/AAAA` para `DATE` (1054 observados); formato `AAAA-MM-DD` (4046 observados) já é compatível. |
| status | TEXT | não | Copiado como está; valores observados: `entregue`, `cancelado`, `em_transporte`. |
| valor_total | NUMERIC(12,2) | não | A4: converter texto com vírgula decimal (ex.: `125,84`, 1287 observados) para número com duas casas decimais; valores já numéricos (3813 observados) passam direto. |
| valor_itens | NUMERIC(12,2) | não | A6: calcular como soma de `quantidade * preco_unitario` dos itens do pedido (coluna não existe nos brutos; é derivada). |
| divergente | BOOLEAN | não (DEFAULT FALSE) | A6: marcar `true` quando `abs(valor_total - valor_itens) > 0,01`; 241 divergentes observados nos brutos. |

O campo `itens` dos brutos não vira coluna: é desdobrado na tabela `itens_pedido`.

## itens_pedido

| campo | tipo | aceita nulo? | regra de transformação |
|---|---|---|---|
| pedido_id | INTEGER | não (FK → pedidos.id, parte do PK) | Id do pedido pai (após deduplicação A5). |
| linha | INTEGER | não (parte do PK) | Numeração sequencial dos itens dentro do pedido (1..n). |
| produto_id | INTEGER | não (FK → produtos.produto_id) | Copiado do campo `itens[].produto_id` como inteiro. |
| quantidade | INTEGER | não | Copiado do campo `itens[].quantidade` como inteiro (observado: sempre inteiro). |
| preco_unitario | NUMERIC(10,2) | não | Copiado do campo `itens[].preco_unitario` e gravado com duas casas decimais (observado: sempre número, 12718 itens no total). |

## Pontos a confirmar

- **`itens_pedido.linha`**: não existe nos brutos; a numeração sequencial a partir de 1 é inferência (o PK composto exige um valor).
- **`cadastro_em` em `DD/MM/AAAA`**: amostra observada só em `AAAA-MM-DD`; a regra A3 do desafio fala de datas de *pedido*, não de cadastro — se surgir data de cliente em outro formato, tratar igual a A3.
- **`produtos.preco_base` com mais de 2 casas**: CSV observado com 1 casa (`3.5`, `12.0`); arredondamento não foi exercitado.
- **`preco_unitario` com vírgula (A4 nos itens)**: todos os 12718 itens observados são numéricos; a regra A4 foi especificada para `valor_total`, mas vale o mesmo cuidado se aparecer texto nos itens.
- **`valor_total` divergente com string (A4 + A6 juntos)**: ambos os casos existem nos brutos, mas a interação (string com vírgula *e* divergência no mesmo pedido) não foi verificada separadamente.
- **Estilo de `estado` em caixa mista além de minúsculas** (ex.: `Rs`): amostra mostrou apenas `MAIUSCULAS` e `minusculas`; caixa mista não observada.
