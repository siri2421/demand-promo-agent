# 1. Enable API
resource "google_project_service" "discovery_engine" {
  project            = var.project_id
  service            = "discoveryengine.googleapis.com"
  disable_on_destroy = false
}

# ---------------------------------------------------------
# FIX: Create a Placeholder Data Store
# (Required by the Chat Engine resource)
# ---------------------------------------------------------
resource "google_discovery_engine_data_store" "placeholder_store" {
  provider          = google-beta
  location          = "global"
  project           = var.project_id
  
  # Internal ID
  data_store_id     = "adk-promo-datastore-v20"
  display_name      = "Promo Agent Knowledge"
  
  # GENERIC config allows us to leave it mostly empty or add documents later
  industry_vertical = "GENERIC"
  
  # CONTENT_REQUIRED means "Unstructured" (PDFs/HTML), which is standard.
  # Even if we don't upload files yet, this container must exist.
  content_config    = "CONTENT_REQUIRED" 
  solution_types    = ["SOLUTION_TYPE_CHAT"]
  
  create_advanced_site_search = false

  depends_on = [google_project_service.discovery_engine]
}

# 3. Create the Agent (Chat Engine)
resource "google_discovery_engine_chat_engine" "gemini_agent" {
  provider          = google-beta
  
  engine_id         = "adk-promo-agent-v20"
  collection_id     = "default_collection"
  location          = "global"
  display_name      = "Promo Agent (ADK)"
  project           = var.project_id
  industry_vertical = "GENERIC"
  
  # ---------------------------------------------------------
  # FIX: Link the Data Store here
  # ---------------------------------------------------------
  data_store_ids    = [google_discovery_engine_data_store.placeholder_store.data_store_id]
  
  common_config {
    company_name = "Your Organization"
  }
  
  chat_engine_config {
    agent_creation_config {
      business              = "Retail Promotions"
      default_language_code = "en"
      time_zone              = "America/Los_Angeles"
    }
  }
}