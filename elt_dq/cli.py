"""Linha de comando: python -m elt_dq run [--clean]"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from .generate_data import generate, write_csvs
from .pipeline import run_pipeline
from .runners import DuckDBRunner


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="elt_dq")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="gera dados fictícios e roda o pipeline com o gate")
    run.add_argument("--clean", action="store_true", help="dados sem defeitos plantados")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--orders", type=int, default=400)
    run.add_argument("--db", default=":memory:", help="arquivo DuckDB (padrão: memória)")
    run.add_argument("--report", help="grava o resultado em JSON")
    args = ap.parse_args(argv)

    tables, planted = generate(args.orders, args.seed, defects=not args.clean)
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = write_csvs(tables, Path(tmp))
        runner = DuckDBRunner(args.db)
        try:
            report = run_pipeline(runner, data_dir)
        finally:
            runner.close()

    print(f"Defeitos plantados: {planted if not args.clean else 'nenhum (--clean)'}\n")
    print(f"{'estágio':<9}{'severity':<9}{'violações':>10}  checagem")
    for r in report.results:
        mark = "ok " if r.passed else ("ERRO" if r.severity == "error" else "aviso")
        print(f"{r.stage:<9}{r.severity:<9}{r.violations:>10}  {mark:<5} {r.name}")
    print()
    if not report.gate_passed:
        print("GATE REPROVADO: a staging tem erros; as marts NÃO foram construídas.")
    elif report.failed_errors:
        print("Marts construídas, mas há checagens com erro.")
    else:
        print("Gate aprovado: marts construídas.")

    if args.report:
        Path(args.report).write_text(
            json.dumps(
                {
                    "planted_defects": planted,
                    "gate_passed": report.gate_passed,
                    "marts_built": report.marts_built,
                    "results": [r.__dict__ for r in report.results],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
