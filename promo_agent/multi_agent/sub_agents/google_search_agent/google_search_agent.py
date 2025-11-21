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

from google.adk.agents import Agent
from google.adk.tools import google_search

# Google Search Agent specific prompt
GOOGLE_SEARCH_SYSTEM_PROMPT = """
Perform a Google search.
"""

google_search_agent = Agent(
    name="GoogleSearchAgentAgent",
    model="gemini-2.5-flash",
    instruction=GOOGLE_SEARCH_SYSTEM_PROMPT,
    tools=[google_search]
)