import subprocess
from splunk_utils import wait_for_splunk

def start_splunk_container():
    print("Starting Splunk container using Docker Compose...")
    subprocess.run(["docker-compose", "-f", "./docker/docker-compose.yml", "up", "-d"], check=True)
    wait_for_splunk()

if __name__ == "__main__":
    start_splunk_container()