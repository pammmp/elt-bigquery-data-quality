"""Pipeline ELT local: raw -> staging -> (gate de qualidade) -> marts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .checks import Check, CheckResult, load_checks
from .dialect import qualify, render
from .runners import DuckDBRunner

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
CHECKS_FILE = ROOT / "checks" / "checks.yml"

RAW_TABLES = ["suppliers", "orders", "order_items"]
STAGING = ["stg_suppliers", "stg_orders", "stg_order_items"]
MARTS = ["dim_suppliers", "fct_orders", "mart_supplier_monthly"]


@dataclass
class PipelineReport:
    results: list[CheckResult] = field(default_factory=list)
    gate_passed: bool = True
    marts_built: bool = False

    @property
    def failed_errors(self) -> list[CheckResult]:
        return [r for r in self.results if r.severity == "error" and not r.passed]

    @property
    def ok(self) -> bool:
        return self.gate_passed and not self.failed_errors


def load_raw(runner: DuckDBRunner, data_dir: str | Path) -> None:
    """Carrega os CSVs como estão (tudo texto), sem corrigir nada."""
    for name in RAW_TABLES:
        path = str(Path(data_dir) / f"{name}.csv").replace("'", "''")
        runner.execute(
            f"CREATE OR REPLACE TABLE raw_{name} AS "
            f"SELECT * FROM read_csv('{path}', header=true, all_varchar=true)"
        )


def build_model(runner: DuckDBRunner, name: str, layer: str, sql_dir: Path = SQL_DIR) -> None:
    sql = (sql_dir / layer / f"{name}.sql").read_text(encoding="utf-8")
    body = render(sql, runner.dialect, runner.dataset)
    runner.execute(f"CREATE OR REPLACE TABLE {name} AS\n{body}")


def run_checks(runner, checks: list[Check], as_of, stage: str) -> list[CheckResult]:
    def q(table: str) -> str:
        return qualify(table, runner.dialect, runner.dataset)

    results = []
    for c in (c for c in checks if c.stage == stage):
        violations = int(runner.scalar(c.sql(q, as_of)))
        results.append(CheckResult(c.name, c.stage, c.severity, violations))
    return results


def run_pipeline(
    runner: DuckDBRunner,
    data_dir: str | Path,
    checks_file: Path = CHECKS_FILE,
    sql_dir: Path = SQL_DIR,
) -> PipelineReport:
    checks, as_of = load_checks(checks_file)
    report = PipelineReport()

    load_raw(runner, data_dir)
    report.results += run_checks(runner, checks, as_of, "raw")

    for name in STAGING:
        build_model(runner, name, "staging", sql_dir)
    report.results += run_checks(runner, checks, as_of, "staging")

    # gate: erro na staging impede a construção das marts
    if any(r.severity == "error" and not r.passed for r in report.results):
        report.gate_passed = False
        return report

    for name in MARTS:
        build_model(runner, name, "marts", sql_dir)
    report.marts_built = True
    report.results += run_checks(runner, checks, as_of, "marts")
    return report
