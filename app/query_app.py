import json
import logging
import os
import re
import sys
import time

import requests
import urllib3
import yaml
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from splunk_utils import SPLUNK_USERNAME, SPLUNK_PASSWORD

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Load configuration
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Read values from config.yaml
CONFLUENCE_BASE_URL = config.get("confluence_url", "https://default-confluence-url.com")
CONFLUENCE_EMAIL = config.get("confluence_email", "default-email@example.com")
SPLUNK_URL = config.get("splunk_url", "https://localhost:8089/services/search/jobs")

# Set up environment variables
load_dotenv()

# Access the OpenAI API key and Confluence token
api_key = os.getenv("OPENAI_API_KEY")
confluence_token = os.getenv("CONFLUENCE_API_TOKEN")

if not api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

if not confluence_token:
    raise ValueError("CONFLUENCE_API_TOKEN is not set in the environment variables.")

client = OpenAI(api_key=api_key)

def setup_splunk_session():
    session = requests.Session()
    session.auth = (SPLUNK_USERNAME, SPLUNK_PASSWORD)
    session.verify = False
    return session

def wait_for_splunk_job(session, search_url, sid):
    while True:
        status_url = f"{search_url}/{sid}"
        status_response = session.get(status_url, params={"output_mode": "json"})
        status = status_response.json()["entry"][0]["content"]
        if status.get("isDone", False):
            break
        time.sleep(1)

def extract_matching_logs_from_splunk(queryKeywords):
    if isinstance(queryKeywords, str):
        queryKeywords = json.loads(queryKeywords)

    search_terms = (
        queryKeywords.get("services", [])
        + queryKeywords.get("errors", [])
        + queryKeywords.get("correlation_id", [])
        + queryKeywords.get("endpoints", [])
    )

    session = setup_splunk_session()
    search_url = SPLUNK_URL
    matching_logs = []

    try:
        search_query = f'search sourcetype="splunk_logs" ({" AND ".join(search_terms)}) level=ERROR | sort -_time | head 1'
        logging.info('Splunk Search Query:', search_query)
        search_params = {"search": search_query, "output_mode": "json", "exec_mode": "normal"}
        job_response = session.post(search_url, data=search_params)
        job_response.raise_for_status()
        sid = job_response.json()["sid"]

        wait_for_splunk_job(session, search_url, sid)

        results_url = f"{search_url}/{sid}/results"
        results_response = session.get(results_url, params={"output_mode": "json", "count": 50})
        results = results_response.json()

        for result in results.get("results", []):
            if "_raw" in result:
                matching_logs.append(result["_raw"])

        extracted_fields = []
        for line in matching_logs:
            fields = {}
            fields["service"] = re.search(r'service=(\w+)', line).group(1) if re.search(r'service=(\w+)', line) else None
            fields["error_code"] = re.search(r'error_code=(\w+)', line).group(1) if re.search(r'error_code=(\w+)', line) else None
            extracted_fields.append(fields)

        return extracted_fields

    except requests.exceptions.RequestException as e:
        logging.error(f"Error querying Splunk: {e}")
        return []

def query_confluence_for_keywords(keywords):
    headers = {"Accept": "application/json"}
    auth = (CONFLUENCE_EMAIL, confluence_token)
    context_snippets = []

    for keyword in keywords:
        url = f"{CONFLUENCE_BASE_URL}/content/search?cql=text~\"{keyword}\"&expand=body.storage"
        response = requests.get(url, headers=headers, auth=auth)

        if response.status_code == 200:
            data = response.json()
            for page in data.get("results", []):
                title = page.get("title", "")
                body_html = page.get("body", {}).get("storage", {}).get("value", "")
                snippet = re.sub('<[^<]+?>', '', body_html).strip().replace("\n", " ")[:1000]
                context_snippets.append(f"{title}: {snippet}")
        else:
            logging.error(f"Error: Received status code {response.status_code} with response: {response.text}")

    return context_snippets

def generate_response(user_prompt, confluence_snippets):
    prompt_template = """
You are a helpful assistant that uses Confluence data to answer user questions.

Confluence Snippets:
{confluence_snippets}

User Query:
{user_prompt}

Based on the provided documentation context, identify relevant information that narrates clear steps for resolving the issue.
Present these steps in a simple and easy-to-follow manner, suitable for someone without technical expertise.
Ensure you share all steps mentioned in the Confluence snippets.
If no relevant information is found, respond with "I don't know" or "No relevant information available."
"""
    prompt = prompt_template.format(
        confluence_snippets="\n".join(confluence_snippets),
        user_prompt=user_prompt
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def extract_keywords_with_llm(user_query):
    prompt = f"""
You are a helpful assistant. Extract the following structured information from the user's query:

- service names (like checkout-service, mandate, etc.)
- error types or exceptions (like NullPointerException or HTTP errors only)
- correlation_id which contains the string 'err'
- relevant API endpoints or identifiers

Return your answer in this format:
{{
  "services": [...],
  "errors": [...],
  "correlation_id": [...],
  "endpoints": [...]
}}

User query: "{user_query}"
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def process_user_query(user_query):
    queryKeywords = extract_keywords_with_llm(user_query)
    logging.info('Extracted Query Keywords:', queryKeywords)
    splunk_keywords = extract_matching_logs_from_splunk(queryKeywords)
    logging.info('Extracted Splunk Keywords:', splunk_keywords)
    confluence_snippets = query_confluence_for_keywords(splunk_keywords)
    logging.info('Confluence Snippets:', confluence_snippets)
    return generate_response(user_query, confluence_snippets)

def main():
    if len(sys.argv) > 1:
        user_query = sys.argv[1]
        response = process_user_query(user_query)
        return response
    else:
        user_query = input("Enter your question: ")
        response = process_user_query(user_query)
        return response

if __name__ == "__main__":
    result = main()
    if result:
        print(result)  # Only print if running standalone