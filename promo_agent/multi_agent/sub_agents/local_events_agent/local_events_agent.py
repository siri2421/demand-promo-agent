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

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from ..google_search_agent.google_search_agent import google_search_agent
from ...callbacks.modelarmor import model_armor_sanitize_response


# Local Events Agent specific prompt
LOCAL_EVENTS_SYSTEM_PROMPT = """
You are an agent that performs real-time web searches for local events.

Use the google_search_agent tool to get local events for a given city.

If no city is provided, assume that the city is Seattle.

Output only a list of up to 10 events in this format:

**Local Events Agent:**

Events for [city] on [day of week]:

- [event_name]: [description]
- [event_name]: [description]
...
[newline][newline]

"""

local_events_agent = LlmAgent(
    name="LocalEventsAgent",
    model="gemini-2.5-flash",
    instruction=LOCAL_EVENTS_SYSTEM_PROMPT,
    output_key="local_events",
    tools=[
        AgentTool(google_search_agent)
    ],
    after_model_callback=model_armor_sanitize_response  # call model armor
)