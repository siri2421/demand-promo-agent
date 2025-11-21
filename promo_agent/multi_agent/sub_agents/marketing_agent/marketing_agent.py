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
from google.adk.tools import ToolContext
from google import genai
from google.genai import types
from google.genai.types import GenerateImagesConfig


async def generate_image(tool_context: ToolContext, prompt: str) -> dict:
    """Generates an image using Imagen."""
    client = genai.Client()

    output_file = "promo-image.png"

    image = client.models.generate_images(
        model="imagen-4.0-fast-generate-001",
        prompt=prompt,
        config=GenerateImagesConfig(
            image_size="2K",
        ),
    )

    generated_image = image.generated_images[0]

    # save image to local filesystem - TESTING ONLY - TO BE REMOVED
    #generated_image.image.save(output_file)

    artifact_part = types.Part(inline_data=types.Blob(data=generated_image.image.image_bytes, mime_type="image/png"))

    # Save artifact
    try:
        artifact_version = await tool_context.save_artifact( 
        filename=output_file, 
        artifact=artifact_part 
    )
    except Exception as e:
        error_message = f"Failed to save artifact: {e}"
        print(error_message)
        return {"status": "error", "error_message": error_message}

    return {
        "image_artifact": artifact_version,
    }


# MARKETING Agent specific prompt
MARKETING_SYSTEM_PROMPT = """
You are a marketing agent. Your goal is to create a compelling visual advertisement.
Based on the provided inventory details in {inventory}, generate a single, high-quality image that would be suitable for a promotional campaign.
Use the `generate_image` tool to create the visual. The description you provide to the tool should be a rich, detailed prompt that captures the essence of the product.
Include the product name and an advertising slogan prominently in the image itself.

Your response MUST look like this:

**Marketing Agent:**

Product: {Product Name}
Slogan: {The slogan used in the image}[newline][newline]
"""

marketing_agent = LlmAgent(
    name="MarketingAgent",
    model="gemini-2.5-flash",
    instruction=MARKETING_SYSTEM_PROMPT,
    output_key="promo",
    tools=[generate_image]
)