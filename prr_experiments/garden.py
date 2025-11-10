import pdb
from math import exp
import sys
from pathlib import Path
import yaml
from enum import IntEnum, auto
experiment_path = Path(__file__).parent.parent / "experiment"
sys.path.insert(0, str(experiment_path))
import experiment
from selenium.webdriver.common.by import By
import time


class State(IntEnum):
    WELCOME = 0
    GARDEN_CONSENT          = auto()
    GARDEN_QUALTRICS_PHASE1 = auto() # start video rec
    GARDEN_USEMENTOR        = auto()
    GARDEN_QUALTRICS_PHASE2 = auto()
    GARDEN_THANKYOU         = auto()
    CYCLE6_CONSENT          = auto()
    CYCLE6_AMPARA           = auto()
    CYCLE6_USEPLATFORM      = auto()
    CYCLE6_QUALTRICS        = auto()
    CYCLE6_THANKYOU         = auto()




# Add the experiment directory to sys.path
URL_CFG  = Path.cwd() / 'prr_experiments' / 'private' / "PRR_CONFIG.yaml"
URL_DICT = yaml.safe_load(open(URL_CFG.__str__(), 'r'))
# dict_keys([   'informed_consent_taikai',
#               'informed_consent_cyclesix',
#               'celfocus_cyclesix_url',
#               'taikai_garden_url'])
welcome_url = URL_CFG.parent / URL_DICT['welcome_page']

browser_handler = experiment.ChromiumHandler()
browser_handler.create_new_window()

state = State.WELCOME
current_page = experiment.WebPage(  welcome_url.as_uri(),
                                    browser_handler=browser_handler)
current_page.start() # create browser driver and open url

if (current_page.wait_for_start_click()):
    current_page.browser_handler.browser.get(URL_DICT['informed_consent_taikai'])
    time.sleep(2)

# Add this debugging code to check if we can find the element
def debug_submit_button(driver):
    """Debug function to test different locators for the submit button"""
    locators_to_try = [
        ("aria-label", (By.XPATH, "//button[@aria-label='Submit']")),
        ("text content", (By.XPATH, "//button[contains(text(), 'Submit')]")),
        ("span text", (By.XPATH, "//button[.//span[contains(text(), 'Submit')]]")),
        ("type submit", (By.XPATH, "//button[@type='submit']")),
        ("css aria-label", (By.CSS_SELECTOR, "button[aria-label='Submit']")),
        ("css type", (By.CSS_SELECTOR, "button[type='submit']")),
        ("mat-flat-button", (By.CSS_SELECTOR, "button[mat-flat-button]")),
        ("class contains", (By.CSS_SELECTOR, "button.mat-mdc-unelevated-button")),
    ]

    print("=== Debugging Submit Button Locators ===")
    for name, locator in locators_to_try:
        try:
            elements = driver.find_elements(*locator)
            print(f"✓ {name}: Found {len(elements)} element(s)")
            if elements:
                element = elements[0]
                print(f"  - Text: '{element.text}'")
                print(f"  - aria-label: '{element.get_attribute('aria-label')}'")
                print(f"  - type: '{element.get_attribute('type')}'")
                print(f"  - enabled: {element.is_enabled()}")
        except Exception as e:
            print(f"✗ {name}: Error - {e}")

    return True

# Add this to your garden.py temporarily:
# debug_submit_button(current_page.browser_handler.browser)

# Use the improved click detection
if current_page.browser_handler.wait_for_actual_click(
    (By.XPATH, "//button[@aria-label='Submit']"),
    timeout=3000  # 50 minutes
):
    print('Consent submitted! Start recording screen')

breakpoint()
