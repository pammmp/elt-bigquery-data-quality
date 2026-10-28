from pathlib import Path

import pytest

from elt_dq.dialect import qualify, render

ROOT = Path(__file__).resolve().parent.parent


def test_duckdb_rendering():
    sql = "SELECT {{TRY_CAST}}(x AS {{INT}}) FROM {{ ref('t') }}"
    assert render(sql, "duckdb") == "SELECT TRY_CAST(x AS INTEGER) FROM t"


def test_bigquery_rendering():
    sql = "SELECT {{TRY_CAST}}(x AS {{DECIMAL}}) FROM {{ ref('t') }}"
    assert render(sql, "bigquery", "proj.ds") == (
        "SELECT SAFE_CAST(x AS NUMERIC) FROM `proj.ds.t`"
    )


def test_bigquery_requires_dataset():
    with pytest.raises(ValueError):
        qualify("t", "bigquery")


def test_unknown_token_and_dialect_fail():
    with pytest.raises(ValueError):
        render("{{NOPE}}", "duckdb")
    with pytest.raises(ValueError):
        render("SELECT 1", "oracle")


@pytest.mark.parametrize("dialect", ["duckdb", "bigquery"])
def test_every_sql_file_renders_without_leftovers(dialect):
    files = list((ROOT / "sql").rglob("*.sql")) + list((ROOT / "bigquery").glob("*.sql"))
    assert files
    for f in files:
        out = render(f.read_text(encoding="utf-8"), dialect, "proj.ds")
        assert "{{" not in out and "}}" not in out, f
        if dialect == "bigquery":
            assert "TRY_CAST(" not in out.replace("SAFE_CAST(", "")
