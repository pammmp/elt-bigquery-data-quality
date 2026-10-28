"""Cada tipo de checagem, com uma tabela minúscula que passa e outra que falha."""

from datetime import date

import pytest

from elt_dq.checks import Check, load_checks


def q(t):
    return t


def violations(runner, check, as_of=None):
    return int(runner.scalar(check.sql(q, as_of)))


def test_not_null(runner):
    runner.execute("CREATE TABLE t AS SELECT * FROM (VALUES (1), (NULL), (NULL)) v(a)")
    assert violations(runner, Check("s", "not_null", "t", params={"column": "a"})) == 2


def test_unique_single_and_composite(runner):
    runner.execute("CREATE TABLE t AS SELECT * FROM (VALUES (1,'x'),(1,'y'),(2,'x'),(2,'x')) v(a,b)")
    assert violations(runner, Check("s", "unique", "t", params={"columns": ["a"]})) == 2
    assert violations(runner, Check("s", "unique", "t", params={"columns": ["a", "b"]})) == 1


def test_unique_ignores_nulls(runner):
    runner.execute("CREATE TABLE t AS SELECT * FROM (VALUES (NULL),(NULL),(1)) v(a)")
    assert violations(runner, Check("s", "unique", "t", params={"columns": ["a"]})) == 0


def test_accepted_values(runner):
    runner.execute("CREATE TABLE t AS SELECT * FROM (VALUES ('a'),('b'),('z'),(NULL)) v(s)")
    c = Check("s", "accepted_values", "t", params={"column": "s", "values": ["a", "b"]})
    assert violations(runner, c) == 1


def test_relationships_ignores_null_children(runner):
    runner.execute("CREATE TABLE child AS SELECT * FROM (VALUES (1),(2),(9),(NULL)) v(k)")
    runner.execute("CREATE TABLE parent AS SELECT * FROM (VALUES (1),(2)) v(k)")
    c = Check(
        "s", "relationships", "child",
        params={"column": "k", "to_table": "parent", "to_column": "k"},
    )
    assert violations(runner, c) == 1


def test_range(runner):
    runner.execute("CREATE TABLE t AS SELECT * FROM (VALUES (-1),(0),(5),(11),(NULL)) v(n)")
    assert violations(runner, Check("s", "range", "t", params={"column": "n", "min": 0})) == 1
    assert violations(runner, Check("s", "range", "t", params={"column": "n", "max": 10})) == 1
    assert (
        violations(runner, Check("s", "range", "t", params={"column": "n", "min": 0, "max": 10}))
        == 2
    )
    with pytest.raises(ValueError):
        Check("s", "range", "t", params={"column": "n"}).sql(q)


def test_freshness(runner):
    runner.execute("CREATE TABLE t AS SELECT DATE '2026-06-20' AS d")
    c = Check("s", "freshness", "t", params={"column": "d", "max_age_days": 10})
    assert violations(runner, c, date(2026, 6, 30)) == 0
    assert violations(runner, c, date(2026, 7, 5)) == 1
    runner.execute("CREATE TABLE e AS SELECT DATE '2026-01-01' AS d WHERE 1 = 0")
    empty = Check("s", "freshness", "e", params={"column": "d", "max_age_days": 10})
    assert violations(runner, empty, date(2026, 6, 30)) == 1  # tabela vazia reprova


def test_row_count_min(runner):
    runner.execute("CREATE TABLE t AS SELECT * FROM (VALUES (1),(2)) v(a)")
    assert violations(runner, Check("s", "row_count_min", "t", params={"min": 2})) == 0
    assert violations(runner, Check("s", "row_count_min", "t", params={"min": 3})) == 1


def test_reconciliation(runner):
    runner.execute("CREATE TABLE h AS SELECT * FROM (VALUES ('a', 10.00), ('b', 99.00)) v(k, total)")
    runner.execute(
        "CREATE TABLE i AS SELECT * FROM (VALUES ('a',2,5.00),('b',1,50.00),('b',1,49.00)) v(k,q,p)"
    )
    c = Check(
        "s", "reconciliation", "h",
        params={
            "key": "k", "value": "total", "against_table": "i", "against_key": "k",
            "against_value": "q * p", "tolerance": 0.01,
        },
    )
    assert violations(runner, c) == 0
    runner.execute("UPDATE h SET total = 11 WHERE k = 'a'")
    assert violations(runner, c) == 1


def test_config_loads_and_rejects_bad_input(tmp_path):
    checks, as_of = load_checks("checks/checks.yml")
    assert as_of == date(2026, 6, 30)
    assert {c.stage for c in checks} == {"raw", "staging", "marts"}
    bad = tmp_path / "bad.yml"
    bad.write_text("checks:\n  - {stage: raw, type: inventado, table: t}\n")
    with pytest.raises(ValueError):
        load_checks(bad)
    bad.write_text("checks:\n  - {stage: raw, type: not_null, table: t, severity: grave}\n")
    with pytest.raises(ValueError):
        load_checks(bad)
