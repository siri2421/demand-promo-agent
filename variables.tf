variable "region" {
  type        = string
  description = "the region where the resources live"
  default     = "us-central1"
}

variable "project_id" {
  description = "The GCP project ID."
  type        = string
  default     = "kar-ai1"
}
variable "staging_bucket_name" {
  description = "The name of the GCS bucket for staging."
  type        = string
  default     = "promo-agent-agentspace-bucket"
}

variable "app_name" {
  description = "The name of the application."
  type        = string
  default     = "promo-agent"
}

variable "gcp_service_list" {
  description = "List of GCP service APIs to enable"
  type        = list(string)
  default     = [
    # --- Core Infrastructure ---
    "compute.googleapis.com",              # Compute Engine
    "container.googleapis.com",            # Kubernetes Engine (GKE)
    "cloudresourcemanager.googleapis.com", # Resource Manager
    "iam.googleapis.com",                  # IAM
    "servicenetworking.googleapis.com",    # Private Service Connect / VPC Peering

    # --- Observability ---
    "logging.googleapis.com",              # Cloud Logging
    "monitoring.googleapis.com",           # Cloud Monitoring
    "telemetry.googleapis.com",            # Cloud Tracing 

    # --- DevOps & CI/CD (Added) ---
    "cloudbuild.googleapis.com",           # Cloud Build
    "artifactregistry.googleapis.com",     # Artifact Registry (Docker images)
    "secretmanager.googleapis.com",        # Secret Manager
    
    # --- Application Layer (Added) ---
    "run.googleapis.com",                  # Cloud Run
    
    # --- Data (Uncomment if needed) ---
    "bigquery.googleapis.com",           # BigQuery

    # --- AI Security ------
    "aiplatform.googleapis.com",         # Vertex AI
    "modelarmor.googleapis.com",          # Model Armor
    "dlp.googleapis.com",                 # DLP
    "discoveryengine.googleapis.com",     #Agent Builder
     "dialogflow.googleapis.com",       # Required for conversational capabilities

    # --- Google Maps Platform (NEW) ---
    "apikeys.googleapis.com",            # Required to create/manage API Keys
    "maps-backend.googleapis.com",       # Maps JavaScript API (Web maps)
    "geocoding-backend.googleapis.com",  # Geocoding API (Address <-> Lat/Long)
    "places-backend.googleapis.com",     # Places API (Search for businesses/points of interest)
    "directions-backend.googleapis.com", # Directions API (Routing)
    "distance-matrix-backend.googleapis.com" # Distance Matrix API
  ]
}

variable "latest_engine_id" {
  description = "The name of the application."
  type        = string
  default     = "projects/371273199457/locations/us-central1/reasoningEngines/3306754832257253376"
}
