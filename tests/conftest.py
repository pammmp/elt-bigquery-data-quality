import pytest

from elt_dq.generate_data import generate, write_csvs
from elt_dq.runners import DuckDBRunner


@pytest.fixture
def runner():
    r = DuckDBRunner()
    yield r
    r.close()


@pytest.fixture
def dirty(tmp_path):
    tables, planted = generate(400, seed=42, defects=True)
    return tables, planted, write_csvs(tables, tmp_path / "dirty")


@pytest.fixture
def clean(tmp_path):
    tables, planted = generate(400, seed=42, defects=False)
    return tables, planted, write_csvs(tables, tmp_path / "clean")
