# 1. Create a Staging Bucket for Vertex AI Artifacts
resource "google_storage_bucket" "vertex_staging" {
  name          = "vertex-agent-staging-${var.project_id}"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

# 2. Trigger the Deployment Script
resource "null_resource" "deploy_to_reasoning_engine" {
  triggers = {
    script_hash = filemd5("${path.root}/deploy_adk_native.py")
    code_hash   = sha256(join("", [for f in fileset(path.root, "${var.agent_source_path}/**") : filemd5(f)]))
    env_signal  = var.dependency_signal
  }

  provisioner "local-exec" {
    environment = {
      TF_PROJECT_ID       = var.project_id
      TF_REGION           = var.region
      TF_STAGING_BUCKET   = google_storage_bucket.vertex_staging.url
    }

    command = <<EOT
      echo "🚀 Setting up Deployment Environment..."
      
      # 1. Create fresh virtual environment
      rm -rf .deploy_venv
      python3 -m venv .deploy_venv
      source .deploy_venv/bin/activate
      
      # 1. Generate Configuration
      # We overwrite the .env file to ensure these flags are present
      cat >> "${path.root}/promo_agent/multi_agent/.env" <<ENV_VARS
   
# --- Telemetry Configuration (Appended by Vertex Module) ---
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY="true"
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT="true"
ENV_VARS

      # 2. Install Dependencies
      # We separate the installs to ensure aiplatform gets the final say on version
      echo "📦 Installing Base Dependencies..."
      pip3 install --quiet cloudpickle google-adk python-dotenv
      
      echo "📦 Forcing Critical SDK Update..."
      # Force re-install of aiplatform to ensure we get 1.71.0+
      pip3 install --quiet --upgrade pip
      pip3 install --force-reinstall "google-cloud-aiplatform[agent_engines,adk]"
            
      # 3. DEBUG: Verify Version
      echo "🔍 Verifying SDK Version:"
      python3 -c "import google.cloud.aiplatform; print(f'   aiplatform version: {google.cloud.aiplatform.__version__}')"
      
      # We need ALL libraries that your agent imports at the top level
      pip3 install --upgrade \
        "google-cloud-aiplatform[agent_engines,adk]" \
        cloudpickle \
        google-adk \
        python-dotenv \
        google-cloud-modelarmor \
        google-cloud-secret-manager \
        fastmcp \
        google-genai
      # 4. Run Script
      echo "🚀 Executing Deployment..."
      python3 deploy_adk_native.py
    EOT
  }
}