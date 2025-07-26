import subprocess
from pathlib import Path

class Streamer:
    def __init__(self, kind: str = ""):
        self.config_path = Path(config_path)
        self.mediamtx_path = './mediamtx/'
        self.process = None

    def start(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file {self.config_path} not found.")
        if self.process is not None and self.process.poll() is None:
            raise RuntimeError("Stream already running.")
        self.process = subprocess.Popen(
            [self.mediamtx_path, str(self.config_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None