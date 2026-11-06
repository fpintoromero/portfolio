variable "project_id" {
  description = "GCP project id"
  type        = string
}

variable "region" {
  description = "Region for the function and buckets"
  type        = string
  default     = "us-central1"
}

variable "bq_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "env" {
  description = "Environment suffix (dev, prod)"
  type        = string
  default     = "dev"
}

variable "raw_retention_days" {
  description = "Days to keep raw files and raw partitions"
  type        = number
  default     = 30
}

variable "invoker_member" {
  description = "IAM member allowed to call the function, e.g. serviceAccount:airflow@<project>.iam.gserviceaccount.com or user:me@example.com"
  type        = string
}
