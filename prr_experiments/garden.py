from bdb import Breakpoint
import pdb
import sys
from pathlib import Path

# Add the experiment directory to sys.path
experiment_path = Path(__file__).parent.parent / "experiment"
sys.path.insert(0, str(experiment_path))

import experiment

welcome_url = Path.cwd() / 'prr_experiments' / "welcome_page.html"

welcome_page = experiment.WelcomePageTask(welcome_url.as_uri())
welcome_page.start() # create browser driver and open url

input()
