import streamlit as st
from google.cloud import aiplatform
from vertexai.preview import reasoning_engines
import os

# Enterprise Branding
st.set_page_config(page_title="Enterprise Agent Portal", page_icon="⚡")
st.title("⚡ ADK Multi-Agent: Enterprise Edition")

# 1. Load Config from Environment (Injected by Terraform)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
ENGINE_ID = os.getenv("REASONING_ENGINE_ID")

if not ENGINE_ID:
    st.error("❌ Configuration Error: REASONING_ENGINE_ID is missing.")
    st.stop()

# 2. Initialize Chat Session
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle User Input
if prompt := st.chat_input("Ask the agent (e.g., 'Seattle on Friday')..."):
    # Show User Message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Call Vertex AI Reasoning Engine
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⏳ *Thinking...*")
        
        try:
            # Initialize Connection
            aiplatform.init(project=PROJECT_ID, location=LOCATION)
            # Connect to the Remote Agent
            remote_agent = reasoning_engines.ReasoningEngine(ENGINE_ID)
            
            # Query
            response = remote_agent.query(prompt=prompt)
            
            # Display Result
            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            message_placeholder.error(f"🔌 Connection Failed: {str(e)}")