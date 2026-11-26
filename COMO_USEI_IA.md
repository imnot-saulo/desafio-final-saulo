# Como usei IA

## Sugestões aceitas

### Esqueleto da parte de como usei IA

- **Trecho pedido:** "Gere o COMO_USEI_IA.md com três seções vazias e um modelo de entrada com os campos: trecho pedido, resposta da IA (resumo), decisão, justificativa e como validei."
- **Resposta da IA (resumo):** Arquivo com as três seções e um template de entrada já formatado em Markdown.
- **Decisão:** Aceitei o esqueleto como base e mantenho o formato em todas as entradas.
- **Justificativa:** Segura a estrutura pedida pela avaliação e agiliza o registro de cada uso de IA.
- **Como validei:** Conferi o Markdown renderizado e o preenchimento desta primeira entrada.

### Padrão tupla (registro, flag) para contadores

- **Trecho pedido:** Contadores A1–A6 sem estado global, cada função precisando permitir saber se tratou/mudou.
- **Resposta da IA (resumo):** Propôs devolver sempre `(registro_novo, flag)` e somar as flags no orquestrador.
- **Decisão:** Aceitei e apliquei em todas as funções de registro.
- **Justificativa:** Funções continuam puras e testáveis isoladamente; sem globais.
- **Como validei:** `main --brutos` imprimiu as 7 contagens conferidas contra os brutos (81, 151, 1037, 1255, 238).

### Erro claro em formato inválido em vez de nulo

- **Trecho pedido:** Definir comportamento para `data_pedido`/`valor_total` inválidos.
- **Resposta da IA (resumo):** Sugestão de `ValueError` com valor e `id` do pedido, em vez de nulo silencioso.
- **Decisão:** Aceitei.
- **Justificativa:** Schema é `NOT NULL`; nulo só adiaria a falha para o load com mensagem pior.
- **Como validei:** Dados reais passaram sem exceção; caso inválido não existe na amostra (defesa validada por leitura do código).

### Estratégia de idempotência: DELETE + reload na mesma transação

- **Trecho pedido:** "Compare duas estratégias de idempotência (limpar tabelas antes de carregar vs ON CONFLICT) e escolha uma com base no meu schema; implemente no carregar."
- **Resposta da IA (resumo):** Comparou as duas e escolheu `DELETE` na ordem inversa das FKs + `INSERT` na ordem das FKs, tudo numa única transação com rollback em qualquer erro.
- **Decisão:** Aceitei a escolha da IA.
- **Justificativa:** O destino precisa espelhar a origem para a reconciliação passar; `ON CONFLICT DO NOTHING` manteria linhas obsoletas se a origem encolhesse. Todas as tabelas têm PK, mas as FKs exigem ordem na limpeza — a transação única garante que um erro no meio desfaça tudo.
- **Como validei:** Rodei o ETL duas vezes e as contagens (12/1000/5000/12455) não mudaram; injeti `cliente_id` inválido e o rollback preservou os dados (`ForeignKeyViolation`).

### reconciliar() devolvendo bool com rótulo por verificação

- **Trecho pedido:** "Imprima uma linha por verificação, no formato 'verificacao: OK' ou 'verificacao: FALHA (origem=..., destino=...)' e retorne um booleano para eu poder testar com pytest depois."
- **Resposta da IA (resumo):** Compara `COUNT` e `SUM(valor_itens)` com tolerância de 0.01, imprime uma linha por verificação e devolve o `and` das duas; acrescentou o nome da verificação na linha para não perder qual falhou.
- **Decisão:** Aceitei, inclusive o rótulo extra (`qtd_pedidos`, `soma_valor_itens`) que foge levemente ao formato pedido.
- **Justificativa:** Sem o rótulo, duas linhas `verificacao: FALHA` seriam indistinguíveis; o formato original foi mantido.
- **Como validei:** Com lista adulterada (4999 pedidos) imprimiu `FALHA` e retornou `False`; com os dados corretos, `OK` e `True`.

### Suíte pytest para as partes da ETL

- **Trecho pedido:** "Adicione testes automatizados para as partes da ETL" (pytest, sem depender de API, brutos ou banco real).
- **Resposta da IA (resumo):** Criou `conftest.py` na raiz para o `import etl` funcionar sem instalar o pacote, e três arquivos de teste: `test_estrutura.py` (contratos JSON/CSV), `test_transformacoes.py` (A1–A6 isolados por função) e `test_reconciliacao.py` (reconciliação em SQLite em memória com `schema_sqlite.sql`).
- **Decisão:** Aceitei a estrutura; mantive o adaptador de conexão só no arquivo de teste e rejeitei teste dependente de API/banco real ou mock pesado de psycopg2.
- **Justificativa:** Os testes rodam em qualquer máquina com `pip install pytest`; a reconciliação exercita o mesmo código de produção sem exigir PostgreSQL na suíte.
- **Como validei:** `python -m pytest -q` → `32 passed`; os contadores A1–A6 testados batem com os valores reais (81, 151, 1037, 1255, 238).

### README de entrega final com resultados das consultas

- **Trecho pedido:** "Como ficará o README para entrega final: como rodar (API, banco, ETL, testes), caminho do banco escolhido e biblioteca de conexão, estratégia de idempotência" e "registrar os resultados das três consultas de validação".
- **Resposta da IA (resumo):** Reescreveu o README com as seções de banco (PostgreSQL + `psycopg2-binary` + variáveis de ambiente), os 4 passos de como rodar, a estratégia de idempotência e a seção de validação em SQL com os resultados reais (tabela mensal com conferência `312047.75 = 312047.75 → OK`, estados RS 1543 / SC 1127 / PR 974 / SP 880 / MG 476 e 238 divergentes).
- **Decisão:** Aceitei a estrutura e conferi cada número antes de gravar; os mesmos resultados foram comentados no `consultas_validacao.sql`.
- **Justificativa:** O README passa a responder sozinho o que a avaliação cobra (rodar, banco, idempotência, validação) sem precisar de outro arquivo.
- **Como validei:** Números batidos contra a execução real do ETL na Etapa 4 (5000 pedidos) e contra o contador A6 impresso; `32 passed` confirmado antes do commit `f6f1bff`.

## Sugestões rejeitadas

### Adaptar o código para SQLite usando o schema_sqlite.sql

- **Trecho pedido:** "schema.sql ou schema_sqlite.sql: use o que existir para descobrir se o banco é PostgreSQL ou SQLite e adapte o código e o SQL a ele."
- **Resposta da IA (resumo):** Como os dois schemas existiam, avaliou suportar os dois drivers com uma variável `VERDEJAR_DB_DRIVER` e SQL duplicado (`strftime` para SQLite).
- **Decisão:** Rejeitei; fiquei só no PostgreSQL.
- **Justificativa:** `schema.sql` é o schema de registro (citado no contrato, `transformacoes.py` documenta PostgreSQL) e o `psycopg2-binary` já estava instalado; manter dois dialetos dobraria o teste sem necessidade. O SQLite fica como contingência documentada.
- **Como validei:** O ETL rodou de ponta a ponta no PostgreSQL e as 4 consultas de validação (`DATE_TRUNC`) passaram.

## Falhas e retrabalho

### Erro de sintaxe no comando de teste da API

- **Trecho pedido:** Validar `salvar_brutos`/`carregar_brutos` contra a API
- **Resposta da IA (resumo):** Gerou um comando `python -c` com a variável `de volta` (espaço no nome)
- **Decisão:** Primeira execução falhou com `SyntaxError`; a IA corrigiu para `volta` e o teste passou
- **Justificativa:** Erro de digitação no heredoc PowerShell, detectado na hora pelo retorno do Python
- **Como validei:** Segunda execução imprimiu `recarregados: 1000 == 1000`

### Linha destrutiva no script de teste da reconciliação

- **Trecho pedido:** "Teste os caminhos de erro: variáveis ausentes, rollback e FALHA da reconciliação."
- **Resposta da IA (resumo):** O primeiro rascunho do script chamava `carregar(conn, [], [], [], [])` "para testar", o que executaria o `DELETE` das quatro tabelas e confirmaria o apagão.
- **Decisão:** Reescrevi o script antes de executar; o teste passou a usar um pedido com `cliente_id` inválido para forçar o erro.
- **Justificativa:** Listas vazias ainda passam pela limpeza — o DELETE rodaria e o commit confirmaria a perda dos dados.
- **Como validei:** O script final falhou por `ForeignKeyViolation`, fez rollback e as contagens ficaram iguais às de antes.
