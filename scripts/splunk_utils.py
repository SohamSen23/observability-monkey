import requests
import time
import subprocess
import urllib3
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Splunk credentials and settings
SPLUNK_USERNAME = "admin"
SPLUNK_PASSWORD = "Dummy@splunk"
SPLUNK_URL = "https://localhost:8089"  # Changed to HTTPS
HEC_URL = "https://localhost:8088/services/collector"  # Changed to HTTPS
HEC_API_URL = f"{SPLUNK_URL}/services/data/inputs/http"
TOKEN_NAME = "observability-monkey"
SPLUNK_HEALTH_ENDPOINT = f"{SPLUNK_URL}/services/server/info"


def start_splunk_container():
    print("Starting Splunk container using Docker Compose...")
    subprocess.run(["docker-compose", "-f", "./docker/docker-compose.yml", "up", "-d"], check=True)
    wait_for_splunk()


def wait_for_splunk(timeout=120, interval=5):
    print("Waiting for Splunk to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                SPLUNK_HEALTH_ENDPOINT,
                auth=HTTPBasicAuth(SPLUNK_USERNAME, SPLUNK_PASSWORD),
                verify=False,
                timeout=10
            )
            if response.status_code == 200 and "<feed" in response.text:
                print("✅ Splunk is ready!")
                return
            else:
                print(f"Attempt: Unexpected response, status code = {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt: Request failed: {e}")

        time.sleep(interval)

    raise Exception("Splunk did not become ready in time.")


def create_splunk_token():
    print("Creating Splunk token (using basic auth)...")

    session = requests.Session()
    session.auth = (SPLUNK_USERNAME, SPLUNK_PASSWORD)
    session.verify = False

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # First check if token already exists
    try:
        print("Checking for existing token...")
        list_resp = session.get(
            HEC_API_URL,
            params={"output_mode": "json"},
            timeout=30
        )
        list_resp.raise_for_status()

        tokens = list_resp.json().get("entry", [])
        print(f"Found {len(tokens)} tokens")

        # Debug token names
        token_names = [t["name"] for t in tokens]
        print(f"Existing token names: {token_names}")

        # Check for exact match or token with http:// prefix
        existing_token = next((t for t in tokens if t["name"] == TOKEN_NAME or t["name"].endswith(TOKEN_NAME)), None)

        if existing_token:
            print(f"Token for {TOKEN_NAME} found, using existing token")
            return existing_token["content"]["token"]

        # Enable HEC if needed
        print("Enabling HEC...")
        try:
            enable_resp = session.post(
                f"{HEC_API_URL}/http",
                data={"disabled": "0", "output_mode": "json"},
                headers=headers,
                timeout=30
            )
            enable_resp.raise_for_status()
            print("HEC enabled successfully")
        except requests.exceptions.HTTPError as e:
            print(f"Error enabling HEC: {e}. Continuing anyway...")

        # Create new token with better error handling
        print(f"Creating new token: {TOKEN_NAME}")
        token_data = {
            "name": TOKEN_NAME,
            "index": "main",
            "output_mode": "json"
        }

        try:
            token_resp = session.post(
                HEC_API_URL,
                data=token_data,
                headers=headers,
                timeout=30
            )
            token_resp.raise_for_status()

            # Extract token from creation response
            token_json = token_resp.json()
            if "entry" in token_json and len(token_json["entry"]) > 0:
                new_token = token_json["entry"][0]["content"]["token"]
                print(f"Token created successfully")
                return new_token
        except requests.exceptions.HTTPError as e:
            # Handle 409 Conflict specifically - token likely exists
            if e.response.status_code == 409:
                print("Token already exists. Fetching it...")
            else:
                raise e

        # Fetch all tokens again to find our token
        print("Retrieving token from list...")
        time.sleep(2)  # Give Splunk time to update
        list_resp = session.get(
            HEC_API_URL,
            params={"output_mode": "json"},
            timeout=30
        )
        list_resp.raise_for_status()

        tokens = list_resp.json().get("entry", [])
        print(f"Retrieved {len(tokens)} tokens")
        token_names = [t["name"] for t in tokens]
        print(f"Token names: {token_names}")

        # Handle name with or without http:// prefix
        created_token = next((t["content"]["token"] for t in tokens if t["name"] == TOKEN_NAME or t["name"].endswith(TOKEN_NAME)), None)

        if created_token:
            print(f"Token retrieved successfully")
            return created_token

        raise Exception("Token not found after creation. Check Splunk logs.")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response content: {e.response.text}")
        raise Exception(f"Failed to create Splunk token: {e}")