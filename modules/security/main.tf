# ==============================================================================
# 1. DLP RESOURCES (Standard)
# ==============================================================================
resource "google_data_loss_prevention_inspect_template" "ma_inspect" {
  provider    = google-beta
  parent      = "projects/${var.project_id}/locations/${var.region}"
  template_id = "ma-inspect"
  
  inspect_config {
    custom_info_types {
      info_type { name = "SENSITIVE_WORD" }
      dictionary {
        word_list { words = [var.sensitive_word] }
      }
      likelihood = "LIKELY"
    }
  }
}

resource "google_data_loss_prevention_deidentify_template" "ma_deid" {
  provider    = google-beta
  parent      = "projects/${var.project_id}/locations/${var.region}"
  template_id = "ma-deid"

  deidentify_config {
    info_type_transformations {
      transformations {
        info_types { name = "SENSITIVE_WORD" }
        primitive_transformation {
          replace_config {
            new_value {
              string_value = "[REDACTED]"
            }
          }
        }
      }
    }
  }
}

# ==============================================================================
# 2. MODEL ARMOR RESOURCES (Simplified Loop)
# ==============================================================================

# Define the standard list of safety filters once
locals {
  safety_filters = [
    "SEXUALLY_EXPLICIT", 
    "HATE_SPEECH", 
    "HARASSMENT", 
    "DANGEROUS"
  ]
}

resource "google_model_armor_template" "templates" {
  # Loop through the map defined in variables.tf
  for_each = var.ma_templates

  provider    = google-beta
  project     = var.project_id
  location    = var.region
  template_id = each.key

  template_metadata {
    # Setting this to true is generally safer for templates 
    # to prevent errors if the API introduces new experimental fields
    ignore_partial_invocation_failures = false
  }

  filter_config {
    # A. Generate all 4 safety filters dynamically
    rai_settings {
      dynamic "rai_filters" {
        for_each = local.safety_filters
        content {
          filter_type      = rai_filters.value
          confidence_level = "MEDIUM_AND_ABOVE"
        }
      }
    }

    # B. Standard Settings
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "MEDIUM_AND_ABOVE"
    }
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }

    # C. Conditional DLP (Only if enable_dlp is true)
    dynamic "sdp_settings" {
      for_each = each.value.enable_dlp ? [1] : []
      content {
        advanced_config {
          inspect_template    = google_data_loss_prevention_inspect_template.ma_inspect.id
          deidentify_template = google_data_loss_prevention_deidentify_template.ma_deid.id
        }
      }
    }
  }
}

# ==============================================================================
# 3. LOGGING
# ==============================================================================
resource "google_project_iam_audit_config" "model_armor_logs" {
  project = var.project_id
  service = "modelarmor.googleapis.com"
  audit_log_config { log_type = "DATA_READ" }
  audit_log_config { log_type = "DATA_WRITE" }
  audit_log_config { log_type = "ADMIN_READ" }
}