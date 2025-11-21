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
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES FIRST
# ---------------------------------------------------------------------------
# We do this immediately so that all subsequent imports (like sub-agents)
# have access to the variables in os.environ.
load_dotenv()

# Optional: specific check to ensure env loaded correctly
if not os.getenv("GOOGLE_CLOUD_PROJECT"):
    logging.warning("⚠️ GOOGLE_CLOUD_PROJECT not found. Did you create the .env file?")

# ---------------------------------------------------------------------------
# 2. IMPORT LIBRARIES & SUB-AGENTS
# ---------------------------------------------------------------------------
from google.adk.agents import LlmAgent

from .callbacks.modelarmor import model_armor_init_first_agent, model_armor_sanitize_request
from .sub_agents.promo_sequence_agent.promo_sequence_agent import promo_sequence_agent

import os


# MARKETING Agent specific prompt
GREETING_SYSTEM_PROMPT= """
You are a greeting agent. Your job is to take the most recent user prompt and decide if it is formed in the correct manner.

The prompt needs to be in this format: [US City] on [Day of Week]

US City: Can be any city in the US.
Day of Week: Cannot be the current day of the week, but can be any other day like Monday, Tuesday, etc.

IMPORTANT: Only focus on the last user prompt. If the prompt does not meet the required format, then output the following message:

"Hello! I'm a promotional marketing agent that monitors local conditions such as weather and events, creates product suggestions based on current inventory, and automatically generates highly relevant promotional visuals for in-store displays or digital marketing channels.

Please provide the US City and Day of Week for the promotion in this format: [US City] on [Day of Week]

Eg: Seattle on Friday  [newline][newline]"

Once you are satisfied the format of the prompt is correct, output "Thank you! Generating promotion...[newline][newline]" and run the promo_sequence_agent.

"""

root_agent = LlmAgent(
    name="GreetingAgent",
    model="gemini-2.5-flash",
    instruction=GREETING_SYSTEM_PROMPT,
    output_key="greeting",
    sub_agents=[promo_sequence_agent],
    before_agent_callback=model_armor_init_first_agent,
    before_model_callback=model_armor_sanitize_request  # call model armor on the first agent
)
