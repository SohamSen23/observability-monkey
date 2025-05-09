import sys
import os
import streamlit as st
import atexit

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.start_dependencies import start_dependencies
from scripts.stop_dependencies import stop_splunk_container
from app.query_app import process_user_query

# Set page configuration (must be the first Streamlit command)
st.set_page_config(page_title="Observability Monkey Chat", layout="wide")

# Ensure stop_dependencies is called when the app stops
atexit.register(stop_splunk_container)

# Start dependencies only once
if "dependencies_started" not in st.session_state:
    with st.spinner("Starting dependencies... Please wait."):
        start_dependencies()
    st.session_state.dependencies_started = True

st.title("🧠 Observability Monkey Chat Assistant")

if "history" not in st.session_state:
    st.session_state.history = []

# Chat input
user_input = st.text_input("Enter your question:", key="input")

if st.button("Send") and user_input:
    # Clear previous chat history
    st.session_state.history = []

    # Append to chat history
    st.session_state.history.append(("user", user_input))

    # Call the backend logic directly
    response = process_user_query(user_input)
    st.session_state.history.append(("bot", response))

# Display chat history
for sender, message in st.session_state.history:
    align = "left" if sender == "bot" else "right"
    st.markdown(f"<div style='text-align: {align}; padding: 4px 0;'>{message}</div>", unsafe_allow_html=True)