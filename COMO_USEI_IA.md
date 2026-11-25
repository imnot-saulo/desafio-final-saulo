# Como usei IA

## Sugestões aceitas

### Esqueleto da parte de como usei IA

- **Trecho pedido:** "Gere o COMO_USEI_IA.md com três seções vazias e um modelo de entrada com os campos: trecho pedido, resposta da IA (resumo), decisão, justificativa e como validei."
- **Resposta da IA (resumo):** Arquivo com as três seções e um template de entrada já formatado em Markdown.
- **Decisão:** Aceitei o esqueleto como base e mantenho o formato em todas as entradas.
- **Justificativa:** Segura a estrutura pedida pela avaliação e agiliza o registro de cada uso de IA.
- **Como validei:** Conferi o Markdown renderizado e o preenchimento desta primeira entrada.

## Sugestões rejeitadas

### [Título curto da entrada]

- **Trecho pedido:** 
- **Resposta da IA (resumo):** 
- **Decisão:** 
- **Justificativa:** 
- **Como validei:** 

## Falhas e retrabalho

### Erro de sintaxe no comando de teste da API

- **Trecho pedido:** Validar `salvar_brutos`/`carregar_brutos` contra a API
- **Resposta da IA (resumo):** Gerou um comando `python -c` com a variável `de volta` (espaço no nome)
- **Decisão:** Primeira execução falhou com `SyntaxError`; a IA corrigiu para `volta` e o teste passou
- **Justificativa:** Erro de digitação no heredoc PowerShell, detectado na hora pelo retorno do Python
- **Como validei:** Segunda execução imprimiu `recarregados: 1000 == 1000`
