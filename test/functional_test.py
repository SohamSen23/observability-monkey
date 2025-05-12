from playwright.sync_api import sync_playwright
import json
import os.path

# Set up file paths
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file_path = os.path.join(script_dir, 'input.json')
output_file_path = os.path.join(script_dir, 'output.json')

def launch_chrome():
    # Load questions from input.json
    try:
        with open(input_file_path, 'r') as file:
            input_data = json.load(file)
            questions = input_data['questions']
    except Exception as e:
        print(f"Error reading {input_file_path}: {str(e)}")
        return

    results = []

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        try:
            # Navigate to the page and wait for it to load
            page.goto("http://localhost:8501/")
            page.wait_for_selector("text=Starting dependencies... Please wait.", timeout=300000)
            page.wait_for_selector("text=Starting dependencies... Please wait.", state="detached", timeout=300000)
            page.wait_for_timeout(2000)  # Reduced from 4000 to 2000

            # Verify page title
            page_title = page.title()
            print("********************************")
            print("Page Title:", page_title)
            assert "Observability Monkey Chat" in page_title, f"Page title mismatch. Got: {page_title}"

            # Verify app name
            name_app = page.inner_text('#observability-monkey-chat-assistant')
            print("Text from #observability-monkey-chat-assistant:", name_app)
            print("********************************")
            assert "Observability Monkey Chat Assistant" in name_app, f"Text mismatch in '#observability-monkey-chat-assistant'. Got: {name_app}"

            for question in questions:
                print(f"\nProcessing question: {question}")
                result = {"input": question, "output": ""}

                try:
                    # Scroll to top before interaction
                    page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
                    page.wait_for_timeout(1000)  # Already 1s
                    print("Scrolled to the top.")

                    # Clear and fill the input field
                    input_field = page.locator("//textarea[@aria-label='Enter your question:']")
                    input_field.fill("")  # Clear the field
                    page.wait_for_timeout(1000)  # Already 1s
                    input_field.fill(question)
                    print(f"Entered question: {question}")
                    page.wait_for_timeout(1000)  # Already 1s (reduced previously)

                    # Click the send button
                    send_button = page.locator("//button[@data-testid='stChatInputSubmitButton']")
                    send_button.click()
                    print("Clicked send button.")
                    page.wait_for_timeout(1000)  # Already 1s (reduced previously)

                    # Extract the last bot response
                    xpath = "//div[@data-testid='stChatMessageContent' and @aria-label='Chat message from bot']//div[@data-testid='stMarkdownContainer']"
                    page.wait_for_selector(f'xpath={xpath}', timeout=30000)

                    # Get all bot responses and take the last one
                    elements = page.locator(f'xpath={xpath}')
                    count = elements.count()
                    if count > 0:
                        text = elements.nth(count - 1).inner_text().strip()
                        print("Extracted Bot Response:", text)
                        result["output"] = text
                    else:
                        print("No bot response found.")
                        result["output"] = "No bot response found."

                except Exception as e:
                    print(f"Error processing question '{question}': {str(e)}")
                    result["output"] = f"Error: {str(e)}"

                results.append(result)
                page.wait_for_timeout(1000)  # Already 1s (reduced previously)

        except Exception as e:
            print(f"An error occurred during setup: {str(e)}")
            if not results:
                results.append({"input": "Setup failed", "output": f"Error: {str(e)}"})

        finally:
            # Save results to output.json
            try:
                with open(output_file_path, 'w') as file:
                    json.dump({"results": results}, file, indent=4)
                print(f"\nResults written to {output_file_path}")
            except Exception as e:
                print(f"Error writing to {output_file_path}: {str(e)}")

            # Close browser
            browser.close()

if __name__ == "__main__":
    launch_chrome()