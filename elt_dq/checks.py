"""Checagens de qualidade de dados.

Cada checagem vira um SQL que devolve o número de violações. Zero = passou.
O SQL usa só construções comuns ao DuckDB e ao BigQuery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

import yaml

KINDS = {
    "not_null",
    "unique",
    "accepted_values",
    "relationships",
    "range",
    "freshness",
    "row_count_min",
    "reconciliation",
}


@dataclass
class Check:
    stage: str
    kind: str
    table: str
    severity: str = "error"
    params: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        target = self.params.get("column") or ",".join(self.params.get("columns", []))
        return f"{self.kind}:{self.table}" + (f".{target}" if target else "")

    def sql(self, q: Callable[[str], str], as_of: date | None = None) -> str:
        """SQL que conta as violações. q() qualifica o nome de uma tabela."""
        p = self.params
        t = q(self.table)
        if self.kind == "not_null":
            return f"SELECT COUNT(*) FROM {t} WHERE {p['column']} IS NULL"
        if self.kind == "unique":
            cols = ", ".join(p["columns"])
            nn = " AND ".join(f"{c} IS NOT NULL" for c in p["columns"])
            return (
                f"SELECT COUNT(*) FROM (SELECT {cols} FROM {t} WHERE {nn} "
                f"GROUP BY {cols} HAVING COUNT(*) > 1) AS dup"
            )
        if self.kind == "accepted_values":
            vals = ", ".join("'" + str(v).replace("'", "''") + "'" for v in p["values"])
            c = p["column"]
            return (
                f"SELECT COUNT(*) FROM {t} "
                f"WHERE {c} IS NOT NULL AND {c} NOT IN ({vals})"
            )
        if self.kind == "relationships":
            return (
                f"SELECT COUNT(*) FROM {t} AS c "
                f"LEFT JOIN {q(p['to_table'])} AS p ON c.{p['column']} = p.{p['to_column']} "
                f"WHERE c.{p['column']} IS NOT NULL AND p.{p['to_column']} IS NULL"
            )
        if self.kind == "range":
            c = p["column"]
            conds = []
            if "min" in p:
                conds.append(f"{c} < {p['min']}")
            if "max" in p:
                conds.append(f"{c} > {p['max']}")
            if not conds:
                raise ValueError("range exige min e/ou max")
            return (
                f"SELECT COUNT(*) FROM {t} "
                f"WHERE {c} IS NOT NULL AND ({' OR '.join(conds)})"
            )
        if self.kind == "freshness":
            if as_of is None:
                raise ValueError("freshness exige as_of")
            cutoff = as_of - timedelta(days=int(p["max_age_days"]))
            return (
                f"SELECT CASE WHEN MAX({p['column']}) >= DATE '{cutoff.isoformat()}' "
                f"THEN 0 ELSE 1 END FROM {t}"
            )
        if self.kind == "row_count_min":
            return f"SELECT CASE WHEN COUNT(*) >= {int(p['min'])} THEN 0 ELSE 1 END FROM {t}"
        if self.kind == "reconciliation":
            return (
                f"SELECT COUNT(*) FROM {t} AS a JOIN ("
                f"SELECT {p['against_key']} AS k, SUM({p['against_value']}) AS v "
                f"FROM {q(p['against_table'])} GROUP BY {p['against_key']}"
                f") AS s ON a.{p['key']} = s.k "
                f"WHERE ABS(a.{p['value']} - s.v) > {p.get('tolerance', 0)}"
            )
        raise ValueError(f"tipo de checagem desconhecido: {self.kind}")


@dataclass
class CheckResult:
    name: str
    stage: str
    severity: str
    violations: int

    @property
    def passed(self) -> bool:
        return self.violations == 0


def load_checks(path: str | Path) -> tuple[list[Check], date | None]:
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    as_of = cfg.get("as_of")
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)
    checks = []
    for item in cfg["checks"]:
        item = dict(item)
        kind = item.pop("type")
        if kind not in KINDS:
            raise ValueError(f"tipo de checagem desconhecido: {kind}")
        severity = item.pop("severity", "error")
        if severity not in ("error", "warn"):
            raise ValueError(f"severity inválida: {severity}")
        stage = item.pop("stage")
        table = item.pop("table")
        checks.append(Check(stage, kind, table, severity, item))
    return checks, as_of
