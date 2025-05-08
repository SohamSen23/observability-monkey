import streamlit as st
import subprocess
import atexit

# Set page configuration (must be the first Streamlit command)
st.set_page_config(page_title="Observability Monkey Chat", layout="wide")

# Ensure stop_dependencies is called when the app stops
def stop_dependencies():
    subprocess.run(["python3", "scripts/stop_dependencies.py"], check=True)

atexit.register(stop_dependencies)

# Start dependencies only once
if "dependencies_started" not in st.session_state:
    with st.spinner("Starting dependencies... Please wait."):
        subprocess.run(["python3", "scripts/start_dependencies.py"], check=True)
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

    # Run your backend logic (subprocess call)
    result = subprocess.run(
        ["python3", "app/query_app.py", user_input],
        stdout=subprocess.PIPE,  # Capture the returned response
        stderr=None,  # Allow logs to print to the terminal
        text=True
    )
    response = result.stdout.strip()

    st.session_state.history.append(("bot", response))

# Display chat history
for sender, message in st.session_state.history:
    align = "left" if sender == "bot" else "right"
    st.markdown(f"<div style='text-align: {align}; padding: 4px 0;'>{message}</div>", unsafe_allow_html=True)