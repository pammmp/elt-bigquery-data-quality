"""Renderização do SQL para cada dialeto.

Os arquivos em sql/ usam dois marcadores:

  {{ ref('tabela') }}   -> nome da tabela, qualificado conforme o dialeto
  {{TRY_CAST}}, {{INT}}, {{DECIMAL}} -> diferenças entre DuckDB e BigQuery

O dialeto "duckdb" é o único executado neste repositório. O dialeto
"bigquery" só é renderizado (e testado como texto); ele nunca foi executado
em um BigQuery real aqui.
"""

from __future__ import annotations

import re

_TOKENS = {
    "duckdb": {"TRY_CAST": "TRY_CAST", "INT": "INTEGER", "DECIMAL": "DECIMAL(18,2)"},
    "bigquery": {"TRY_CAST": "SAFE_CAST", "INT": "INT64", "DECIMAL": "NUMERIC"},
}
_REF = re.compile(r"\{\{\s*ref\('(\w+)'\)\s*\}\}")
_TOKEN = re.compile(r"\{\{\s*([A-Z_]+)\s*\}\}")


def qualify(table: str, dialect: str, dataset: str | None = None) -> str:
    if dialect == "bigquery":
        if not dataset:
            raise ValueError("dataset (projeto.dataset) é obrigatório no BigQuery")
        return f"`{dataset}.{table}`"
    return table


def render(sql: str, dialect: str = "duckdb", dataset: str | None = None) -> str:
    if dialect not in _TOKENS:
        raise ValueError(f"dialeto desconhecido: {dialect}")
    sql = _REF.sub(lambda m: qualify(m.group(1), dialect, dataset), sql)

    def token(m: re.Match) -> str:
        key = m.group(1)
        if key not in _TOKENS[dialect]:
            raise ValueError(f"marcador desconhecido: {key}")
        return _TOKENS[dialect][key]

    return _TOKEN.sub(token, sql)
