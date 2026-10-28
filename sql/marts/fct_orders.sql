-- Uma linha por pedido, com o total recalculado a partir dos itens.
SELECT
    o.order_id,
    o.supplier_id,
    o.order_date,
    EXTRACT(YEAR FROM o.order_date) * 100
        + EXTRACT(MONTH FROM o.order_date)      AS year_month,
    o.status,
    COALESCE(i.items_qty, 0)                    AS items_qty,
    COALESCE(i.items_total, 0)                  AS total_amount
FROM {{ ref('stg_orders') }} AS o
LEFT JOIN (
    SELECT
        order_id,
        SUM(quantity)                AS items_qty,
        SUM(quantity * unit_price)   AS items_total
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id
) AS i
    ON o.order_id = i.order_id
