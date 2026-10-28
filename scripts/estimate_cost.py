"""Estima os bytes processados de uma consulta com dry run (não executa a consulta).

NÃO TESTADO: este script nunca foi executado contra um BigQuery real.
Requer: pip install -r requirements-bigquery.txt e credenciais do Google Cloud.

  python scripts/estimate_cost.py --project P --dataset D --sql-file arquivo.sql
O arquivo pode ter várias consultas separadas por ';'.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from elt_dq.dialect import render  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--sql-file", required=True)
    args = ap.parse_args()

    from google.cloud import bigquery

    client = bigquery.Client(project=args.project)
    sql = render(
        Path(args.sql_file).read_text(encoding="utf-8"),
        "bigquery",
        f"{args.project}.{args.dataset}",
    )
    cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    for i, statement in enumerate(s.strip() for s in sql.split(";") if s.strip()):
        job = client.query(statement, job_config=cfg)
        print(f"consulta {i + 1}: {job.total_bytes_processed:,} bytes (estimativa)")


if __name__ == "__main__":
    main()
