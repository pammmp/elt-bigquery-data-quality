"""Verificações de TEXTO dos arquivos do BigQuery (nada é executado no BigQuery)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ddl_has_partition_and_cluster():
    ddl = (ROOT / "bigquery" / "ddl_fct_orders.sql").read_text(encoding="utf-8")
    assert "PARTITION BY order_date" in ddl
    assert "CLUSTER BY supplier_id, status" in ddl


def test_render_bigquery_script_output():
    out = _load_script("render_bigquery").build("meu-proj.meu_ds")
    assert "CREATE TABLE `meu-proj.meu_ds.fct_orders`" in out
    assert "INSERT INTO `meu-proj.meu_ds.fct_orders`" in out
    assert "FROM `meu-proj.meu_ds.stg_orders`" in out
    assert "PROJETO.DATASET" not in out and "{{" not in out


def test_ddl_columns_match_the_model():
    ddl = (ROOT / "bigquery" / "ddl_fct_orders.sql").read_text(encoding="utf-8")
    model = (ROOT / "sql" / "marts" / "fct_orders.sql").read_text(encoding="utf-8")
    for col in ["order_id", "supplier_id", "order_date", "year_month", "status", "items_qty", "total_amount"]:
        assert col in ddl and col in model
