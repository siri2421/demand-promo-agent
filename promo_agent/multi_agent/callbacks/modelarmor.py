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
from google.adk.tools import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types
from typing import Optional
from google.cloud import modelarmor_v1

# --- Environment Setup ---
# Resolve path to root .env: current_file -> callbacks_dir -> root
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

# Load variables
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
# NEW: Load Location
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
MA_ENDPOINT = os.getenv("MODEL_ARMOR_ENDPOINT")
MA_REQUEST_TEMPLATE = os.getenv("MA_REQUEST_TEMPLATE_ID")
MA_RESPONSE_TEMPLATE = os.getenv("MA_RESPONSE_TEMPLATE_ID")

if not all([PROJECT_ID, LOCATION, MA_ENDPOINT, MA_REQUEST_TEMPLATE, MA_RESPONSE_TEMPLATE]):
    raise EnvironmentError("Missing required Model Armor environment variables in .env file.")

def model_armor_init_first_agent(callback_context: CallbackContext) -> Optional[types.Content]:
    # Clear signals
    callback_context.state["request_stop_signal_found"] = False
    callback_context.state["response_stop_signal_found"] = False
    return None

def model_armor_sanitize_request(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM request or skips the call."""
    agent_name = callback_context.agent_name
    print(f"[Callback] Before model call for agent: {agent_name}")

    # Inspect the last user message in the request contents
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
         if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
    print(f"[Callback] Inspecting last user message: '{last_user_message}'")

    # Skip if last user message is empty
    if not last_user_message: 
        print("No message found - Skipping.")
        return None

    # Call Model Armor
    client = modelarmor_v1.ModelArmorClient(transport="rest", client_options = {"api_endpoint" : MA_ENDPOINT})

    user_prompt_data = modelarmor_v1.DataItem()
    user_prompt_data.text = last_user_message

    # UPDATED: Uses LOCATION variable
    request = modelarmor_v1.SanitizeUserPromptRequest(
        #name=f"projects/{PROJECT_ID}/locations/{LOCATION}/templates/{MA_REQUEST_TEMPLATE}",
        name=f"{MA_REQUEST_TEMPLATE}",
        user_prompt_data=user_prompt_data,
    )

    # Make the request
    response = client.sanitize_user_prompt(request=request)

    # Take action based on Model Armor's result
    if response.sanitization_result.filter_results["pi_and_jailbreak"].pi_and_jailbreak_filter_result.match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND:  # A PIJB match was found
        print("Query failed security check. Error.")
        # Set the STOP flag in shared state
        callback_context.state["request_stop_signal_found"] = True
        #pprint.pprint(response)

        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="LLM call was blocked by Model Armor due to user prompt content.")],
            )
        )
    else:
        print("Query passed security check. Sending prompt to LLM.")
        # Unset the STOP flag in shared state
        callback_context.state["request_stop_signal_found"] = False
        return None
    
def model_armor_sanitize_response(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM response or skips the call."""
    agent_name = callback_context.agent_name
    print(f"[Callback] After model call for agent: {agent_name}")

    # --- Inspection ---
    original_text = ""
    if llm_response.content and llm_response.content.parts:
        # Assuming simple text response for this example
        if llm_response.content.parts[0].text:
            original_text = llm_response.content.parts[0].text
            print(f"[Callback] Inspecting original response text: '{original_text[:100]}...'") # Log snippet
            # Call Model Armor
            client = modelarmor_v1.ModelArmorClient(transport="rest", client_options = {"api_endpoint" : MA_ENDPOINT})

            model_response_data = modelarmor_v1.DataItem()
            model_response_data.text = original_text

            # UPDATED: Uses LOCATION variable
            request = modelarmor_v1.SanitizeModelResponseRequest(
                #name=f"projects/{PROJECT_ID}/locations/{LOCATION}/templates/{MA_RESPONSE_TEMPLATE}",
                name=f"{MA_RESPONSE_TEMPLATE}",
                model_response_data=model_response_data,
            )

            # Sanitize the model response
            response = client.sanitize_model_response(request=request)

            # Take action based on Model Armor's result
            if response.sanitization_result.filter_results["sdp"].sdp_filter_result.deidentify_result.match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND:  # An SDP match was found
                print("Query failed security check. Error.")
                # Set the STOP flag in shared state
                callback_context.state["response_stop_signal_found"] = True

                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text="Agent sequence was blocked by Model Armor due to model response content." \
                        "\n\nRedacted text: \n\n" + response.sanitization_result.filter_results["sdp"].sdp_filter_result.deidentify_result.data.text)],
                    )
                )
            else:
                print("Query passed security check. Sending response to user.")
                return None
        else:
             print("[Callback] Inspected response: No text content found.")
             return None
    elif llm_response.error_message:
        print(f"[Callback] Inspected response: Contains error '{llm_response.error_message}'. No modification.")
        return None
    else:
        print("[Callback] Inspected response: Empty LlmResponse.")
        return None # Nothing to modify