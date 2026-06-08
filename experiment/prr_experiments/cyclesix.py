"""
Run the Cycle 6 PRR experiment with MediaMTX and screen recording enabled.

Inputs:
    prr_experiments/private/PRR_CONFIG.yaml with consent, platform, and asset
    paths; MediaMTX record_cyclesix.yaml; evince for the Ampara PDF.

Expected output:
    Opens consent and Cycle 6 pages, starts owl and screen recording after
    consent, opens the Ampara PDF, then stops recordings at completion text.
"""

import pdb
import sys
from pathlib import Path
import yaml
from enum import IntEnum, auto
experiment_path = Path(__file__).parent.parent / "experiment"
sys.path.insert(0, str(experiment_path))
import experiment
from experiment import MediaMTX
from experiment import ScreenRecorder
from selenium.webdriver.common.by import By
import time
import datetime
import threading
import subprocess

if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
    print(__doc__.strip())
    raise SystemExit(0)

class State(IntEnum):
    CYCLE6_DEBRIEF          = 0
    CYCLE6_CONSENT          = auto()
    CYCLE6_AMPARA           = auto()
    CYCLE6_USEPLATFORM      = auto()
    CYCLE6_QUALTRICS        = auto()
    CYCLE6_THANKYOU         = auto()

mediamtx_proc = MediaMTX.start_mediamtx(str(Path.cwd() / 'prr_experiments' / "record_cyclesix.yaml"))
screen_recorder = ScreenRecorder()
screen_rec_path = f"/data/cyclesix/cyclesix_screen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

EXP_CFG  = Path.cwd() / 'prr_experiments' / 'private' / "PRR_CONFIG.yaml"
CFG_DICT = yaml.safe_load(open(EXP_CFG.__str__(), 'r'))
welcome_url = EXP_CFG.parent / CFG_DICT['welcome_page']

browser_handler = experiment.ChromiumHandler()
browser_handler.create_new_window()

def open_pdf_in_background(pdf_path):
    try:
        # Use subprocess.Popen to run evince in the background
        # stdout=subprocess.PIPE captures the output, stderr=subprocess.PIPE captures errors
        process = subprocess.Popen(['evince', '--page-label=1', pdf_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # You can optionally capture the outputs if you need them later
        #stdout, stderr = process.communicate()

        # Check if there were any errors during execution
        #if process.returncode != 0:
        #    print(f"Error opening PDF: {stderr.decode('utf-8')}")
    except FileNotFoundError:
        print("evince is not installed or not found in the PATH.")
    except Exception as e:
        print(f"An error occurred: {e}")


state = State.CYCLE6_DEBRIEF
current_page = experiment.WebPage(CFG_DICT['informed_consent_cyclesix'],
                                    browser_handler=browser_handler)
current_page.start() # create browser driver and open url

#if (current_page.wait_for_start_click(timeout=9999)):
#    current_page.browser_handler.browser.get(CFG_DICT['informed_consent_cyclesix'])
#    time.sleep(2)

state = State.CYCLE6_CONSENT

if current_page.browser_handler.wait_for_actual_click(
    (By.XPATH, "//button[@aria-label='Submit']"), timeout=9999):
    print('Consent submitted! Start recording screen and video')
    # TODO: TOGGLE SCREEN RECORDING
    time.sleep(1)

    MediaMTX.start_recording("owl")
    screen_recorder.start_recording(screen_rec_path)
    time.sleep(1)
    print('opening cyclesix platform and ampara pdf')

    state = State.CYCLE6_AMPARA
    current_page.browser_handler.browser.get(CFG_DICT['celfocus_cyclesix_url'])
    open_pdf_in_background(EXP_CFG.parent / 'ampara.pdf')

target_text = 'Please go see the person responsible for the room'

while True:
    if len(current_page.browser_handler.browser.window_handles) > 1:
        current_page.browser_handler.browser.switch_to.window(current_page.browser_handler.browser.window_handles[-1])
        current_page.browser_handler.browser.close()
        current_page.browser_handler.browser.switch_to.window(current_page.browser_handler.browser.window_handles[0])
        time.sleep(1)

    if current_page.monitor_for_target_text(target_text):
        print("Detected completion message.")
        MediaMTX.stop_recording('owl')
        screen_recorder.stop_recording()
        time.sleep(10)
        print("mediamtx will be terminated.")
        screen_recorder.force_stop()
        current_page.cleanup()

# todo: do not close upon closing pdf
