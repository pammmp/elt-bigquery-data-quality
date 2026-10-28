-- Duas consultas para comparar o custo (bytes processados) com dry run.
-- Resultado esperado: a B lê menos bytes que a A, porque só varre as partições
-- de março. Isso é o ESPERADO pela documentação; NÃO foi medido aqui.
-- Meça com: python scripts/estimate_cost.py --project P --dataset D --sql-file <arquivo>

-- A) sem filtro na coluna de partição (varre a tabela toda;
--    com require_partition_filter = TRUE, esta consulta é recusada)
SELECT supplier_id, SUM(total_amount) AS gasto
FROM {{ ref('fct_orders') }}
GROUP BY supplier_id;

-- B) com filtro na coluna de partição (varre só as partições de março)
SELECT supplier_id, SUM(total_amount) AS gasto
FROM {{ ref('fct_orders') }}
WHERE order_date BETWEEN '2026-03-01' AND '2026-03-31'
GROUP BY supplier_id;
