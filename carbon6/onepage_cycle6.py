import pdb
from selenium import webdriver  # to control the browser
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, threading

# ---------------------
# CONFIGURE
# ---------------------
MODE = "test"
DRIVER = "chrome"  # or 'firefox'
if MODE == "test":
    PLATFORM_URL = "https://footprint.wwf.org.uk/"
    QUALTRICS_URL = "https://www.youtube.com"
elif MODE == "production":
    PLATFORM_URL = "https://app.carbon-market.pt/content/cyclesix/ufe/v5/canvas/ufe/modules.html/_login"
    QUALTRICS_URL = "qualtrics.com"
else:
    raise ValueError("Invalid mode")

REPORT_KEYWORD = "submit"  # e.g. "report", "summary", or any unique URL fragment
if MODE == "test":
    REPORT_KEYWORD = "Your footprint is equal to"
CHECK_INTERVAL = 2  # seconds between checks
# ---------------------
qualtrics_window = None

# ---------------------
# FUNCTION DEFINITIONS
# ---------------------
#
def create_new_window(DRIVER):
    if DRIVER == "chrome":
        driver = webdriver.Chrome(service=service, options=options)
    elif DRIVER == "firefox":
        driver = webdriver.Firefox(service=service, options=options)
    return driver
def is_submitted(driver):
    # current_url = driver.current_url
    # return REPORT_KEYWORD in current_url.lower()
    return "Your footprint is equal to" in driver.page_source
def check_if_submitted_and_open_qualtrics(driver, qualtrics_window):
    if is_submitted(driver) and qualtrics_window is None:
        print("Report detected. Opening Qualtrics survey...")
        qualtrics_window = create_new_window(DRIVER)
        qualtrics_window.get(QUALTRICS_URL)
    threading.Timer(
        CHECK_INTERVAL, check_if_submitted_and_open_qualtrics, args=[driver, qualtrics_window]
    ).start()


# Launch Browser
if DRIVER == "chrome":
    service = ChromeService("/usr/bin/chromedriver")
    options = ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
elif DRIVER == "firefox":
    service = FirefoxService("/snap/bin/geckodriver")
    options = FirefoxOptions()

driver = create_new_window(DRIVER)

driver.get(PLATFORM_URL)
WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
).click()

# get the window handle
cyclesix_window_handle = driver.current_window_handle
assert len(driver.window_handles) == 1

# ---------------------
check_if_submitted_and_open_qualtrics(driver, qualtrics_window)

breakpoint()
a = 1
