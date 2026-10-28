-- DDL da tabela fato no BigQuery, com partição por data e clusterização.
-- NUNCA foi executado em um BigQuery real neste repositório.
-- Troque PROJETO.DATASET pelo seu, ou gere com:
--   python scripts/render_bigquery.py --dataset SEU_PROJETO.SEU_DATASET
--
-- Decisões:
--   * PARTITION BY order_date: a maioria das consultas de gasto filtra por período.
--   * CLUSTER BY supplier_id, status: colunas usadas em filtros e agrupamentos.
--   * require_partition_filter: obriga a consulta a filtrar por data, para
--     ninguém varrer a tabela inteira sem querer. (Opção não confirmada nas
--     páginas de documentação lidas; confira na sua versão.)

CREATE TABLE `PROJETO.DATASET.fct_orders` (
    order_id     STRING,
    supplier_id  STRING,
    order_date   DATE,
    year_month   INT64,
    status       STRING,
    items_qty    INT64,
    total_amount NUMERIC
)
PARTITION BY order_date
CLUSTER BY supplier_id, status
OPTIONS (require_partition_filter = TRUE);
