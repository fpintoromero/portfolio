terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  prefix = "weather-${var.env}"
  labels = { project = "weather-pipeline", env = var.env, managed_by = "terraform" }
}

# ---------- APIs ----------
resource "google_project_service" "apis" {
  for_each = toset([
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# ---------- Service account (least privilege) ----------
resource "google_service_account" "ingest" {
  account_id   = "${local.prefix}-ingest"
  display_name = "Weather ingestion function"
}

# ---------- Storage: raw zone + function source ----------
resource "google_storage_bucket" "raw" {
  name                        = "${var.project_id}-${local.prefix}-raw"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true # portfolio project: allow `terraform destroy`
  labels                      = local.labels

  lifecycle_rule {
    condition { age = var.raw_retention_days }
    action { type = "Delete" }
  }
}

resource "google_storage_bucket_iam_member" "ingest_writer" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.ingest.email}"
}

resource "google_storage_bucket" "source" {
  name                        = "${var.project_id}-${local.prefix}-fn-source"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
  labels                      = local.labels
}

data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../ingestion/cloud_function"
  output_path = "${path.module}/.build/function.zip"
  excludes    = ["__pycache__"]
}

resource "google_storage_bucket_object" "function_zip" {
  name   = "function-${data.archive_file.function_zip.output_md5}.zip"
  bucket = google_storage_bucket.source.name
  source = data.archive_file.function_zip.output_path
}

# ---------- Pub/Sub: "file landed" events ----------
resource "google_pubsub_topic" "landed" {
  name   = "${local.prefix}-raw-landed"
  labels = local.labels
}

resource "google_pubsub_topic_iam_member" "ingest_publisher" {
  topic  = google_pubsub_topic.landed.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.ingest.email}"
}

# ---------- Cloud Function (2nd gen) ----------
resource "google_cloudfunctions2_function" "ingest" {
  name     = "${local.prefix}-ingest"
  location = var.region
  labels   = local.labels

  build_config {
    runtime     = "python312"
    entry_point = "ingest_weather"
    source {
      storage_source {
        bucket = google_storage_bucket.source.name
        object = google_storage_bucket_object.function_zip.name
      }
    }
  }

  service_config {
    max_instance_count    = 1
    available_memory      = "256M"
    timeout_seconds       = 120
    service_account_email = google_service_account.ingest.email
    ingress_settings      = "ALLOW_ALL"
    environment_variables = {
      RAW_BUCKET   = google_storage_bucket.raw.name
      PUBSUB_TOPIC = google_pubsub_topic.landed.id
    }
  }

  depends_on = [google_project_service.apis]
}

# Only the orchestrator's identity may invoke the function (no public access).
resource "google_cloud_run_service_iam_member" "invoker" {
  location = google_cloudfunctions2_function.ingest.location
  service  = google_cloudfunctions2_function.ingest.name
  role     = "roles/run.invoker"
  member   = var.invoker_member
}

# ---------- BigQuery ----------
resource "google_bigquery_dataset" "raw" {
  dataset_id                 = "weather_raw"
  location                   = var.bq_location
  description                = "Landing zone loaded from GCS"
  delete_contents_on_destroy = true
  labels                     = local.labels
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id                 = "weather_analytics"
  location                   = var.bq_location
  description                = "dbt models (staging + marts)"
  delete_contents_on_destroy = true
  labels                     = local.labels
}

resource "google_bigquery_table" "hourly_observations" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "hourly_observations"
  deletion_protection = false
  labels              = local.labels

  time_partitioning {
    type          = "DAY"
    field         = "ingested_at"
    expiration_ms = var.raw_retention_days * 24 * 60 * 60 * 1000
  }
  clustering = ["city"]

  schema = file("${path.module}/schemas/hourly_observations.json")
}
