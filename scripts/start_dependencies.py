import sys
import os
import subprocess  # Missing import

# First add the scripts directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Then import from splunk_utils
from splunk_utils import wait_for_splunk

def start_dependencies():
    print("Starting Splunk container using Docker Compose...")
    subprocess.run(["docker-compose", "-f", "./docker/docker-compose.yml", "up", "-d"], check=True)
    wait_for_splunk()

    print("Generating fake Splunk logs...")
    subprocess.run(["python3", "scripts/generate_fake_splunk_logs.py"], check=True)

    print("Dependencies started successfully.")

if __name__ == "__main__":
    start_dependencies()