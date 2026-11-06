"""Dry-run every query in sql/queries against the baseline and the optimized table and print a cost report.

Dry runs are free: BigQuery only plans the query and returns the bytes it would process.

Usage:
    python scripts/compare_dry_runs.py --project my-project --dataset portfolio_cost
"""

from __future__ import annotations

import argparse
from pathlib import Path

from costing import DEFAULT_USD_PER_TIB, Comparison, render_table

QUERIES_DIR = Path(__file__).resolve().parents[1] / "sql" / "queries"


def dry_run_bytes(client, sql: str) -> int:
    from google.cloud import bigquery

    job = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    return int(job.total_bytes_processed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--dataset", default="portfolio_cost")
    parser.add_argument("--usd-per-tib", type=float, default=DEFAULT_USD_PER_TIB)
    args = parser.parse_args()

    from google.cloud import bigquery

    client = bigquery.Client(project=args.project)
    baseline = f"`{args.project}.{args.dataset}.taxi_trips_baseline`"
    optimized = f"`{args.project}.{args.dataset}.taxi_trips_optimized`"

    rows = []
    for path in sorted(QUERIES_DIR.glob("*.sql")):
        template = path.read_text()
        rows.append(
            Comparison(
                query=path.stem,
                baseline_bytes=dry_run_bytes(client, template.format(table=baseline)),
                optimized_bytes=dry_run_bytes(client, template.format(table=optimized)),
            )
        )
    print(render_table(rows, args.usd_per_tib))


if __name__ == "__main__":
    main()
