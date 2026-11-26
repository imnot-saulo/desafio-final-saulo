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

-- (b) Quantidade de pedidos por estado: onde estão os clientes que compraram.
SELECT c.estado,
       COUNT(*) AS qtd_pedidos
FROM pedidos p
JOIN clientes c ON c.id = p.cliente_id
GROUP BY c.estado
ORDER BY qtd_pedidos DESC, c.estado;

-- (c) Pedidos divergentes: valor_total difere da soma real dos itens (flag A6).
SELECT p.id,
       p.data_pedido,
       p.valor_total,
       p.valor_itens,
       p.valor_total - p.valor_itens AS diferenca
FROM pedidos p
WHERE p.divergente
ORDER BY ABS(p.valor_total - p.valor_itens) DESC, p.id;

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
