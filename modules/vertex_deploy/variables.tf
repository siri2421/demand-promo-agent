variable "project_id" {}
variable "region" {}
variable "agent_source_path" {
  description = "Path to the agent source code (e.g., promo-agent/multi_agent)"
  type        = string
}
# We need dependencies to ensure .env exists before running
variable "dependency_signal" {
  type    = string
  default = ""
}