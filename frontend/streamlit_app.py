import sys
import os
import streamlit as st
import atexit
from PIL import Image

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.start_dependencies import start_dependencies
from scripts.stop_dependencies import stop_splunk_container
from app.query_app import process_user_query

# Set page configuration
st.set_page_config(page_title="Observability Monkey Chat", layout="wide")

# Ensure stop_dependencies is called when the app stops
atexit.register(stop_splunk_container)

# Start dependencies only once
if "dependencies_started" not in st.session_state:
    with st.spinner("Starting dependencies... Please wait."):
        start_dependencies()
    st.session_state.dependencies_started = True

# Load and display logo in the header
logo_path = "assets/logo.png"  # Adjust if needed
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image(logo, width=60)
    with col2:
        st.markdown("## Observability Monkey Chat Assistant")
else:
    st.markdown("## Observability Monkey Chat Assistant")  # Fallback if logo is missing

# Initialize chat history
if "history" not in st.session_state:
    st.session_state.history = []

# Display previous chat messages
for sender, message in st.session_state.history:
    with st.chat_message(sender):
        st.markdown(message)

# Chat input box (sends on Enter)
user_input = st.chat_input("Enter your question:")

if user_input:
    # Append user message
    st.session_state.history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get bot response
    response = process_user_query(user_input)
    st.session_state.history.append(("bot", response))
    with st.chat_message("bot"):
        st.markdown(response)
