"""Daily weather pipeline: ingest -> load raw -> dbt build -> reconciliation.

Runs on Cloud Composer or on a local Airflow (docker compose) pointed at the same GCP project.
Required Airflow Variables:
    weather_project      GCP project id
    weather_raw_bucket   raw-zone bucket (Terraform output raw_bucket)
    weather_function_url HTTPS URL of the ingestion Cloud Function (Terraform output function_url)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCheckOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.http.operators.http import HttpOperator

PROJECT = Variable.get("weather_project", default_var="my-gcp-project")
RAW_BUCKET = Variable.get("weather_raw_bucket", default_var="my-raw-bucket")
DBT_DIR = "/opt/airflow/dbt"

default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
}

with DAG(
    dag_id="weather_pipeline",
    description="Open-Meteo hourly weather for Chilean cities into BigQuery",
    start_date=datetime(2026, 11, 1),
    schedule="15 6 * * *",  # once a day, 06:15 UTC
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["portfolio", "gcp", "bigquery", "dbt"],
) as dag:
    ingest = HttpOperator(
        task_id="ingest_to_gcs",
        http_conn_id="weather_function",  # host = Cloud Function URL, auth via ID token
        endpoint="",
        method="POST",
        data='{"run_date": "{{ ds }}", "run_id": "{{ run_id | replace(":", "-") | replace("+", "-") }}", "past_days": 1}',
        headers={"Content-Type": "application/json"},
        response_filter=lambda r: r.json(),
        log_response=True,
    )

    load_raw = GCSToBigQueryOperator(
        task_id="load_raw_to_bigquery",
        bucket=RAW_BUCKET,
        source_objects=["raw/weather/dt={{ ds }}/*.json"],
        destination_project_dataset_table=f"{PROJECT}.weather_raw.hourly_observations",
        source_format="NEWLINE_DELIMITED_JSON",
        write_disposition="WRITE_APPEND",
        create_disposition="CREATE_NEVER",  # table + schema are owned by Terraform
        autodetect=False,
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {DBT_DIR} && dbt build --target prod --vars '{{\"run_date\": \"{{{{ ds }}}}\"}}'",
    )

    # Reconciliation: every hour ingested today must exist exactly once in the curated model.
    reconcile = BigQueryCheckOperator(
        task_id="reconcile_raw_vs_staging",
        use_legacy_sql=False,
        sql="""
            SELECT COUNT(*) = 0
            FROM (
              SELECT city, observed_at FROM `{project}.weather_raw.hourly_observations`
              WHERE DATE(ingested_at) = '{{{{ ds }}}}'
              EXCEPT DISTINCT
              SELECT city, observed_at FROM `{project}.weather_analytics.stg_weather_hourly`
            )
        """.format(project=PROJECT),
    )

    ingest >> load_raw >> dbt_build >> reconcile
