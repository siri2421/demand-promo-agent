# deploy_to_vertex.py
import os
import sys
import logging
from typing import Dict

# -------------------------------------------------------------------------
# 1. Setup Paths
# -------------------------------------------------------------------------
sys.path.append(os.getcwd())

from google.cloud import aiplatform
from vertexai.preview import reasoning_engines

# -------------------------------------------------------------------------
# 2. Wrapper Class
# -------------------------------------------------------------------------
class AgentEngineWrapper:
    def __init__(self, config: Dict[str, str] = None):
        if config:
            for k, v in config.items():
                os.environ[k] = v
        
        # Lazy Import to ensure env vars are set first
        try:
            from promo_agent.multi_agent.agent import root_agent
            self.agent = root_agent
        except ImportError as e:
            print(f"❌ Remote Import Error: {e}")
            self.agent = None

    def query(self, prompt: str) -> str:
        if not self.agent:
            return "Error: Agent failed to initialize. Check logs."
        try:
            response = self.agent.query(prompt)
            if hasattr(response, "text"):
                return response.text
            return str(response)
        except Exception as e:
            return f"Error executing agent: {str(e)}"

# -------------------------------------------------------------------------
# 3. Helper: Parse .env
# -------------------------------------------------------------------------
def get_env_vars(env_path: str) -> Dict[str, str]:
    env_dict = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith('#') or not line.strip():
                    continue
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    env_dict[key] = value.strip('"').strip("'")
    return env_dict

# -------------------------------------------------------------------------
# 4. Deployment Logic
# -------------------------------------------------------------------------
def deploy():
    project_id = os.getenv("TF_PROJECT_ID")
    location = os.getenv("TF_REGION")
    staging_bucket = os.getenv("TF_STAGING_BUCKET")
    
    # We construct the SA email from the project ID (standard format)
    # Make sure this matches the SA you created in Terraform
    service_account_email = f"promo-agent-sa@{project_id}.iam.gserviceaccount.com"

    env_file_path = "./promo_agent/multi_agent/.env"
    
    print(f"🚀 Starting Vertex AI Deployment...")
    print(f"   Project: {project_id}")
    print(f"   Service Account: {service_account_email}")

    aiplatform.init(project=project_id, location=location, staging_bucket=staging_bucket)
    
    runtime_env = get_env_vars(env_file_path)
    configured_agent = AgentEngineWrapper(config=runtime_env)

    remote_agent = reasoning_engines.ReasoningEngine.create(
        configured_agent,
        # ---------------------------------------------------------
        # FIX: Added missing libraries (httpx, google-auth, etc.)
        # ---------------------------------------------------------
        requirements=[
            "google-cloud-aiplatform",
            "google-adk==1.14.1",
            "google-cloud-secret-manager",
            "google-cloud-modelarmor",
            "google-genai",
            "python-dotenv",
            "fastmcp",
            "pydantic-settings",
            "httpx",           # <--- Was missing
            "google-crc32c",   # <--- Was missing
            "google-auth",     # <--- Was missing
            "PyJWT",            # <--- Was missing
            "opentelemetry-sdk",
            "opentelemetry-exporter-gcp-trace"
        ],
        extra_packages=[
            "./promo_agent", 
        ],
        display_name="promo-multi-agent",
        description="ADK Multi-Agent System",
        )

    print(f"✅ Deployment Complete!")
    print(f"   Resource Name: {remote_agent.resource_name}")

if __name__ == "__main__":
    deploy()