"""Imprime o DDL e o INSERT da fct_orders já no dialeto do BigQuery.

Só gera texto; não executa nada. Uso:
  python scripts/render_bigquery.py --dataset meu-projeto.meu_dataset
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from elt_dq.dialect import render  # noqa: E402


def build(dataset: str) -> str:
    ddl = (ROOT / "bigquery" / "ddl_fct_orders.sql").read_text(encoding="utf-8")
    ddl = ddl.replace("PROJETO.DATASET", dataset)
    model = (ROOT / "sql" / "marts" / "fct_orders.sql").read_text(encoding="utf-8")
    insert = (
        f"INSERT INTO `{dataset}.fct_orders` "
        f"(order_id, supplier_id, order_date, year_month, status, items_qty, total_amount)\n"
        + render(model, "bigquery", dataset)
    )
    return ddl + "\n" + insert + ";\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="projeto.dataset")
    print(build(ap.parse_args().dataset))
