# 1. Create the Restricted API Key
resource "google_apikeys_key" "maps_frontend_key" {
  name         = "maps-frontend-key"
  display_name = "Maps API Key - Frontend"
  project      = var.project_id

  restrictions {
    # Browser restrictions (Adjust domain as needed)
    browser_key_restrictions {
      allowed_referrers = ["*"] # TODO: Lock this down to your specific domain
    }

    # Limit scope to Maps APIs only
    api_targets { service = "maps-backend.googleapis.com" }
    api_targets { service = "places-backend.googleapis.com" }
    api_targets { service = "geocoding-backend.googleapis.com" }
    api_targets { service = "directions-backend.googleapis.com" }
  }
}

# 2. Create the Secret Container
resource "google_secret_manager_secret" "maps_key_secret" {
  secret_id = "maps-api-key"
  project   = var.project_id

  replication {
    auto {} # Automatically replicates to the best locations
  }
}

# 3. Store the API Key Value as a Secret Version
resource "google_secret_manager_secret_version" "maps_key_version" {
  secret = google_secret_manager_secret.maps_key_secret.id
  
  # We pull the raw key string from the resource above
  secret_data = google_apikeys_key.maps_frontend_key.key_string
}

# 4. Grant Access to the Service Account
resource "google_secret_manager_secret_iam_member" "sa_access" {
  secret_id = google_secret_manager_secret.maps_key_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.app_service_account_email}"
}