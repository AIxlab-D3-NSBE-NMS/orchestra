from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time, webbrowser, os

PLATFORM_URL = "https://footprint.wwf.org.uk/questionnaire"
QUALTRICS_URL = "https://www.youtube.com"
REPORT_KEYWORD = "results"
CHECK_INTERVAL = 2
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"

def launch_driver():
    service = Service(CHROMEDRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Hide Selenium detection & “automation” banner
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })
    return driver

