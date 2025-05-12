from playwright.sync_api import sync_playwright
import json
import os.path

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file_path = os.path.join(script_dir, 'input.json')
output_file_path = os.path.join(script_dir, 'output.json')

def launch_chrome():
    try:
        with open(input_file_path, 'r') as file:
            input_data = json.load(file)
            questions = input_data['questions']
    except Exception as e:
        print(f"Error reading {input_file_path}: {str(e)}")
        return

    results = []

    with sync_playwright() as p:
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        browser = p.chromium.launch(executable_path=chrome_path, headless=False)
        page = browser.new_page()

        try:
            page.goto("http://localhost:8502/")
            page.wait_for_selector("text=Starting dependencies... Please wait.", timeout=300000)
            page.wait_for_selector("text=Starting dependencies... Please wait.", state="detached", timeout=300000)
            page.wait_for_timeout(5000)

            page_title = page.title()
            print("********************************")
            print("Page Title:", page_title)
            assert "Observability Monkey Chat" in page_title, f"Page title does not contain 'Observability Monkey Chat'. Actual title: {page_title}"

            name_app = page.inner_text('#observability-monkey-chat-assistant')
            print("Text from #observability-monkey-chat-assistant:", name_app)
            print("********************************")
            assert "Observability Monkey Chat Assistant" in name_app, f"Text from '#observability-monkey-chat-assistant' does not contain 'Observability Monkey Chat Assistant'. Actual text: {name_app}"

            for question in questions:
                print(f"\nProcessing question: {question}")
                result = {"input": question, "output": ""}

                try:
                    input_field = page.get_by_label("Enter your question:")
                    input_field.fill("")
                    page.wait_for_timeout(2000)
                    print("Input field cleared.")

                    input_field.fill(question)
                    print(f"Question '{question}' entered in the input field.")
                    page.wait_for_timeout(3000)

                    send_button = page.get_by_role("button", name="Send")
                    send_button.click()
                    print("Send button clicked.")
                    page.wait_for_timeout(3000)

                    xpath = "//div[@data-testid='stElementContainer']//div[@data-testid='stMarkdown']//div[@data-testid='stMarkdownContainer']/div[@style='text-align: left; padding: 4px 0px;']"
                    page.wait_for_selector(f'xpath={xpath}', timeout=30000)
                    element = page.locator(f'xpath={xpath}')
                    text = element.inner_text()

                    print("Extracted Text:", text)
                    result["output"] = text

                except Exception as e:
                    print(f"Error processing question '{question}': {str(e)}")
                    result["output"] = f"Error: {str(e)}"

                results.append(result)
                page.wait_for_timeout(2000)

        except Exception as e:
            print(f"An error occurred during setup: {str(e)}")
            if not results:
                results.append({"input": "Setup failed", "output": f"Error: {str(e)}"})

        finally:
            try:
                with open(output_file_path, 'w') as file:
                    json.dump({"results": results}, file, indent=4)
                print(f"\nResults written to {output_file_path}")
            except Exception as e:
                print(f"Error writing to {output_file_path}: {str(e)}")

            browser.close()

if __name__ == "__main__":
    launch_chrome()