SELECT
    TRIM(supplier_id)               AS supplier_id,
    TRIM(name)                      AS name,
    UPPER(TRIM(country))            AS country,
    LOWER(TRIM(active)) = 'true'    AS active
FROM {{ ref('raw_suppliers') }}
