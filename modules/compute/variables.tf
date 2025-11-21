variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region (e.g., us-central1)"
  type        = string
}

variable "zone" {
  default = "us-central1-a"
}

variable "network_name" {
  default = "agent-vpc"
}
variable "subnet_name" {
  default = "sub-us-central1"
}

variable "service_account_email" {
  description = "The email of the Service Account that needs to read the API Key"
  type        = string
}

variable "code_bucket_name" {
  description = "Name of the bucket where code is stored (for startup script)"
  type        = string
}
variable "secure_tag_value_id" {
  description = "The namespaced ID of the Secure Tag (app:agent)"
  type        = string
}
