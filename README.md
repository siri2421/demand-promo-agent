## Demand and Promotion Agent
A promotional marketing agent built with the Google Agent Development Kit (ADK).
A multi-agentic system that monitors local conditions such as weather and events, creates product suggestions based on current inventory, and automatically generates highly relevant promotional visuals for in-store displays or digital marketing channels. Alongside this, it promotes GCP security concepts and provides integration examples.
  
The system is a multi-agent setup orchestrated by a main "GreetingAgent". This agent first validates user input, which must be a US city and a day of the week. Upon successful validation, it triggers a sequence of specialized
  
## Sub-agents:
### 1. Weather Agent
Fetches the weather forecast for the specified city and  day by calling a remote server.
 ### 2. Local Events Agent
 Searches for local events in the city using a   Google Search agent.
 ### 3. Inventory Agent
  Recommends a product from inventory stored in a Google Cloud Storage bucket, based on the weather and local events.
  ### 4. Marketing Agent
   Generates a promotional image for the recommended product using Google's Imagen text-to-image model.
  
The project also includes a FastAPI server that exposes a weather tool to the Weather Agent, which in turn retrieves data from the National Weather Service (NWS) API. The system utilizes Google Cloud services, including
Vertex AI for the language models, Cloud Storage for inventory data, and Secret Manager for API keys.
