import json
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

CONFLUENCE_BASE_URL = "https://observability-monkey.atlassian.net/wiki/rest/api"
CONFLUENCE_EMAIL = "soham.sen@thoughtworks.com"


def setup_splunk_session():
    """Set up a Splunk session with authentication."""
    session = requests.Session()
    session.auth = (SPLUNK_USERNAME, SPLUNK_PASSWORD)
    session.verify = False
    return session


def wait_for_splunk_job(session, search_url, sid):
    """Wait for a Splunk search job to complete."""
    while True:
        status_url = f"{search_url}/{sid}"
        status_response = session.get(status_url, params={"output_mode": "json"})
        status = status_response.json()["entry"][0]["content"]
        if status.get("isDone", False):
            break
        time.sleep(1)


def extract_matching_logs_from_splunk(queryKeywords, time_range="24h"):
    """
    Query logs from Splunk using structured keywords.

    Args:
        queryKeywords (dict): Structured keywords (e.g., services, errors, etc.)
        time_range (str): Time range for the search (default: 24h)

    Returns:
        list: Unique keywords extracted from matching logs
    """
    print(f"Searching Splunk for logs using keywords: {queryKeywords}...")

    # Parse queryKeywords if it's a JSON string
    if isinstance(queryKeywords, str):
        queryKeywords = json.loads(queryKeywords)

    # Extract search terms from the structured keywords
    search_terms = (
            queryKeywords.get("services", [])
            + queryKeywords.get("errors", [])
            + queryKeywords.get("uuids", [])
            + queryKeywords.get("endpoints", [])
    )

    session = setup_splunk_session()
    search_url = SPLUNK_URL
    matching_logs = []

    try:
        for term in search_terms:
            # Create a search job for each term
            search_query = f'search sourcetype="java_errors" "{term}" earliest=-{time_range}'
            search_params = {"search": search_query, "output_mode": "json", "exec_mode": "normal"}
            job_response = session.post(search_url, data=search_params)
            job_response.raise_for_status()
            sid = job_response.json()["sid"]

            # Wait for search to complete
            wait_for_splunk_job(session, search_url, sid)

            # Get results
            results_url = f"{search_url}/{sid}/results"
            results_response = session.get(results_url, params={"output_mode": "json", "count": 50})
            results = results_response.json()

            # Process results
            for result in results.get("results", []):
                if "_raw" in result:
                    matching_logs.append(result["_raw"])

        # Extract keywords from matching logs
        stopwords = {"at", "the", "to", "in", "all", "and", "due", "file", "while", "for", "from", "with", "large"}
        keywords = [
            word
            for line in matching_logs
            for word in re.findall(r"[A-Za-z]+", line)
            if word.lower() not in stopwords and len(word) > 3
        ]

        return list(set(keywords))

    except requests.exceptions.RequestException as e:
        print(f"Error querying Splunk: {e}")
        return []


def query_confluence_for_keywords(keywords):
    """
    Query Confluence for pages matching the given keywords.

    Args:
        keywords (list): List of keywords to search for.

    Returns:
        list: Context snippets from Confluence pages.
    """
    headers = {"Accept": "application/json"}
    auth = (CONFLUENCE_EMAIL, confluence_token)
    context_snippets = []

    for keyword in keywords:
        url = f"{CONFLUENCE_BASE_URL}/content/search?cql=text~\"{keyword}\"&expand=body.storage"
        print("\nHitting Confluence")
        response = requests.get(url, headers=headers, auth=auth)

        if response.status_code == 200:
            data = response.json()
            for page in data.get("results", []):
                title = page.get("title", "")
                body_html = page.get("body", {}).get("storage", {}).get("value", "")
                snippet = re.sub('<[^<]+?>', '', body_html).strip().replace("\n", " ")[:1000]
                context_snippets.append(f"{title}: {snippet}")
        else:
            print(f"Error: Received status code {response.status_code} with response: {response.text}")

    return context_snippets


def generate_response(user_prompt, context_snippets):
    """
    Generate a response using OpenAI based on the user prompt and context snippets.

    Args:
        user_prompt (str): The user's query.
        context_snippets (list): Context snippets from Confluence.

    Returns:
        str: AI-generated response.
    """
    prompt_template = """
You are a helpful assistant that uses Confluence data to answer user questions.

Context:
{context_snippets}

User Query:
{user_prompt}

Please provide a concise and accurate answer based on the context provided above. If you don't find relevant information, say "I don't know" or "No relevant information found."
"""
    prompt = prompt_template.format(
        context_snippets="\n".join(context_snippets),
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
    """
    Extract structured information from the user's query using OpenAI.

    Args:
        user_query (str): The user's query.

    Returns:
        dict: Structured information (services, errors, etc.).
    """
    prompt = f"""
You are a helpful assistant. Extract the following structured information from the user's query:

- service names (like checkout-service, mandate, etc.)
- error types or exceptions (like NullPointerException, 500 error, etc.)
- UUIDs or event IDs
- relevant API endpoints or identifiers

Return your answer in this format:
{{
  "services": [...],
  "errors": [...],
  "uuids": [...],
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


def main():
    user_query = input("Enter your question: ")
    queryKeywords = extract_keywords_with_llm(user_query)

    splunk_keywords = extract_matching_logs_from_splunk(queryKeywords)
    print("\nMatching Logs from Splunk:\n", splunk_keywords)

    confluence_snippets = query_confluence_for_keywords(splunk_keywords)
    print("\nConfluence Snippets:")
    for snippet in confluence_snippets:
        print(f"- {snippet[:100]}...")

    final_answer = generate_response(user_query, confluence_snippets)
    print("\n--- AI Response ---\n")
    print(final_answer)


if __name__ == "__main__":
    main()