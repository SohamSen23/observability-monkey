# observability-monkey

This is a lightweight RAG-based assistant for real-time monitoring systems.  
It fetches information from Splunk logs and Confluence documents to answer user queries.

## Features
- Keyword-based retrieval from mock Splunk logs and Confluence docs
- Uses GPT-3.5-Turbo to generate final answers
- Lightweight, easy to run locally

---

## Setup Instructions

### 1. Check if Python 3.13 is installed

```bash
python3 --version
```
If Python version is below 3.11, install Python 3.13:

#### Mac (using Homebrew)
```bash
brew install python@3.13
brew link python@3.13
```

#### Ubuntu
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev
```

#### Windows

Download the installer from: https://www.python.org/downloads/release/python-3130/
Install and add Python to PATH.

### 2. Create and activate virtual environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate venv
# Mac/Linux
source .venv/bin/activate

# Windows (Powershell)
.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat
```

### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Docker (Required for Splunk)
```bash
brew install docker-compose
```

### 5. Environment Variables
#### 1. Install Google Cloud SDK (Needed for fetching API keys)
```bash
brew install --cask google-cloud-sdk
```
#### 2. Use your TW mail id to authenticate:
```bash
gcloud auth application-default login
```

#### 3. Fetch Secrets
```bash
python fetch_secrets.py
```

```
## Running the Application Locally
### 1. Start the Streamlit Application
```bash
streamlit run streamlit_app.py
```
###  2. What Happens Under the Hood?
- The app automatically starts a Docker container for Splunk.
- Dummy logs are generated and loaded into the Splunk instance via the scripts/generate_fake_splunk_logs.py script.
- The Streamlit app runs on http://localhost:8501 and is ready to use.

### 3. Stopping the Application
When the app is stopped, a cleanup script (stop_dependencies.py) is executed to stop the Splunk container and clean up resources.

## Access Splunk on browser (Optional)
- Open your browser and go to `http://localhost:8000`
- Login with default credentials:
  - Username: `admin`
  - Password: `Dummy@splunk`
  - You can view the logs that were automatically generated

## Important Notes

This project uses mock Splunk logs and mock Confluence documents for testing.
This is a lightweight Retrieval-Augmented Generation (RAG) solution.
No vector database is used — simple file reading and matching is sufficient for the current use case.
If we want to extend it later for more scale or semantic search, we can add a vector DB like FAISS or Chroma.