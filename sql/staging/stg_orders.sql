-- Tipagem, normalização e deduplicação (fica a linha mais recente de cada pedido).
SELECT
    order_id,
    supplier_id,
    order_date,
    status,
    total_amount,
    updated_at
FROM (
    SELECT
        TRIM(order_id)                                  AS order_id,
        NULLIF(TRIM(supplier_id), '')                   AS supplier_id,
        {{TRY_CAST}}(TRIM(order_date) AS DATE)          AS order_date,
        LOWER(TRIM(status))                             AS status,
        {{TRY_CAST}}(total_amount AS {{DECIMAL}})       AS total_amount,
        {{TRY_CAST}}(updated_at AS TIMESTAMP)           AS updated_at,
        ROW_NUMBER() OVER (
            PARTITION BY TRIM(order_id)
            ORDER BY {{TRY_CAST}}(updated_at AS TIMESTAMP) DESC
        )                                               AS rn
    FROM {{ ref('raw_orders') }}
) AS ranked
WHERE rn = 1
