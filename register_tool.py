# register_tool.py
import os
import json
import sys
import requests
import google.auth
from google.auth.transport.requests import Request

# Config
PROJECT_ID = os.getenv("TF_PROJECT_ID")
LOCATION = os.getenv("TF_REGION")
AGENT_ID = os.getenv("AGENT_ID") # e.g., "adk-promo-agent-v17"

# ---------------------------------------------------------
# FIX: Target the Collection Level for Tool Creation
# ---------------------------------------------------------
API_ENDPOINT = "https://discoveryengine.googleapis.com/v1alpha"
COLLECTION_PATH = f"projects/{PROJECT_ID}/locations/global/collections/default_collection"

def get_auth_headers():
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    return {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": PROJECT_ID
    }

def get_latest_engine_schema():
    print("🔍 Auto-discovering latest Reasoning Engine...")
    from google.cloud import aiplatform
    try:
        from vertexai.preview import reasoning_engines
    except ImportError:
        from vertexai import reasoning_engines

    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    try:
        engines = reasoning_engines.ReasoningEngine.list(project=PROJECT_ID, location=LOCATION)
        if not engines: return None
        engines.sort(key=lambda x: x.update_time, reverse=True)
        latest = engines[0]
        print(f"✅ Found latest engine: {latest.resource_name}")
        if hasattr(latest, '_operation_schemas') and callable(latest._operation_schemas):
            return latest._operation_schemas()[0]
    except Exception as e:
        print(f"⚠️ Auto-discovery warning: {e}")
    return None

def get_adk_schema():
    # ... (Schema remains the same as previous) ...
    return {
        "openapi": "3.0.0",
        "info": { "title": "Promo Agent Action", "version": "1.0.0" },
        "paths": {
            "/query": {
                "post": {
                    "operationId": "query",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": { "prompt": { "type": "string" } }
                                }
                            }
                        }
                    },
                    "responses": { "200": { "description": "OK" } }
                }
            }
        }
    }

def register_integration():
    print(f"🚀 Starting Gemini Enterprise Registration (REST Mode)...")
    
    schema = get_latest_engine_schema()
    if not schema:
        print("ℹ️ Using Default ADK Schema.")
        schema = get_adk_schema()

    tool_id = "adk_promo_logic"
    
    # ---------------------------------------------------------
    # FIX: Create Tool at Collection Level
    # URL: .../collections/default_collection/tools?toolId=...
    # ---------------------------------------------------------
    create_url = f"{API_ENDPOINT}/{COLLECTION_PATH}/tools?toolId={tool_id}"
    
    payload = {
        "displayName": "ADK Promo Logic",
        "description": "Generates promotions based on weather and inventory.",
        "toolType": "OPEN_API",
        "openApiSpec": {
            "text": json.dumps(schema)
        }
    }

    print(f"📤 Registering Tool '{tool_id}' in default_collection...")
    try:
        response = requests.post(create_url, headers=get_auth_headers(), json=payload)
        
        if response.status_code == 200:
            print(f"✅ Tool Created: {response.json().get('name')}")
        elif response.status_code == 409:
            print("✅ Tool already exists (Skipping creation).")
        else:
            print(f"❌ Registration Failed: {response.status_code} - {response.text}")
            # Don't exit(1) so we can try linking even if creation failed
            
    except Exception as e:
        print(f"❌ Network Error: {e}")

    # ---------------------------------------------------------
    # OPTIONAL: Link Tool to Agent (Engine)
    # ---------------------------------------------------------
    # Note: In many Enterprise setups, simply existing in the collection 
    # allows the agent to select it if configured to use "All Tools".
    # Explicit linking via API is complex and often changes, 
    # so we stop here for the infrastructure setup.

if __name__ == "__main__":
    register_integration()