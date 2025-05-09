# fetch_secrets.py

import os
from google.cloud import secretmanager
from dotenv import load_dotenv, dotenv_values

# Set your GCP project ID here or use an environment variable
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "observability-monkey-f54e")

# List of secret names to fetch from GCP Secret Manager
SECRETS = [
    "OPENAI_API_KEY",
    "CONFLUENCE_API_TOKEN"
]

# Path to your local .env file
ENV_PATH = ".env"


def fetch_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def write_to_env_file(key, value):
    # Load existing .env variables
    existing_env = dotenv_values(ENV_PATH)

    # Check if the key already exists
    if key in existing_env:
        print(f"🔄 {key} already exists in .env. Skipping.")
    else:
        with open(ENV_PATH, "a") as env_file:
            env_file.write(f"{key}={value}\n")
        print(f"✅ {key} fetched and written to .env")


def main():
    # Ensure .env exists
    open(ENV_PATH, 'a').close()
    load_dotenv(ENV_PATH)

    for secret in SECRETS:
        try:
            value = fetch_secret(secret)
            write_to_env_file(secret, value)
        except Exception as e:
            print(f"❌ Failed to fetch {secret}: {e}")


if __name__ == "__main__":
    main()