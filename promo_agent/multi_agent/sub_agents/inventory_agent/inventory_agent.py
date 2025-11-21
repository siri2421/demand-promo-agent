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
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext
from google.cloud import storage

# --- Environment Setup ---
# Resolve path to root .env: current_file -> inventory_agent_dir -> sub_agents -> root
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

# Load variables
INVENTORY_BUCKET_NAME = os.getenv("INVENTORY_BUCKET_NAME")

if not INVENTORY_BUCKET_NAME:
    raise EnvironmentError("Missing INVENTORY_BUCKET_NAME in .env file.")

# Inventory Agent specific prompt
INVENTORY_SYSTEM_PROMPT = """
Gets store inventory as it relates to the local events and weather.

Local Events:

{local_events}

Weather:

{weather}

You have the following tools available to you:

def get_inventory(tool_context: ToolContext, city: str) -> dict:
    \"\"\"Gets the retailer's inventory from a Google Cloud Storage bucket\"\"\"

First, call the get_inventory tool to get a CSV file with the inventory.

Next, analyze the inventory in relation to the local events and weather to recommend an inventory item.
Add some flair to the chosen inventory item to make it relatable and more appealling.

Output only this:

**Inventory Agent:**

Recommended inventory item:

Name: [insert_name]
Description: [insert_description][newline][newline]

"""

def get_inventory(tool_context: ToolContext, city: str) -> dict:
    """Gets the retailer's inventory from a Google Cloud Storage bucket"""

    storage_client = storage.Client()
    bucket = storage_client.bucket(INVENTORY_BUCKET_NAME)
    blob = bucket.blob("inventory.csv")

    with blob.open("r") as f:
        inventory = f.read()

    print("Inventory:\n\n:" + inventory)

    if inventory:
        return {"Result": "Success", "inventory": inventory}
    else:
        return {"Result": "Fail", "inventory": ""}

inventory_agent = LlmAgent(
    name="InventoryAgent",
    model="gemini-2.5-flash",
    instruction=INVENTORY_SYSTEM_PROMPT,
    output_key="inventory",
    tools=[get_inventory]
)