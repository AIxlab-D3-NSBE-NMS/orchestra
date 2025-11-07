import pdb
from selenium import webdriver  # to control the browser
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
import time, threading

# ---------------------
# CONFIGURE
# ---------------------
MODE = "test"
DRIVER = "chrome"  # or 'firefox'
if MODE == "test":
    PLATFORM_URL = "https://forms.cloud.microsoft/e/dHmkTn0XAv"
    QUALTRICS_URL = "https://novasbe.az1.qualtrics.com/jfe/form/SV_2lwJ2iia3pBK4oC"
elif MODE == "production":
    PLATFORM_URL = "https://app.carbon-market.pt/content/cyclesix/ufe/v5/canvas/ufe/modules.html/_login"
    QUALTRICS_URL = "https://novasbe.az1.qualtrics.com/jfe/form/SV_2lwJ2iia3pBK4oC"
else:
    raise ValueError("Invalid mode")

REPORT_KEYWORD = "submit"  # e.g. "report", "summary", or any unique URL fragment
if MODE == "test":
    REPORT_KEYWORD = "Your footprint is equal to"
CHECK_INTERVAL = 3  # seconds between checks
GOODBYE_INTERVAL = 20
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
    return "Your footprint is equal to" in driver.page_source
def check_if_submitted_and_open_qualtrics(driver, qualtrics_window):
    if is_submitted(driver) and qualtrics_window is None:
        print("Report detected. Opening Qualtrics survey...")
        driver.execute_script("alert('Please analyse the content of this page carefully. \
            We will ask you some questions about these results. Click next when you are ready to proceed.');")
        while True:
            try:
                alert = driver.switch_to.alert
                time.sleep(0.5)
            except NoAlertPresentException:
                break
        qualtrics_window = create_new_window(DRIVER)
        qualtrics_window.get(QUALTRICS_URL)

        if qualtrics_window is None:
            print('carbon footprint not filled in yet')
    qualtrics_window = threading.Timer(
         CHECK_INTERVAL,
         check_if_submitted_and_open_qualtrics,
         args=[driver, qualtrics_window]).start()

    return qualtrics_window
def is_qualtrics_finished(qualtrics_window):
    if qualtrics_window is not None:
        if 'We thank you for your time spent taking this survey'\
            in qualtrics_window.page_source:
            print("Qualtrics survey completed.")
            qualtrics_window.quit()
            driver.quit()
    threading.Timer(GOODBYE_INTERVAL, is_qualtrics_finished, args=[qualtrics_window]).start()


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
# COOKIE CONTROL
# WebDriverWait(driver, 10).until(
#     EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
# ).click()

# get the window handle
cyclesix_window_handle = driver.current_window_handle
assert len(driver.window_handles) == 1

# ---------------------
qualtrics_window = check_if_submitted_and_open_qualtrics(driver, qualtrics_window)

is_qualtrics_finished(qualtrics_window) # closes window

breakpoint()
a = 1
