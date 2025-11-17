import pdb
import sys
from pathlib import Path
import yaml
from enum import IntEnum, auto
experiment_path = Path(__file__).parent.parent / "experiment"
sys.path.insert(0, str(experiment_path))
import experiment
from selenium.webdriver.common.by import By
import time
import datetime
import threading
import subprocess

class State(IntEnum):
    CYCLE6_DEBRIEF          = 0
    CYCLE6_CONSENT          = auto()
    CYCLE6_AMPARA           = auto()
    CYCLE6_USEPLATFORM      = auto()
    CYCLE6_QUALTRICS        = auto()
    CYCLE6_THANKYOU         = auto()

EXP_CFG  = Path.cwd() / 'prr_experiments' / 'private' / "PRR_CONFIG.yaml"
CFG_DICT = yaml.safe_load(open(EXP_CFG.__str__(), 'r'))
welcome_url = EXP_CFG.parent / CFG_DICT['welcome_page']


browser_handler = experiment.ChromiumHandler()
browser_handler.create_new_window()

rec = experiment.ScreenRecorder()
recordings_dir = Path('/home/participant/data/cyclesix')
recordings_dir.mkdir(parents=True, exist_ok=True)
def _new_recording_path(prefix="garden"):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return recordings_dir / f"{prefix}_{ts}.mkv"
def open_pdf_in_background(pdf_path):
    try:
        # Use subprocess.Popen to run evince in the background
        # stdout=subprocess.PIPE captures the output, stderr=subprocess.PIPE captures errors
        process = subprocess.Popen(['evince', pdf_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # You can optionally capture the outputs if you need them later
        stdout, stderr = process.communicate()

        # Check if there were any errors during execution
        if process.returncode != 0:
            print(f"Error opening PDF: {stderr.decode('utf-8')}")
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


    state = State.CYCLE6_AMPARA
    current_page.browser_handler.browser.get(CFG_DICT['celfocus_cyclesix_url'])
    open_pdf_in_background(EXP_CFG.parent / 'ampara.pdf')

state = State.CYCLE6_USEPLATFORM

breakpoint()

# todo: do not close upon closing pdf