variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region (e.g., us-central1)"
  type        = string
}

variable "sensitive_word" {
  description = "The word to redact in DLP"
  type        = string
  default     = "Juneau"
}

# Configuration for Model Armor Templates
variable "ma_templates" {
  description = "Map of template IDs to their configuration"
  type = map(object({
    enable_dlp = bool
  }))
  default = {
    "promo-req"  = { enable_dlp = false }
    "promo-resp" = { enable_dlp = true }
  }
}