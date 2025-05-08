import subprocess

def stop_splunk_container():
    print("Stopping Splunk container using Docker Compose...")
    subprocess.run(["docker-compose", "-f", "./docker/docker-compose.yml", "down"], check=True)

if __name__ == "__main__":
    stop_splunk_container()