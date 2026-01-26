import pdb
import os
import sys
from pathlib import Path
import yaml
from enum import IntEnum, auto
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime
import threading


experiment_path = Path(__file__).parent.parent / "experiment"
sys.path.insert(0, str(experiment_path))
import experiment
from experiment import MediaMTX


HOME = Path.home()

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

recordings_dir = HOME / "data" / "garden"
recordings_dir.mkdir(parents=True, exist_ok=True)
mediamtx_proc = MediaMTX.start_mediamtx(str(Path.cwd() / 'prr_experiments' / "record_garden.yaml"))

EXP_CFG  = Path.cwd() / 'prr_experiments' / 'private' / "PRR_CONFIG.yaml"
CFG_DICT = yaml.safe_load(open(EXP_CFG.__str__(), 'r'))
welcome_url = EXP_CFG.parent / CFG_DICT['welcome_page']
if CFG_DICT['informed_consent_taikai'].split('.')[-1]=='html':
    CFG_DICT['informed_consent_taikai'] = (EXP_CFG.parent / CFG_DICT['informed_consent_taikai']).as_uri()

browser_handler = experiment.ChromiumHandler()
browser_handler.create_new_window()


# --- Your experiment logic here ---
state = State.WELCOME
current_page = experiment.WebPage(welcome_url.as_uri(), browser_handler=browser_handler)
current_page.start() # create browser driver and open url

if (current_page.wait_for_start_click(timeout=9999)):
    current_page.browser_handler.browser.get(CFG_DICT['informed_consent_taikai'])
    time.sleep(2)

state = State.GARDEN_CONSENT
if current_page.browser_handler.wait_for_actual_click(
    (By.XPATH, "//button[@aria-label='Submit']"), timeout=9999):
    print('Consent submitted! Start recording screen')
    MediaMTX.start_recording("screen")
    time.sleep(1)
    current_page.browser_handler.browser.get(CFG_DICT['taikai_qualtrics'])
    print(f"Screen recording started")

state = State.GARDEN_QUALTRICS_PHASE1
if current_page.monitor_for_target_text('https://garden.taikai.network/feed'):
    time.sleep(1)

submitted = False
state = State.GARDEN_USEMENTOR
notified_1st = False
notified_2nd = False
start_time_garden = time.time()
while time.time() - start_time_garden < CFG_DICT['garden_allowed_duration']:
    if current_page.browser_handler.wait_for_actual_click(
        (By.ID, "NextButton"), timeout=1):
        print('Submitted business plan')
        submitted = True
    if submitted:
        break
    if time.time() - start_time_garden > (CFG_DICT['garden_allowed_duration']-CFG_DICT['garden_first_notification']) \
        and not notified_1st:
            print('showing first time notification')
            notified_1st = True
            remaining_minutes = CFG_DICT['garden_first_notification'] // 60
            if not submitted:
                current_page.force_tab_active()
                current_page.show_non_blocking_popup(f"{remaining_minutes} minutes remaining", duration_seconds=1)

    if time.time() - start_time_garden > (CFG_DICT["garden_allowed_duration"]-CFG_DICT["garden_second_notification"]) \
        and not notified_2nd:
            notified_2nd = True
            current_page.force_tab_active()
            if not submitted:
                remaining_minutes = CFG_DICT['garden_first_notification'] // 60
                current_page.show_non_blocking_popup(f"{remaining_minutes} minutes remaining", duration_seconds=1)

    if (time.time() - start_time_garden > (CFG_DICT["garden_allowed_duration"])) and not submitted:
        current_page.force_tab_active()
        print('Please submit')
        current_page.show_non_blocking_popup(f"Please submit your business plan!", duration_seconds=1)

if current_page.browser_handler.wait_for_actual_click(
    (By.ID, "NextButton"), timeout=9999):
    print('Submitted business plan')
    submitted = True

target_text = 'Please call the person responsible for the room to receive further instructions'
if current_page.monitor_for_target_text(target_text):
    print("Detected completion message.")
    MediaMTX.stop_recording("screen")
    time.sleep(10)
    print("mediamtx will be terminated.")
    MediaMTX.kill_mediamtx(mediamtx_proc)
    current_page.cleanup()
