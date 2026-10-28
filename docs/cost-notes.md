# Notas de custo no BigQuery

> Estas notas resumem o que a documentação diz e o que eu **espero** observar. Nada foi medido neste repositório: os itens de medição estão em aberto no README.

## O que as fontes dizem

**Partição.** Uma tabela particionada é dividida em segmentos (partições). Quando a consulta filtra pela coluna de partição, o BigQuery "pode ler as partições que correspondem ao filtro e ignorar as demais", então lê menos bytes. A coluna pode ser inteira, ou de tipo `DATE`, `TIMESTAMP` ou `DATETIME`, ou pode-se usar o horário de ingestão.

**Cluster.** As colunas de cluster ordenam os blocos de armazenamento por seus valores; consultas que filtram por essas colunas leem só os blocos relevantes. A documentação avisa que:
- o limite é de **quatro** colunas de cluster;
- como os blocos a ler só são conhecidos quando a consulta roda, **não há estimativa de custo exata antes da execução**; para estimativas mais firmes, a página sugere usar partição;
- tabelas ou partições pequenas (menos de 64 MB) normalmente têm ganho desprezível.

**Boas práticas de custo.** Um artigo do Google Cloud recomenda estimar o custo com *dry run* antes de rodar, definir um limite de bytes cobrados (a consulta falha sem custo se a estimativa passar do limite) e lembra que `LIMIT` **não** reduz a quantidade de dados lidos.

## Como isso aparece neste repositório

- `bigquery/ddl_fct_orders.sql` particiona por `order_date` (as consultas de gasto costumam filtrar por período) e agrupa por `supplier_id, status`.
- `bigquery/cost_demo_queries.sql` traz a consulta A (sem filtro de data) e a B (filtrando março). O esperado é que a B processe menos bytes.
- `scripts/estimate_cost.py` faz o dry run das duas. **Nunca foi executado.**

## Não confirmado

- A opção `require_partition_filter` (que recusa consultas sem filtro de partição) aparece no DDL, mas **não a encontrei** nas páginas de documentação que li. Confira na sua versão antes de usar.
- Preço por TB processado e cotas: não verifiquei; consulte a página de preços atual.

## Fontes

- Google Cloud. *Introduction to partitioned tables* | BigQuery | Google Cloud Documentation. Atualizada em 26/10/2026. https://docs.cloud.google.com/bigquery/docs/partitioned-tables
- Google Cloud. *Introduction to clustered tables* | BigQuery | Google Cloud Documentation. Atualizada em 26/10/2026. https://docs.cloud.google.com/bigquery/docs/clustered-tables
- Pandey, Sonakshi. *Controlling your BigQuery costs*. Google Cloud Blog, 15/08/2022. https://cloud.google.com/blog/topics/developers-practitioners/controlling-your-bigquery-costs
