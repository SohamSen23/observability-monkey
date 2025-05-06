docs = {
    "doc1": """# PaymentService Errors
Common errors involve timeout during transaction processing. Solutions: Increase payment gateway retries.""",
    "doc2": """# InventoryService Issues
Stock mismatches occur due to concurrent updates. Solutions: Implement database locking or queuing."""
}

for doc_name, content in docs.items():
    with open(f"mock_server/confluence_docs/{doc_name}.txt", "w") as f:
        f.write(content.strip())
