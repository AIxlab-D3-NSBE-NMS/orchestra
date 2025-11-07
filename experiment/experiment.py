from asyncio.unix_events import SelectorEventLoop
from selenium import webdriver  # to control the browser
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
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
    def __init__(self):
        self.webdriver  = None
        self.service    = None
        self.options    = None
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks = {}  # event_name: callback_function
        
    def create_new_window(self):
        self.service    = ChromeService("/usr/bin/chromedriver")
        self.options    = ChromeOptions()
        # important: the following line suppresses the google chromium banner
        # saying that the browser is being controlled externally
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.webdriver = webdriver.Chrome(service=self.service, options=self.options)
        
    def open_url(self, url):
        self.webdriver.get(url)
        
    def register_callback(self, event_name, callback_function):
        """Register a callback for a specific event (e.g., 'page_contains', 'url_changed')"""
        self.callbacks[event_name] = callback_function
        
    def start_monitoring(self, check_interval=3):
        """Start background monitoring thread"""
        if self.monitoring:
            return
            
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring and self.webdriver:
                try:
                    # Check for registered callbacks
                    for event_name, callback in self.callbacks.items():
                        callback(self.webdriver)
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
        if self.webdriver:
            return keyword in self.webdriver.page_source
        return False
        
    def quit(self):
        """Clean shutdown of browser and monitoring"""
        self.stop_monitoring()
        if self.webdriver:
            self.webdriver.quit()
            self.webdriver = None


class WelcomePageTask(Task):
    """Shows a welcome page. Stays open so user can refer back to it."""
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.browser = ChromiumHandler()

    def start(self):
        super().start()# update status to 'RUNNING'
        self.browser.create_new_window()
        self.browser.open_url(self.url)
        
        # Example: Register a callback to monitor for specific content
        def on_page_loaded(driver):
            if "Google" in driver.title:
                print("Google page detected")
                
        self.browser.register_callback("page_check", on_page_loaded)
        self.browser.start_monitoring(check_interval=5)
        
    def is_complete(self):
        return self.status == "completed"
        
    def cleanup(self):
        # Don't close the window - let user refer back to instructions
        print("WelcomePageTask staying open for reference")
        self.browser.stop_monitoring()
        # Note: not calling browser.quit() to keep window open




def main():
    return True

if __name__ == "__main__":
    main()
