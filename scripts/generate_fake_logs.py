logs = """
2025-04-28 10:10:11 ERROR PaymentService - Transaction timeout.
2025-04-28 10:15:22 INFO AuthService - Login successful.
2025-04-28 10:17:03 ERROR InventoryService - Item stock mismatch.
"""

with open("mock_server/splunk_logs.txt", "w") as file:
    file.write(logs.strip())
