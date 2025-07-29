import os
import sys
from pathlib import Path    

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent.resolve())


from stream.streamer import Streamer

screen = Streamer("screen")

screen.start()


