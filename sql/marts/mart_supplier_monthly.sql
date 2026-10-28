-- Gasto mensal por fornecedor (pedidos cancelados ficam de fora).
SELECT
    f.supplier_id,
    d.name                      AS supplier_name,
    f.year_month,
    COUNT(*)                    AS orders_count,
    SUM(f.total_amount)         AS total_spend
FROM {{ ref('fct_orders') }} AS f
JOIN {{ ref('dim_suppliers') }} AS d
    ON f.supplier_id = d.supplier_id
WHERE f.status <> 'cancelado'
GROUP BY f.supplier_id, d.name, f.year_month
