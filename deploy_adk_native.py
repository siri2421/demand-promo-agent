# deploy_adk_native.py
import os
import sys
import vertexai
#from vertexai.preview import agent_engines # Note: Might be in 'preview' depending on SDK version
from typing import Dict
try:
    from vertexai import agent_engines
    print("✅ Loaded 'agent_engines' from Stable namespace.")
except ImportError:
    try:
        from vertexai.preview import agent_engines
        print("⚠️ Loaded 'agent_engines' from Preview namespace.")
    except ImportError:
        print("❌ Could not find 'agent_engines' in vertexai or vertexai.preview.")
        # Debugging aid for logs
        import vertexai.preview
        print(f"Contents of vertexai.preview: {dir(vertexai.preview)}")
        sys.exit(1)
# -------------------------------------------------------------------------
# 1. Setup Paths to find your Agent Code
# -------------------------------------------------------------------------
# We need to look inside 'promo_agent/multi_agent'
sys.path.append(os.getcwd())
try:
    from promo_agent.multi_agent.agent import root_agent
except ImportError as e:
    print(f"❌ Error importing root_agent: {e}")
    sys.exit(1)

# -------------------------------------------------------------------------
# 2. Helper: Load Runtime Config from .env
#    (We need to pass MCP_URL etc. to the remote container)
# -------------------------------------------------------------------------
def get_runtime_env_vars(env_path: str) -> Dict[str, str]:
    env_dict = {}
    
    # List of variables that Vertex AI injects automatically.
    # We MUST NOT send these in the env_vars dict, or deployment will fail.
    RESERVED_KEYS = {
        "GOOGLE_CLOUD_PROJECT", 
        "GOOGLE_CLOUD_LOCATION"
    }

    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith('#') or not line.strip(): continue
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    key = key.strip()
                    
                    # SKIP reserved keys
                    if key in RESERVED_KEYS:
                        print(f"ℹ️ Skipping reserved variable: {key}")
                        continue
                        
                    env_dict[key] = value.strip('"').strip("'")
    return env_dict

# -------------------------------------------------------------------------
# 3. Deployment Logic
# -------------------------------------------------------------------------
def deploy():
    # --- Get Infrastructure Config from Terraform Environment ---
    PROJECT_ID = os.getenv("TF_PROJECT_ID")
    LOCATION = os.getenv("TF_REGION")
    STAGING_BUCKET = os.getenv("TF_STAGING_BUCKET")
    SERVICE_ACCOUNT = f"promo-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com"
    
    print(f"🚀 Starting Native ADK Deployment...")
    print(f"   Project: {PROJECT_ID}")
    print(f"   SA: {SERVICE_ACCOUNT}")

    # Initialize Vertex AI SDK
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    # --- Prepare Runtime Environment ---
    # Load the .env file Terraform generated so the agent has its config
    env_file_path = "./promo_agent/multi_agent/.env"
    runtime_env = get_runtime_env_vars(env_file_path)

    # --- Wrap the agent in an AdkApp object ---
    # This replaces the manual 'AgentEngineWrapper' class
    app = agent_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True, # Native Telemetry!
    )

    # --- Deploy ---
    remote_app = agent_engines.create(
        agent_engine=app,
        display_name="promo-multi-agent-native",
        # We instruct it to pip install these packages remotely
        requirements=[
            "google-cloud-aiplatform[agent_engines,adk]>=1.70.0", # Ensure remote has agent support
            "google-adk>=1.14.1",
            "google-cloud-secret-manager",
            "google-cloud-modelarmor",
            "google-genai",
            "python-dotenv",
            "fastmcp",
            "pydantic-settings",
            "httpx",
            "google-crc32c",
            "google-auth",
            "PyJWT",
            "opentelemetry-sdk",
            "opentelemetry-exporter-gcp-trace"
        ],
        # Upload the code
        extra_packages=["./promo_agent"], 
        service_account=SERVICE_ACCOUNT,
        # Pass the MCP_URL and keys to the container
        env_vars=runtime_env 
    )

    print(f"✅ Deployment Complete!")
    print(f"   Resource Name: {remote_app.resource_name}")

if __name__ == "__main__":
    deploy()