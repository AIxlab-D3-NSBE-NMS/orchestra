from sqlite3.dbapi2 import Time
from selenium import webdriver  # to control the browser
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time, threading


# ---------------------
# FUNCTION DEFINITIONS
# ---------------------
def is_submitted(driver):
    current_url = driver.current_url
    return REPORT_KEYWORD in current_url.lower()


def check_if_submitted_and_open_qualtrics(driver):
    if is_submitted(driver):
        print("✅ Report detected. Opening Qualtrics survey...")
        driver.get(QUALTRICS_URL)
    threading.Timer(
        CHECK_INTERVAL, check_if_submitted_and_open_qualtrics, args=[driver]
    ).start()


# ---------------------
# CONFIGURE
# ---------------------
PLATFORM_URL = "https://app.carbon-market.pt/content/cyclesix/ufe/v5/canvas/ufe/modules.html/_login"
QUALTRICS_URL = "https://www.youtube.com"
REPORT_KEYWORD = "submit"  # e.g. "report", "summary", or any unique URL fragment
CHECK_INTERVAL = 2  # seconds between checks
# ---------------------

# Launch Browser
service = FirefoxService("/snap/bin/geckodriver")
options = FirefoxOptions()
options.add_argument("--width=1920")
options.add_argument("--height=1080")
driver = webdriver.Firefox(service=service, options=options)
driver.maximize_window()
driver.get(PLATFORM_URL)

# ---------------------

check_if_submitted_and_open_qualtrics(driver)

# TODO:
# - Add a function to handle errors or exceptions that may occur during closing.
# - Implement a mechanism to handle multiple reports or surveys.
# - auto accept cookies and cookie popups
# - auto login on carbon platform and qualtrix
# - reset credentials after each survey
# - send email notification when survey is completed
