variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region (e.g., us-central1)"
  type        = string
}
variable "service_name" {
  default = "mcp-server"
}
variable "source_dir" {
  description = "Path to the source code directory (relative to root)"
  type        = string
 
}