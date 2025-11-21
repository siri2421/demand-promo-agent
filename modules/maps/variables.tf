variable "project_id" {}

variable "app_service_account_email" {
  description = "The email of the Service Account that needs to read the API Key"
  type        = string
}