-- Consultas de validação do ETL Verdejar — banco: PostgreSQL (insumos/schema.sql).
-- Uso: psql -U <usuario> -d <banco> -f consultas_validacao.sql
-- Equivalente SQLite da consulta (a): trocar DATE_TRUNC('month', data_pedido)
-- por strftime('%Y-%m', data_pedido) e agrupar pelo texto.

-- (a) Total de vendas por mês: quanto faturou e quantos pedidos houve em cada mês.
SELECT DATE_TRUNC('month', data_pedido) AS mes,
       COUNT(*)                        AS qtd_pedidos,
       SUM(valor_total)                AS total_vendas
FROM pedidos
GROUP BY 1
ORDER BY 1;
-- Resultado (5000 pedidos):
--   2026-01-01 | 488 | 30449.02
--   2026-02-01 | 536 | 33923.86
--   2026-03-01 | 487 | 30678.70
--   2026-04-01 | 521 | 31253.96
--   2026-05-01 | 512 | 30890.02
--   2026-06-01 | 523 | 31627.73
--   2026-07-01 | 519 | 32796.17
--   2026-08-01 | 458 | 29328.04
--   2026-09-01 | 476 | 29995.71
--   2026-10-01 | 480 | 31104.54
--   total      | 5000 | 312047.75  (conferência (d): 312047.75 = 312047.75 → OK)

-- (b) Quantidade de pedidos por estado: onde estão os clientes que compraram.
SELECT c.estado,
       COUNT(*) AS qtd_pedidos
FROM pedidos p
JOIN clientes c ON c.id = p.cliente_id
GROUP BY c.estado
ORDER BY qtd_pedidos DESC, c.estado;
-- Resultado: RS 1543, SC 1127, PR 974, SP 880, MG 476 (soma 5000).

-- (c) Pedidos divergentes: valor_total difere da soma real dos itens (flag A6).
SELECT p.id,
       p.data_pedido,
       p.valor_total,
       p.valor_itens,
       p.valor_total - p.valor_itens AS diferenca
FROM pedidos p
WHERE p.divergente
ORDER BY ABS(p.valor_total - p.valor_itens) DESC, p.id;
-- Resultado: 238 pedidos divergentes (diferenças +10.00, -5.00, +3.00);
-- bate com o contador A6 impresso pelo ETL.

-- (d) Conferência: a soma dos totais mensais tem de bater com o total geral
--     da tabela de pedidos; 'conferencia' vem OK ou FALHA.
SELECT total_geral,
       soma_mensal,
       CASE WHEN total_geral = soma_mensal THEN 'OK' ELSE 'FALHA' END AS conferencia
FROM (
    SELECT (SELECT COALESCE(SUM(valor_total), 0) FROM pedidos) AS total_geral,
           (SELECT COALESCE(SUM(mes_total), 0)
              FROM (SELECT SUM(valor_total) AS mes_total
                      FROM pedidos
                     GROUP BY DATE_TRUNC('month', data_pedido)) meses) AS soma_mensal
) t;
-- Resultado: total_geral 312047.75, soma_mensal 312047.75, conferencia OK.
