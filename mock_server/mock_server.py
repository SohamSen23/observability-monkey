from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import os
import uvicorn

app = FastAPI()

# Serve mock Splunk logs
@app.get("/splunk/logs")
def get_splunk_logs():
    with open("mock_server/splunk_logs.txt", "r") as file:
        logs = file.read()
    return PlainTextResponse(logs)

# Serve mock Confluence documents
@app.get("/confluence/docs/{doc_name}")
def get_confluence_doc(doc_name: str):
    path = f"mock_server/confluence_docs/{doc_name}.txt"
    if os.path.exists(path):
        with open(path, "r") as file:
            return PlainTextResponse(file.read())
    else:
        return PlainTextResponse(f"No such document: {doc_name}", status_code=404)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
