import requests
import random
import json
import time
import re  # Fixed missing import
from splunk_utils import create_splunk_token
from start_splunk_container import start_splunk_container

# Other existing code in splunk_utils.py


def generate_fake_logs(splunk_token, splunk_url):
    headers = {
        'Authorization': f'Splunk {splunk_token}',
        'Content-Type': 'application/json'
    }

    splunk_logs = [
        [
            """level=INFO service=parser host=parser-01 environment=production event="Started processing file orders_2025_05_06.csv" status=started file=orders_2025_05_06.csv correlation_id=abc001""",
            """level=INFO service=parser host=parser-01 environment=production event="File header validated successfully" file=orders_2025_05_06.csv header_row=true correlation_id=abc001""",
            """level=INFO service=parser host=parser-01 environment=production event="Parsed 500 records" file=orders_2025_05_06.csv records_processed=500 correlation_id=abc001""",
            """level=INFO service=parser host=parser-01 environment=production event="Completed parsing file" file=orders_2025_05_06.csv duration_ms=642 total_records=1045 status=success correlation_id=abc001""",
            """level=INFO service=parser host=parser-02 environment=production event="Started processing file customers_2025_05_06.json" status=started file=customers_2025_05_06.json correlation_id=abc002""",
            """level=INFO service=parser host=parser-02 environment=production event="Detected 3 customer segments in file" segments_detected=3 file=customers_2025_05_06.json correlation_id=abc002""",
            """level=INFO service=parser host=parser-02 environment=production event="Completed parsing file" file=customers_2025_05_06.json duration_ms=480 total_records=900 status=success correlation_id=abc002""",
            """level=INFO service=parser host=parser-03 environment=production event="Parser health check passed" uptime_minutes=1247 correlation_id=sys001""",
            """level=INFO service=parser host=parser-01 environment=production event="No files to process in incoming directory" directory=/data/incoming correlation_id=abc003""",
            """level=INFO service=parser host=parser-01 environment=production event="Scheduled parser job executed successfully" job_name=daily_parser_sync job_id=job123 duration_ms=122 correlation_id=sched001""",
            """level=WARN service=parser host=parser-01 environment=production event="File contains unexpected column: 'discount_rate'" file=orders_2025_05_06.csv column=discount_rate correlation_id=abc001""",
            """level=WARN service=parser host=parser-02 environment=production event="Missing optional field 'customer_age' in 132 records" file=customers_2025_05_06.json missing_field=customer_age correlation_id=abc002""",
            """level=WARN service=parser host=parser-03 environment=production event="Parser memory usage exceeded threshold: 82%" memory_usage=82% threshold=80% correlation_id=sys002""",
            """level=WARN service=parser host=parser-01 environment=production event="File size unusually large: 250MB" file=large_file.csv size_mb=250 correlation_id=abc004""",
            """level=WARN service=parser host=parser-02 environment=production event="Retrying fetch due to slow network response" retry_count=1 file=transactions_2025_05_06.csv correlation_id=abc005""",
            """level=WARN service=parser host=parser-01 environment=production event="High latency observed while writing to database" latency_ms=512 db_endpoint=db-prod-1 correlation_id=abc006""",
            """level=WARN service=parser host=parser-03 environment=production event="Timezone mismatch detected in 34 rows" file=events_2025_05_06.csv correlation_id=abc007""",
            """level=WARN service=parser host=parser-02 environment=production event="Deprecated format detected in column 'user_status'" column=user_status file=legacy_users.csv correlation_id=abc008""",
            """level=WARN service=parser host=parser-01 environment=production event="Retry limit approaching for file download" retries_left=1 url=https://fileserver/input_1.csv correlation_id=abc009""",
            """level=WARN service=parser host=parser-03 environment=production event="Skipped parsing of empty file" file=empty_file.csv correlation_id=abc010""",
            """level=ERROR service=parser host=parser-02 environment=production event="Parsing failed due to malformed JSON in line 482 of file 'invoices_2025_05_06.json'. Expected closing bracket but found comma." file=invoices_2025_05_06.json line_number=482 error_code=JSON_SYNTAX_ERROR correlation_id=err001""",
            """level=ERROR service=parser host=parser-01 environment=production event="Timeout while accessing remote file location" file_url=https://fileserver/remote.csv timeout_ms=10000 correlation_id=err002 error_code=FILE_FETCH_TIMEOUT""",
            """level=ERROR service=parser host=parser-03 environment=production event="NullPointerException while processing record batch" exception=NullPointerException file=records_batch.csv correlation_id=err003""",
            """level=ERROR service=parser host=parser-02 environment=production event="Database write failed due to constraint violation on 'order_id'" constraint=unique_order_id file=orders_2025_05_06.csv correlation_id=err004""",
            """level=ERROR service=parser host=parser-01 environment=production event="Job crashed unexpectedly. Stacktrace captured." job_name=daily_parser_sync error_code=UNCAUGHT_EXCEPTION correlation_id=err005""",
            """level=ERROR service=parser host=parser-01 environment=production event="DB Connection timed out" job_name=daily_parser_sync error_code=DB_CONNECTION_TIMEOUT correlation_id=err006""",
            """level=INFO service=MandateService host=mandate-01 environment=production event="Started processing mandate file mandates_2025_05_06.csv" status=started file=mandates_2025_05_06.csv correlation_id=mand001""",
            """level=INFO service=MandateService host=mandate-01 environment=production event="File header validated successfully" file=mandates_2025_05_06.csv header_row=true correlation_id=mand001""",
            """level=INFO service=MandateService host=mandate-01 environment=production event="Parsed 1200 records" file=mandates_2025_05_06.csv records_processed=1200 correlation_id=mand001""",
            """level=INFO service=MandateService host=mandate-01 environment=production event="Completed parsing mandate file" file=mandates_2025_05_06.csv duration_ms=753 total_records=1500 status=success correlation_id=mand001""",
            """level=INFO service=MandateService host=mandate-02 environment=production event="Started processing mandate file mandates_2025_05_06.xml" status=started file=mandates_2025_05_06.xml correlation_id=mand002""",
            """level=INFO service=MandateService host=mandate-03 environment=production event="Scheduled mandate file sync executed successfully" job_name=mandate_file_sync job_id=job456 duration_ms=320 correlation_id=sched002""",
            """level=WARN service=MandateService host=mandate-01 environment=production event="File contains unexpected column: 'bank_code'" file=mandates_2025_05_06.csv column=bank_code correlation_id=mand001""",
            """level=ERROR service=MandateService host=mandate-02 environment=production event="Parsing failed due to invalid XML format in line 312 of file 'mandates_2025_05_06.xml'. Expected closing tag but found '<'." file=mandates_2025_05_06.xml line_number=312 error_code=XML_SYNTAX_ERROR correlation_id=err001""",
            """level=ERROR service=MandateService host=mandate-03 environment=production event="Database write failed due to constraint violation on 'mandate_id'" constraint=unique_mandate_id file=mandates_2025_05_06.csv correlation_id=err002"""
        ]
    ]
    for i in range(1000):
        raw_log = random.choice(random.choice(splunk_logs))
        level_match = re.search(r'level=(\w+)', raw_log)
        log_level = level_match.group(1) if level_match else "UNKNOWN"

        log_event = {
            "event": {
                "level": log_level,
                "error": raw_log,
                "logger": f"com.example.module{random.randint(1, 5)}",
                "thread": f"Thread-{random.randint(1, 20)}",
                "timestamp": int(time.time())
            },
            "sourcetype": "splunk_logs"
        }

        try:
            response = requests.post(
                splunk_url,
                headers=headers,
                data=json.dumps(log_event),
                verify=False,
                timeout=10
            )

            if response.status_code != 200:
                print(f"Failed to send event {i}: {response.text}")
            else:
                print(f"[{i + 1}/1000] Event sent")

        except requests.exceptions.RequestException as e:
            print(f"Failed to send event {i}: {e}")

        time.sleep(0.01)  # Slight delay to avoid burst overload


def main():
    print("Generating fake logs for Splunk...")
    start_splunk_container()
    splunk_token = create_splunk_token()
    print("Splunk token created:", splunk_token)

    splunk_url = 'https://localhost:8088/services/collector/event'

    generate_fake_logs(splunk_token, splunk_url)


if __name__ == "__main__":
    main()