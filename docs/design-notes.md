# Notas de design

## Por que ELT e por que três camadas

- **raw**: os dados entram como chegaram (tudo texto). Assim dá para reprocessar e para ver o defeito original.
- **staging**: converte tipos (`TRY_CAST`/`SAFE_CAST` devolvem nulo em vez de quebrar), normaliza texto e remove duplicados, ficando com a linha mais recente de cada pedido.
- **marts**: tabelas prontas para consumo. Só são construídas se o gate aprovar a staging.

## O gate de qualidade

A staging é onde os erros ficam visíveis, depois da limpeza e antes do consumo. Se uma checagem `severity: error` reprova, as marts **não** são construídas: é melhor um relatório velho e correto do que um novo e errado. Checagens `warn` informam sem bloquear (por exemplo, status inesperado ou total do pedido divergente dos itens).

A checagem de `raw` é só informativa: mostra o que a staging vai corrigir (os duplicados), para o relatório dizer "o dado chegou com 15 duplicados e a staging resolveu".

## Uma checagem = um SQL que conta violações

Isso deixa tudo uniforme: o relatório mostra quantas linhas violam cada regra, e o mesmo SQL pode rodar em outro motor. Os SQLs das checagens usam só construções comuns ao DuckDB e ao BigQuery. O que muda entre os dois dialetos é tratado por marcadores em `elt_dq/dialect.py`.

## Testes: o que provam e o que não provam

- Cada tipo de checagem é testado com uma tabela minúscula que passa e outra que falha (incluindo bordas: nulos em `unique` e `relationships`, tabela vazia em `freshness`).
- O gerador planta uma quantidade conhecida de cada defeito, em pedidos disjuntos, e o teste de pipeline confere que as checagens encontram **exatamente** esses números.
- As marts são conferidas contra um cálculo independente em Python.
- Alterei o SQL de propósito (removendo a deduplicação e a normalização do status) para confirmar que os testes falham quando deveriam.
- **Não provam**: comportamento no BigQuery real, desempenho em volume, nem custo.

## Decisões que ficaram de fora

- Carga incremental, orquestração (Airflow, Cloud Composer), contratos de dados, linhagem.
- Execução das checagens no BigQuery: exigiria um executor para o BigQuery e credenciais.
- Alertas (e-mail, Slack) quando o gate reprova.
