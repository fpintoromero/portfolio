# Francisco Pinto — Senior Data Engineer (Google Cloud)

Data engineer based in Santiago, Chile, with 6+ years building and optimizing data platforms on Google Cloud
for telecom, retail, consumer goods and financial services companies (WOM, FEMSA, Falabella, Sodimac).

**What I do:** batch and event-driven pipelines on GCP, BigQuery performance and cost optimization,
Airflow / Cloud Composer orchestration, dbt and Dataform modeling, infrastructure as code with Terraform,
and data quality / reconciliation between systems.

**How I work:** remote and asynchronous, written updates, small well-scoped deliverables,
read-only access first and production changes only with approval.

## Projects

| Project | What it demonstrates | Stack |
|---|---|---|
| [GCP Weather Pipeline](projects/gcp-weather-pipeline) | End-to-end batch pipeline: API ingestion → GCS raw zone → BigQuery → dbt marts, with deduplication, incremental partitions, data quality tests and raw-vs-curated reconciliation | Cloud Functions, Pub/Sub, GCS, BigQuery, Airflow, dbt, Terraform, pytest |
| [BigQuery Cost Optimization](projects/bigquery-cost-optimization) | A reproducible, zero-cost method (dry runs) to measure how partitioning and clustering cut scanned bytes, plus guardrails | BigQuery, SQL, Python |

Both projects use public data only and include CI (GitHub Actions) that runs the test suite on every push.

## Skills

- **Google Cloud:** BigQuery, Cloud Composer (Airflow), Dataform, Dataflow, Pub/Sub, Cloud Functions, Cloud Run,
  Cloud Storage, Secret Manager, IAM
- **Transformation & orchestration:** dbt, Dataform, Apache Airflow, Informatica PowerCenter, SSIS
- **Languages:** Python (pandas, requests, pytest), SQL (BigQuery, T-SQL, PL/SQL)
- **DevOps:** Terraform, GitLab CI, GitHub Actions, Docker, Kubernetes (basic)
- **Applied AI:** LLM APIs with Python to automate code migrations (stored procedures → Dataform SQLX)

## Contact

- LinkedIn: [linkedin.com/in/francisco-pinto-375144166](https://www.linkedin.com/in/francisco-pinto-375144166)
