import pdb
from math import exp
from pickletools import StackObject
import sys
from pathlib import Path
from tracemalloc import start
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
EXP_CFG  = Path.cwd() / 'prr_experiments' / 'private' / "PRR_CONFIG.yaml"
CFG_DICT = yaml.safe_load(open(EXP_CFG.__str__(), 'r'))
# dict_keys([   'informed_consent_taikai',
#               'informed_consent_cyclesix',
#               'celfocus_cyclesix_url',
#               'taikai_garden_url'])
welcome_url = EXP_CFG.parent / CFG_DICT['welcome_page']
if CFG_DICT['informed_consent_taikai'].split('.')[-1]=='html':
    CFG_DICT['informed_consent_taikai'] = (EXP_CFG.parent / CFG_DICT['informed_consent_taikai']).as_uri()
breakpoint()
browser_handler = experiment.ChromiumHandler()
browser_handler.create_new_window()

state = State.WELCOME
current_page = experiment.WebPage(  welcome_url.as_uri(),
                                    browser_handler=browser_handler)
current_page.start() # create browser driver and open url

if (current_page.wait_for_start_click(timeout=9999)):
    current_page.browser_handler.browser.get(CFG_DICT['informed_consent_taikai'])
    time.sleep(2)

state = State.GARDEN_CONSENT
# Use the improved click detection
if current_page.browser_handler.wait_for_actual_click(
    (By.XPATH, "//button[@aria-label='Submit']"), timeout=9999):
    print('Consent submitted! Start recording screen')
    # TODO: TOGGLE SCREEN RECORDING
    time.sleep(5)
    current_page.browser_handler.browser.get(CFG_DICT['taikai_qualtrics'])

state = State.GARDEN_QUALTRICS_PHASE1

if current_page.monitor_for_target_text('https://garden.taikai.network/feed'):
    print('Start COUNTDOWN')

state = State.GARDEN_USEMENTOR
# start haf an hour countdown, warn at 15 left and 5 left
notified_1st = False
notified_2nd = False
start_time_garden = time.time()
while time.time() - start_time_garden < CFG_DICT['garden_allowed_duration']:
    if time.time() - start_time_garden > (CFG_DICT['garden_allowed_duration']-CFG_DICT['garden_first_notification']) \
        and not notified_1st:
            notified_1st = True
            current_page.browser_handler.browser.execute_script(
                            f"alert('{CFG_DICT['garden_first_notification']//60} minutes until submission.');")
    if time.time() - start_time_garden > (CFG_DICT['garden_allowed_duration']-CFG_DICT['garden_second_notification']) \
        and not notified_2nd:
            notified_2nd = True
            current_page.browser_handler.browser.execute_script(
                            f"alert('{CFG_DICT['garden_first_notification']//60} minutes until submission.');")
print('times up')

breakpoint()
