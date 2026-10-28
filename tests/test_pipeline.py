import json

import pytest

from elt_dq.cli import main
from elt_dq.pipeline import run_pipeline


def by_name(report):
    return {r.name: r for r in report.results}


def test_gate_blocks_marts_and_finds_exactly_the_planted_defects(runner, dirty):
    _, planted, data_dir = dirty
    report = run_pipeline(runner, data_dir)
    r = by_name(report)

    assert report.gate_passed is False
    assert report.marts_built is False
    assert not report.ok
    # as marts não podem existir
    tables = {row[0] for row in runner.con.execute("SHOW TABLES").fetchall()}
    assert "fct_orders" not in tables and "stg_orders" in tables

    assert r["unique:raw_orders.order_id"].violations == planted["duplicate_orders"]
    assert r["unique:stg_orders.order_id"].violations == 0  # a staging deduplicou
    assert r["not_null:stg_orders.supplier_id"].violations == planted["null_supplier"]
    assert r["relationships:stg_orders.supplier_id"].violations == planted["orphan_supplier"]
    assert r["accepted_values:stg_orders.status"].violations == planted["invalid_status"]
    assert r["range:stg_order_items.quantity"].violations == planted["negative_quantity"]
    assert r["reconciliation:stg_orders"].violations == planted["total_mismatch"]


def test_staging_normalizes_status_and_dedupes(runner, dirty):
    tables, planted, data_dir = dirty
    run_pipeline(runner, data_dir)
    n_orders = runner.scalar("SELECT COUNT(*) FROM stg_orders")
    assert n_orders == len(tables["orders"]) - planted["duplicate_orders"] == 400
    assert runner.scalar("SELECT COUNT(*) FROM stg_orders WHERE status <> TRIM(LOWER(status))") == 0


def test_clean_data_passes_and_builds_marts(runner, clean):
    _, _, data_dir = clean
    report = run_pipeline(runner, data_dir)
    assert report.ok and report.gate_passed and report.marts_built
    assert all(r.passed for r in report.results)
    assert runner.scalar("SELECT COUNT(*) FROM fct_orders") == 400


def test_mart_numbers_match_an_independent_calculation(runner, clean):
    tables, _, data_dir = clean
    run_pipeline(runner, data_dir)

    status = {o["order_id"]: o["status"] for o in tables["orders"]}
    expected = round(
        sum(
            int(i["quantity"]) * float(i["unit_price"])
            for i in tables["order_items"]
            if status[i["order_id"]] != "cancelado"
        ),
        2,
    )
    got = float(runner.scalar("SELECT SUM(total_spend) FROM mart_supplier_monthly"))
    assert got == pytest.approx(expected, abs=0.05)

    # fct_orders recalcula o total a partir dos itens e deve bater com o cabeçalho
    header = {o["order_id"]: float(o["total_amount"]) for o in tables["orders"]}
    rows = runner.con.execute("SELECT order_id, total_amount FROM fct_orders").fetchall()
    assert all(float(t) == pytest.approx(header[o], abs=0.01) for o, t in rows)


def test_cli_exit_codes_and_report(tmp_path, capsys):
    report_file = tmp_path / "report.json"
    assert main(["run", "--report", str(report_file)]) == 1
    data = json.loads(report_file.read_text(encoding="utf-8"))
    assert data["gate_passed"] is False and data["marts_built"] is False
    assert main(["run", "--clean"]) == 0
    assert "Gate aprovado" in capsys.readouterr().out
