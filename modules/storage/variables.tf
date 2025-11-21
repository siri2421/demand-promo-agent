variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region (e.g., us-central1)"
  type        = string
}

variable "service_account_email" {
  description = "The email of the Service Account that needs to read the API Key"
  type        = string
}