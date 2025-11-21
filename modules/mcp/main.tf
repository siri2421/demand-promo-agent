# 1. Artifact Registry
resource "google_artifact_registry_repository" "mcp_repo" {
  location      = var.region
  repository_id = "remote-mcp-servers"
  description   = "Repository for remote MCP servers"
  format        = "DOCKER"
  project       = var.project_id
}

locals {
  image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.mcp_repo.repository_id}/${var.service_name}:latest"
}

# 2. Build & Push (Triggered by changes in source_dir)
resource "null_resource" "build_and_push_image" {
  triggers = {
    # path.root ensures we look for files relative to where you run 'terraform apply'
    dockerfile_hash = filemd5("${path.root}/${var.source_dir}/Dockerfile")
    server_hash     = filemd5("${path.root}/${var.source_dir}/server.py")
    toml_hash       = filemd5("${path.root}/${var.source_dir}/pyproject.toml")
    lock_hash       = filemd5("${path.root}/${var.source_dir}/uv.lock")
  }

  provisioner "local-exec" {
    # We pass the source directory to gcloud
    command = "gcloud builds submit --project ${var.project_id} --region=${var.region} --tag ${local.image_name} ${var.source_dir}"
  }

  depends_on = [google_artifact_registry_repository.mcp_repo]
}

# 3. Cloud Run Service
resource "google_cloud_run_v2_service" "mcp_service" {
  name     = var.service_name
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = local.image_name
      ports {
        container_port = 8080
      }
    #  env {
    #    name  = "PORT"
    #    value = "8080"
    #  }
    }
  }
    deletion_protection = false
  depends_on = [null_resource.build_and_push_image]
}