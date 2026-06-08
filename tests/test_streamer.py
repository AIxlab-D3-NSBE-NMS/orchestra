"""
Smoke-test the Streamer helper with the screen stream.

Inputs:
    Repository root on PYTHONPATH and a stream.streamer.Streamer named screen.

Expected output:
    Instantiates the screen streamer and calls start().
"""

import os
import sys
from pathlib import Path    

if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
    print(__doc__.strip())
    raise SystemExit(0)

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent.resolve())


from stream.streamer import Streamer

screen = Streamer("screen")

screen.start()


