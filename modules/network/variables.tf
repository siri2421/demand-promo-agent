variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region (e.g., us-central1)"
  type        = string
}


variable "network_name" {
  default = "agent-vpc"
}
variable "subnet_name" {
  default = "sub-us-central1"
}