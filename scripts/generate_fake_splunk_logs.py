import requests
import random
import json
import time
from splunk_utils import create_splunk_token, start_splunk_container


def generate_fake_logs(splunk_token, splunk_url):
    headers = {
        'Authorization': f'Splunk {splunk_token}',
        'Content-Type': 'application/json'
    }

    java_errors = [
        """Exception in thread "main" java.lang.NullPointerException
        at com.example.service.UserService.getUser(UserService.java:42)
        at com.example.controller.UserController.handleRequest(UserController.java:21)
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)""",

        """java.sql.SQLException: Connection refused
        at com.example.dao.DatabaseConnection.connect(DatabaseConnection.java:88)
        at com.example.Main.main(Main.java:14)""",

        """org.springframework.beans.factory.BeanCreationException: Error creating bean
        at org.springframework.beans.factory.support.AbstractBeanFactory.doGetBean(AbstractBeanFactory.java:350)
        at org.springframework.context.support.AbstractApplicationContext.refresh(AbstractApplicationContext.java:476)""",

        """java.lang.ArrayIndexOutOfBoundsException: 5
        at com.example.utils.ArrayUtils.getElement(ArrayUtils.java:15)
        at com.example.service.SomeService.process(SomeService.java:60)""",

        """java.lang.IllegalStateException: Cannot call sendRedirect() after the response has been committed
        at org.apache.catalina.connector.ResponseFacade.sendRedirect(ResponseFacade.java:483)
        at com.example.web.LoginServlet.doPost(LoginServlet.java:77)"""
    ]

    for i in range(1000):
        log_event = {
            "event": {
                "level": "ERROR",
                "error": random.choice(java_errors),
                "logger": f"com.example.module{random.randint(1, 5)}",
                "thread": f"Thread-{random.randint(1, 20)}",
                "timestamp": int(time.time())
            },
            "sourcetype": "java_errors"
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