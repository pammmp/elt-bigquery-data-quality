SELECT
    TRIM(item_id)                                   AS item_id,
    TRIM(order_id)                                  AS order_id,
    UPPER(TRIM(sku))                                AS sku,
    {{TRY_CAST}}(quantity AS {{INT}})               AS quantity,
    {{TRY_CAST}}(unit_price AS {{DECIMAL}})         AS unit_price
FROM {{ ref('raw_order_items') }}
