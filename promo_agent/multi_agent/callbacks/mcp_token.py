# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from google.adk.tools import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import Optional
import google.auth.transport.requests
import google.oauth2.id_token
import jwt
import time
import logging
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

# --- Environment Setup ---
# Resolve path to root .env: current_file -> callbacks_dir -> root
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

#Init cache for token refresh
toolset_cache = {}

# Load MCP_AUD from environment variables
MCP_AUD = os.getenv("MCP_AUD")

if not MCP_AUD:
    raise EnvironmentError("Missing MCP_AUD in .env file.")

# --- CONFIGURATION ---
# REPLACE WITH YOUR SERVICE ACCOUNT EMAIL
# e.g. "agent-runtime-sa@kar-ai1.iam.gserviceaccount.com"
SERVICE_ACCOUNT_EMAIL = "promo-agent-sa@kar-ai1.iam.gserviceaccount.com"

def init_MCP_tools(callback_context: CallbackContext) -> Optional[types.Content]:
    # Get or refresh the ADC token for MCP tool use
    tokenStatus = refreshToken(callback_context)
    print(f"Token Status: {tokenStatus}")
    return None

def get_id_token(audience):
    """
    Robust token fetcher:
    1. Tries standard metadata server (Cloud Run / Prod).
    2. Falls back to gcloud CLI with impersonation (Local Mac).
    """
    try:
        # 1. Try standard production method
        auth_req = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(auth_req, audience)
    except Exception as e:
        # 2. Fallback for Local Development
        print(f"⚠️ Standard Auth failed ({e}). Attempting gcloud fallback...")
        try:
            cmd = [
                "gcloud", "auth", "print-identity-token", 
                f"--audiences={audience}",
                f"--impersonate-service-account={SERVICE_ACCOUNT_EMAIL}"
            ]
            token = subprocess.check_output(cmd, text=True).strip()
            print("✅ gcloud token generated successfully.")
            return token
        except subprocess.CalledProcessError as gcloud_error:
             print(f"❌ gcloud Auth failed: {gcloud_error}")
             if gcloud_error.output: print(gcloud_error.output)
             raise gcloud_error

class MCPToolsetWithToolAccess(MCPToolset):
    """
    A subclass of MCPToolset that overrides the get_tools method
    to inject additional information.
    """

    def __init__(self, *args, tool_set_name: str, **kwargs):
        """Initializes MCPToolsetWithToolAccess with a new tool_set_name property."""
        super().__init__(*args, **kwargs)
        self._tool_set_name = tool_set_name

#Ref: https://github.com/nikhilpurwant/adk-samples/blob/prebuilt-agent-mcp-iam-authn/python/agents/mcp-iam-authn-agent/mcp_agent/agent.py
def refreshToken(callback_context: CallbackContext) -> Optional[str]:
    # CHANGE 1: Add Safety Check (prevents crash if agent has no tools)
    if not callback_context._invocation_context.agent.tools:
        return "No Tools"

    # CHANGE 2: DEFINE VARIABLE FIRST (Moved this line UP)
    # This must happen before we try to set headers in the bypass block below
    mcp_toolset = callback_context._invocation_context.agent.tools[0]
    
    # CHANGE 3: Localhost Bypass Logic
    # Now valid because mcp_toolset is defined above
    if MCP_AUD and ("localhost" in MCP_AUD or "127.0.0.1" in MCP_AUD):
        print("⚠️ Localhost detected: Skipping Google ID Token fetch.")
        
        # Safe header initialization
        if not hasattr(mcp_toolset._connection_params, 'headers') or mcp_toolset._connection_params.headers is None:
             mcp_toolset._connection_params.headers = {}
             
        mcp_toolset._connection_params.headers['X-Serverless-Authorization'] = 'Bearer local-dev-token'
        return "Done (Local)"
    
    if mcp_toolset._tool_set_name not in toolset_cache:
        toolset_cache[mcp_toolset._tool_set_name] = {}

    # The following means the token was never added to the toolset
    # The headers reset every time so cannot check for headers.
    if "token_expiration_time" not in toolset_cache[mcp_toolset._tool_set_name]:
        logging.info("Getting a token and adding to X-Serverless-Authorization header")
        mcp_toolset._connection_params.headers = {}
        id_token = get_id_token(MCP_AUD)
        mcp_toolset._connection_params.headers['X-Serverless-Authorization'] = f"Bearer {id_token}"
        logging.debug(f"id_token => {id_token}")
        decoded_payload = jwt.decode(id_token, options={"verify_signature": False})
        logging.debug("Decoded Token:", decoded_payload)            
        toolset_cache[mcp_toolset._tool_set_name]["prev_used_token"] = f"Bearer {id_token}"      
        toolset_cache[mcp_toolset._tool_set_name]["token_expiration_time"] = decoded_payload['exp']          
    else:
        # header is present but the token might be expired or about to expire within the next 5 minutes.
        time_after_threshold_minutes = int(time.time()) + (5*60)
        logging.debug(f"Token expires at {toolset_cache[mcp_toolset._tool_set_name]['token_expiration_time']}, Time after 5 minutes = {time_after_threshold_minutes}")
        # instead of decoding the token everytime - we are using the stored value to optimize
        if time_after_threshold_minutes >= toolset_cache[mcp_toolset._tool_set_name]['token_expiration_time']:
            logging.info(f"Getting a new token and updating the cache")
            id_token = get_id_token(MCP_AUD)
            mcp_toolset._connection_params.headers = {}
            mcp_toolset._connection_params.headers['X-Serverless-Authorization'] = f"Bearer {id_token}"   
            decoded_payload = jwt.decode(id_token, options={"verify_signature": False})
            logging.debug("Decoded Token:", decoded_payload)            
            toolset_cache[mcp_toolset._tool_set_name]["prev_used_token"] = f"Bearer {id_token}"      
            toolset_cache[mcp_toolset._tool_set_name]["token_expiration_time"] = decoded_payload['exp']  
        else:
            logging.error("Using a valid old token")
            mcp_toolset._connection_params.headers = {}
            mcp_toolset._connection_params.headers['X-Serverless-Authorization'] = toolset_cache[mcp_toolset._tool_set_name]["prev_used_token"]
    
    return "Done"
