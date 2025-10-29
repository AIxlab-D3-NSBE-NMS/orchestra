from selenium import webdriver

# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import time, webbrowser

# ---------------------
# CONFIGURE THESE
# ---------------------
PLATFORM_URL = "https://www.google.com"
QUALTRICS_URL = "https://www.youtube.com"
REPORT_KEYWORD = "submit"  # e.g. "report", "summary", or any unique URL fragment
CHECK_INTERVAL = 2  # seconds between checks
# ---------------------

# Launch Chromium
# service = Service("/usr/bin/chromedriver")  # Adjust if needed
service = Service("/snap/bin/geckodriver")
options = Options()
options.add_argument("--width=1920")
options.add_argument("--height=1080")

driver = webdriver.Firefox(service=service, options=options)
driver.maximize_window()
driver.get(PLATFORM_URL)

print("🟢 Demo started. Monitoring for completion...")

try:
    while True:
        current_url = driver.current_url
        # Check if participant reached the report page
        if REPORT_KEYWORD in current_url.lower():
            print("✅ Report detected. Opening Qualtrics survey...")
            driver.get(QUALTRICS_URL)
            break
        time.sleep(CHECK_INTERVAL)
finally:
    # Optional: keep the demo browser open for reference
    driver.quit()
