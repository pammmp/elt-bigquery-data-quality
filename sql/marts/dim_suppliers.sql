SELECT supplier_id, name, country, active
FROM {{ ref('stg_suppliers') }}
