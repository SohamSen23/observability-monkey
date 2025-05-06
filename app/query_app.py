import os
import re
import sys

import requests
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


def extract_matching_logs_from_splunk(keyword, time_range="24h"):
    """
    Query logs from Splunk containing the specified keyword.

    Args:
        keyword (str): Keyword to search for in logs
        time_range (str): Time range for the search (default: 24h)

    Returns:
        list: Unique keywords extracted from matching logs
    """
    print(f"Searching Splunk for logs containing '{keyword}'...")

    # Setup session with auth
    session = requests.Session()
    session.auth = (SPLUNK_USERNAME, SPLUNK_PASSWORD)
    session.verify = False

    # Create a search job
    search_query = f'search sourcetype="java_errors" "{keyword}" earliest=-{time_range}'
    search_url = "https://localhost:8089/services/search/jobs"

    search_params = {
        "search": search_query,
        "output_mode": "json",
        "exec_mode": "normal"
    }

    # Start the search
    try:
        job_response = session.post(search_url, data=search_params)
        job_response.raise_for_status()
        sid = job_response.json()["sid"]

        # Wait for search to complete
        is_done = False
        while not is_done:
            status_url = f"{search_url}/{sid}"
            status_response = session.get(
                status_url,
                params={"output_mode": "json"}
            )
            status = status_response.json()["entry"][0]["content"]
            is_done = status.get("isDone", False)
            if not is_done:
                import time
                time.sleep(1)

        # Get results
        results_url = f"{search_url}/{sid}/results"
        results_params = {
            "output_mode": "json",
            "count": 50  # Limit results
        }

        results_response = session.get(results_url, params=results_params)
        results = results_response.json()

        # Process results
        matching_logs = []
        for result in results.get("results", []):
            if "_raw" in result:
                matching_logs.append(result["_raw"])

        # Extract keywords from matching logs (keeping original logic)
        stopwords = {"at", "the", "to", "in", "all", "and", "due", "file", "while", "for", "from", "with", "large"}
        keywords = []
        for line in matching_logs:
            words = re.findall(r"[A-Za-z]+", line)  # Extract words
            filtered_words = [word for word in words if word.lower() not in stopwords and len(word) > 3]
            keywords.extend(filtered_words)

        # Return unique keywords
        return list(set(keywords))

    except requests.exceptions.RequestException as e:
        print(f"Error querying Splunk: {e}")
        return []

def query_confluence_for_keywords(keywords):
    headers = {
        "Accept": "application/json"
    }
    auth = (CONFLUENCE_EMAIL, confluence_token)

    context_snippets = []
    for keyword in keywords:
        url = f"{CONFLUENCE_BASE_URL}/content/search?cql=text~\"{keyword}\"&expand=body.storage"
        print("\nHitting Confluence ")
        response = requests.get(url, headers=headers, auth=auth)

        if response.status_code == 200:
            data = response.json()
            for page in data.get("results", []):
                title = page.get("title", "")
                body_html = page.get("body", {}).get("storage", {}).get("value", "")
                snippet = re.sub('<[^<]+?>', '', body_html)  # Strip HTML tags
                snippet = snippet.strip().replace("\n", " ")[:1000]  # Limit size
                context_snippets.append(f"{title}: {snippet}")
        else:
            print(f"Error: Received status code {response.status_code} with response: {response.text}")
    return context_snippets


def generate_response(user_prompt, context_snippets):
    # Define an elaborate prompt template
    prompt_template = """
You are a helpful assistant that uses Confluence data to answer user questions.

Context:
{context_snippets}

User Query:
{user_prompt}

Please provide a concise and accurate answer based on the context provided above. If you don't find relevant information, say "I don't know" or "No relevant information found."
"""

    # Format the prompt with placeholders
    prompt = prompt_template.format(
        context_snippets="\n".join(context_snippets),
        user_prompt=user_prompt
    )

    # Generate the response using the OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def main():
    # Predefined list of services
    SERVICES = ["parser", "mandate", "splunk", "confluence", "database", "nullpointerexception", "java", "error", "exception"]

    user_query = input("Enter your question: ")
    queryKeywords = next(
        (service for service in SERVICES if service in user_query.lower()),
        "unknown"
    )

    keywords = extract_matching_logs_from_splunk(queryKeywords)
    print(f"Extracted Keywords: {keywords}")

    confluence_snippets = query_confluence_for_keywords(keywords)
    print("\nConfluence Snippets:")
    for snippet in confluence_snippets:
        print(f"- {snippet[:100]}...")

    final_answer = generate_response(user_query, confluence_snippets)
    print("\n--- AI Response ---\n")
    print(final_answer)

if __name__ == "__main__":
    main()
