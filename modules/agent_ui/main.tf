# 1. Artifact Registry for the UI
resource "google_artifact_registry_repository" "ui_repo" {
  location      = var.region
  repository_id = "agent-ui-repo"
  description   = "Docker repository for Enterprise UI"
  format        = "DOCKER"
  project       = var.project_id
}

locals {
  image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.ui_repo.repository_id}/agent-ui:latest"
}

# 2. Build & Push UI Image
resource "null_resource" "build_ui" {
  triggers = {
    app_hash = filemd5("${path.root}/ui/app.py")
    docker_hash = filemd5("${path.root}/ui/Dockerfile")
  }

  provisioner "local-exec" {
    command = "gcloud builds submit --project ${var.project_id} --region=${var.region} --tag ${local.image_name} ${path.root}/ui"
  }
}

# 3. Service Account for the UI
resource "google_service_account" "ui_sa" {
  account_id   = "agent-ui-sa"
  display_name = "Agent UI Service Account"
  project      = var.project_id
}

# 4. Grant Permissions (UI needs to call Vertex AI)
resource "google_project_iam_member" "ui_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.ui_sa.email}"
}

# 5. Deploy Cloud Run Service
resource "google_cloud_run_v2_service" "agent_ui" {
  name     = "enterprise-agent-portal"
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.ui_sa.email
    containers {
      image = local.image_name
      ports { container_port = 8080 }
      
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      # Pass the Reasoning Engine ID dynamically
      env {
        name  = "REASONING_ENGINE_ID"
        value = var.reasoning_engine_resource_name
      }
    }
  }
  depends_on = [null_resource.build_ui]
}

# 6. Make Public (For Demo) - In Prod, use IAP
/*resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.agent_ui.location
  project  = google_cloud_run_v2_service.agent_ui.project
  service  = google_cloud_run_v2_service.agent_ui.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}*/