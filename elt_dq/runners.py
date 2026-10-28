"""Executores de SQL. Só o DuckDB está implementado neste repositório."""

from __future__ import annotations

import duckdb


class DuckDBRunner:
    dialect = "duckdb"
    dataset = None

    def __init__(self, database: str = ":memory:"):
        self.con = duckdb.connect(database)

    def execute(self, sql: str) -> None:
        self.con.execute(sql)

    def scalar(self, sql: str):
        return self.con.execute(sql).fetchone()[0]

    def close(self) -> None:
        self.con.close()
