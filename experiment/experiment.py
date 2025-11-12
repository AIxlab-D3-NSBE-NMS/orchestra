
from selenium import webdriver  # to control the browser
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
import time, threading


class Task:
    """A task that runs when triggered and completes based on some condition."""
    def __init__(self):
        self.status = "IDLE"  # IDLE -> RUNNING -> COMPLETED
        self.window = None
    def is_triggered(self, previous_task):
        """Check if this task should start. Override in subclasses."""
        return False
    def start(self):
        """Start the task. Override in subclasses."""
        self.status = "RUNNING"
    def is_complete(self):
        """Check if task is done. Override in subclasses."""
        return False
    def cleanup(self):
        """Close window if needed. Override to keep window open."""
        if self.window:
            self.window.quit()
            self.window = None

class ChromiumHandler():
    DEFAULT_CHECK_INTERVAL = 0.5 # every 0.5 seconds checks for callback / clicks
    def __init__(self):
        self.browser        = None # driver
        self.service        = None
        self.options        = None
        self.monitoring     = False
        self.monitor_thread = None
        self.callbacks      = {}  # event_name: callback_function
    def create_new_window(self):
        self.service    = ChromeService("/usr/bin/chromedriver")
        self.options    = ChromeOptions()
        # important: the following line suppresses the google chromium banner
        # saying that the browser is being controlled externally
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.browser = webdriver.Chrome(service=self.service, options=self.options)
        # self.browser is the important 'output'
    def open_url(self, url):
        self.browser.get(url)
    def register_callback(self, event_name, callback_function):
        """Register a callback for a specific event (e.g., 'page_contains', 'url_changed')"""
        self.callbacks[event_name] = callback_function
    def start_monitoring(self, check_interval=DEFAULT_CHECK_INTERVAL):
        """Start background monitoring thread"""
        if self.monitoring:
            return
        self.monitoring = True

        def monitor_loop():
            while self.monitoring and self.browser:
                try:
                    # Check for registered callbacks
                    for event_name, callback in self.callbacks.items():
                        callback(self.browser)
                    time.sleep(check_interval)
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    break

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
    def check_page_content(self, keyword):
        """Helper method to check if page contains specific content"""
        if self.browser:
            return keyword in self.browser.page_source
        return False
    def wait_for_element_click(self, locator, timeout=10, click_detection_method="data-attribute", data_attribute="data-clicked"):
        """
        General function to wait for any element to be clicked

        Args:
            locator: Tuple of (By.TYPE, "selector") e.g., (By.ID, "startBtn")
            timeout: Maximum time to wait in seconds
            click_detection_method: How to detect the click ("data-attribute", "disabled", "navigation", "custom")
            data_attribute: Name of data attribute to check (for "data-attribute" method)

        Returns:
            bool: True if click detected, False if timeout/error
        """
        try:
            print(f"Waiting for user to click element: {locator}")

            if click_detection_method == "data-attribute":
                # Wait for data attribute to be set
                WebDriverWait(self.browser, timeout).until(
                    lambda driver: driver.find_element(*locator)
                                    .get_attribute(data_attribute) == "true"
                )

            elif click_detection_method == "disabled":
                # Wait for element to become disabled
                WebDriverWait(self.browser, timeout).until_not(
                    EC.element_to_be_clickable(locator)
                )

            elif click_detection_method == "navigation":
                # Wait for URL change
                current_url = self.browser.current_url
                WebDriverWait(self.browser, timeout).until(
                    lambda driver: driver.current_url != current_url
                )

            print("Element click detected!")
            return True

        except Exception as e:
            print(f"Timeout or error waiting for element click: {e}")
            return False
    def wait_for_actual_click(self, locator, timeout=3000):
        """Wait for actual click event using JavaScript listener"""
        try:
            print(f"Waiting for element to be ready: {locator}")

            # Wait for element to be present (but maybe not enabled yet)
            element = WebDriverWait(self.browser, 30).until(
                EC.presence_of_element_located(locator)
            )

            # Add JavaScript click listener
            self.browser.execute_script("""
                const element = arguments[0];
                window.submitClicked = false;
                element.addEventListener('click', function(e) {
                    console.log('Submit button clicked!');
                    window.submitClicked = true;
                });
            """, element)

            print("Click listener added. Waiting for user to click submit...")

            # Wait for the click to be detected
            WebDriverWait(self.browser, timeout).until(
                lambda driver: driver.execute_script("return window.submitClicked === true;")
            )

            print("Submit button click detected!")
            return True

        except Exception as e:
            print(f"Error: {e}")
            return False
    def quit(self):
        """Clean shutdown of browser and monitoring"""
        self.stop_monitoring()
        if self.browser:
            self.browser.quit()
            self.browser = None



class WelcomePageTask(Task):
    """Shows a welcome page. Stays open so user can refer back to it."""
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.browser_handler = ChromiumHandler()
    def start(self):
        super().start()# update status to 'RUNNING'
        self.browser_handler.create_new_window()
        self.browser_handler.open_url(self.url)
    def wait_for_start_click(self, timeout=10):
        """Wait for Start button to become disabled (indicating it was clicked)"""
        if self.status == "RUNNING":
            try:
                print("Waiting for user to click Start button...")

                # Wait for button to become non-clickable (disabled)
                WebDriverWait(self.browser_handler.browser, timeout).until(
                                lambda driver: driver.find_element(By.TAG_NAME, "body")
                                              .get_attribute("data-start-clicked") == "true"
                            )
                print("Start button clicked!")
                # self.start_clicked = True
                self.status = "COMPLETED"
                return True
            finally:
                self.wait_for_start_click()
        if self.status == "COMPLETED":
            self.cleanup()

    def cleanup(self):
        # Don't close the window - let user refer back to instructions
        print("WelcomePageTask staying open for reference")
        self.browser_handler.stop_monitoring()
        # Note: not calling browser.quit() to keep window open

class WebPage(Task):
    """Shows a welcome page. Stays open so user can refer back to it."""
    def __init__(self, url, browser_handler = None):
        super().__init__()
        self.url = url
        self.browser_handler = browser_handler or self.browser_handler.create_new_window()
    def start(self):
        super().start()# update status to 'RUNNING'
        self.browser_handler.open_url(self.url)
    def wait_for_start_click(self, timeout=10):
        """Wait for Start button to become disabled (indicating it was clicked)"""
        if self.status == "RUNNING":
            try:
                print("Waiting for user to click Start button...")

                # Wait for button to become non-clickable (disabled)
                WebDriverWait(self.browser_handler.browser, timeout).until(
                                lambda driver: driver.find_element(By.TAG_NAME, "body")
                                              .get_attribute("data-start-clicked") == "true"
                            )
                print("Start button clicked!")
                # self.start_clicked = True
                self.status = "COMPLETED"
                return True
            finally:
                self.wait_for_start_click()
        if self.status == "COMPLETED":
            self.cleanup()

    def wait_for_element_click(self, locator, timeout=10, detection_method="data-attribute", **kwargs):
            """Wait for any element to be clicked using the general function"""
            if self.status != "RUNNING":
                return False

            success = self.browser_handler.wait_for_element_click(
                locator, timeout, detection_method, **kwargs
            )

            if success:
                self.status = "COMPLETED"
                return True
            return False

    def monitor_for_target_text(self, target_text, check_interval=2, timeout=99999):
        """
        Periodically check if the page contains the target URL
        Returns the timestamp when found, or None if timeout reached
        """
        start_monitoring = time.time()
        print(f"Starting to monitor for: {target_text}")

        while time.time() - start_monitoring < timeout:
            try:
                if self.browser_handler.check_page_content(target_text):
                    print(f"Found target URL: {target_text}")
                    return time.time()
                time.sleep(check_interval)
            except Exception as e:
                print(f"Error during monitoring: {e}")
                time.sleep(check_interval)

        print(f"Timeout reached ({timeout}s) - target text not found")
        return None


    def cleanup(self):
        # Don't close the window - let user refer back to instructions
        print("WelcomePageTask staying open for reference")
        self.browser_handler.stop_monitoring()
        # Note: not calling browser.quit() to keep window open



def main():
    return True

if __name__ == "__main__":
    main()
