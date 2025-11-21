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
import logging
import httpx
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types
from typing import Optional
from google.cloud import secretmanager
import google_crc32c
from google.cloud import modelarmor_v1
import google.auth
import google.auth.transport.requests
import google.oauth2.id_token
from ...callbacks.mcp_token import MCPToolsetWithToolAccess
from ...callbacks.mcp_token import init_MCP_tools
from pathlib import Path
from dotenv import load_dotenv

# --- Logger Configuration ---
# This ensures logs show up with Severity levels in Google Cloud Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Environment Setup ---
# Resolve path to root .env: current_file -> weather_agent_dir -> sub_agents -> root
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

# Load variables
MCP_URL = os.getenv("MCP_URL")
MCP_AUD = os.getenv("MCP_AUD")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
MAPS_SECRET_ID = os.getenv("MAPS_SECRET_ID")
MAPS_SECRET_VERSION = os.getenv("MAPS_SECRET_VERSION")

# --- Log Environment Variables ---
logger.info("--- Environment Configuration Check ---")
logger.info(f"MCP_URL: {MCP_URL}")
logger.info(f"MCP_AUD: {MCP_AUD}")
logger.info(f"PROJECT_ID: {PROJECT_ID}")
logger.info(f"MAPS_SECRET_ID: {MAPS_SECRET_ID}")
logger.info(f"MAPS_SECRET_VERSION: {MAPS_SECRET_VERSION}")
logger.info("---------------------------------------")

if not all([MCP_URL, MCP_AUD, PROJECT_ID]):
    logger.error("Missing required environment variables in .env file.")
    raise EnvironmentError("Missing required environment variables (MCP_URL, MCP_AUD, or GOOGLE_CLOUD_PROJECT) in .env file.")

# Weather Agent specific prompt
WEATHER_SYSTEM_PROMPT = """
You are a weather agent tasked with proving local weather.

First, determine the latitude and longitude of the city provided using the get_coordinates_from_city tool.
Then, get the local weather in the city provided at the specific date using the get_weather tool.

You have the following tools available to you:

get_coordinates_from_city(city: str) -> dict:
    \"\"\"Gets the latitude and longitude for a given city.\"\"\"

def get_weather(latitude: float, longitude: float) -> str:
    \"\"\"
    Gets the weather forecast for a given latitude and longitude from the NWS API.

    Args:
        latitude: The latitude of the location.
        longitude: The longitude of the location.

    Returns:
        A string containing the weather details for multiple 12-hour periods, or an error message.
    \"\"\"

Output only the weather details in this format:

**Weather Agent:**

Weather for [insert_city] on [day_of_week]: 
High: [insert_high] 
Low: [insert_low] 
Wind: [insert_wind] 
Forecast: [insert_forecast][newline][newline]
"""

def get_tools():
    """Gets tools from the MCP Server."""
    # Get token from ADC
    # Ref: https://cloud.google.com/run/docs/authenticating/service-to-service
    #auth_req = google.auth.transport.requests.Request()
    
    #id_token = google.oauth2.id_token.fetch_id_token(auth_req, MCP_AUD)
    
    # Token issue ref: https://github.com/google/adk-python/issues/2221
    tools = MCPToolsetWithToolAccess(
        connection_params=StreamableHTTPConnectionParams(
            url=MCP_URL,
            #headers={'X-Serverless-Authorization': 'Bearer ' + id_token},
        ),
        tool_set_name="get_weather",
        errlog=None # Ref: https://github.com/google/adk-python/issues/1024#issuecomment-2943058567
    )
    logger.info("MCP Toolset created successfully.")
    return tools

def access_secret_version(project_id: str, secret_id: str, version_id: str) -> str:
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    #name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    # ---------------------------------------------------------
    # FIX: Handle Full Resource IDs from Terraform
    # ---------------------------------------------------------
    if secret_id.startswith("projects/"):
        # If Terraform passed the full path, use it directly.
        # This ignores 'project_id' and 'version_id' args, which is fine.
        name = secret_id
    else:
        # Otherwise, construct the path manually
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})

    # Verify payload checksum.
    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)
    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        logger.error("Secret Manager data corruption detected (CRC32C checksum failed).")
        return None
    
    return response.payload.data.decode("UTF-8") # return the secret

async def get_coordinates_from_city(tool_context: ToolContext, city: str) -> dict:
    """Gets the latitude and longitude for a given city."""

    # Call Secret Manager API for Google Maps API Key
    api_key = access_secret_version(PROJECT_ID, MAPS_SECRET_ID, MAPS_SECRET_VERSION)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": city, "key": api_key},
        )
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            return {"lat": location["lat"], "lng": location["lng"]}
        else:
            error_msg = f"Could not get coordinates for {city}. Status: {data['status']}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
def get_weather_agent():
    tools = get_tools()
    weather_agent = LlmAgent(
        name="WeatherAgent",
        model="gemini-2.5-flash",
        instruction=WEATHER_SYSTEM_PROMPT,
        output_key="weather",
        tools=[tools, get_coordinates_from_city],
        before_agent_callback=init_MCP_tools
    )  
    return weather_agent

weather_agent = get_weather_agent()