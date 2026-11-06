# BigQuery cost optimization — measure before you optimize

A repeatable method (and a small tool) to show how much partitioning and clustering reduce the bytes a
BigQuery query scans — and therefore its on-demand cost — using **dry runs only**, so the measurement itself
costs nothing.

It runs on the public dataset `bigquery-public-data.chicago_taxi_trips.taxi_trips`, so anyone can reproduce it.

## The method

1. **Baseline:** dry-run the typical queries (date filter, date + key filter, aggregation) against the
   original, unpartitioned table.
2. **Optimize:** create a copy partitioned by day and clustered by the most selective filter columns
   (`sql/01_create_optimized_table.sql`).
3. **Compare:** dry-run the exact same queries against the optimized table and report bytes and estimated
   cost side by side (`scripts/compare_dry_runs.py`).
4. **Guardrails:** `require_partition_filter`, `maximum_bytes_billed` and a check that flags queries
   scanning more than a threshold.

Note on clustering: dry runs report an *upper bound* for clustered tables, so the real savings from clustering
are usually larger than what the comparison shows; partition pruning, on the other hand, is reflected exactly.

## Run it

```bash
pip install google-cloud-bigquery
gcloud auth application-default login
export GCP_PROJECT=<your-project>

# one-time: create the optimized copy (this step does scan the source table once)
bq query --use_legacy_sql=false < sql/01_create_optimized_table.sql

# free: compare the queries with dry runs
python scripts/compare_dry_runs.py --project $GCP_PROJECT --dataset portfolio_cost
```

The script prints a table like:

```
query                       baseline_GB   optimized_GB   reduction   est_cost_baseline_USD   est_cost_optimized_USD
one_month_by_company        ...           ...            ...%        ...                     ...
```

Results depend on the date ranges you choose; the point of the project is the reproducible method, not a
single headline number.

## Files

```
sql/01_create_optimized_table.sql   baseline copy + partitioned/clustered copy (require_partition_filter)
sql/queries/*.sql                   the workload compared (templated with {table})
scripts/compare_dry_runs.py         dry-run runner + cost report
scripts/costing.py                  pure helpers (bytes → GB / USD, reduction %), unit-tested
tests/test_costing.py               pytest
```
