output "raw_bucket" {
  value = google_storage_bucket.raw.name
}

output "function_url" {
  value = google_cloudfunctions2_function.ingest.service_config[0].uri
}

output "pubsub_topic" {
  value = google_pubsub_topic.landed.id
}

output "raw_table" {
  value = "${var.project_id}.${google_bigquery_dataset.raw.dataset_id}.${google_bigquery_table.hourly_observations.table_id}"
}
