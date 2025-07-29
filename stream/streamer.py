import os
import sys 
from pathlib import Path
import subprocess


if sys.platform.startswith("win"):
    os.environ["FFMPEG_BIN"] = str(Path(__file__).parent / "mediamtx" / "ffmpeg.exe")
    exe_name = "mediamtx.exe"
else:
    os.environ["FFMPEG_BIN"] = str(Path(__file__).parent / "mediamtx" / "ffmpeg")
    exe_name = "mediamtx"

STREAM_CONFIGS = {
    "screen":   "screen.yaml",
    "webcam":   "webcam.yaml",
    "owl":      "owl.yaml",
    "pcsound":  "pcsound.yaml",
    "owlsound": "owlsound.yaml",
    # Add more mappings as needed
}

class Streamer:
    def __init__(self, kind: str = ""):
        self.kind = kind # screen, webcam, owl, pcsound, owlsound
        
        self.mediamtx_path = (Path(__file__).parent / 'mediamtx' / exe_name).resolve()
        
        self.config_path = (Path(__file__).parent / 'mediamtx' / 'configs' / STREAM_CONFIGS.get(self.kind)).resolve()

        self.process = None
        
    def start(self):
        if not self.kind:
            raise ValueError("Stream kind must be specified.")
        
        if not self.mediamtx_path.exists():
            raise FileNotFoundError(f"MediaMTX executable not found at {self.mediamtx_path}")
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        
        command = str(self.mediamtx_path) + ' ' + str(self.config_path)
        self.process = subprocess.Popen(command.split(" "))
        print(f"Started process PID: {self.process.pid}")
        stdout, stderr = self.process.communicate()
        print("Output:\n", stdout.decode())
        print("Errors:\n", stderr.decode())


    def stop(self):
        if self.process and self.process.poll() is None:
            print(f"Terminating process PID: {self.process.pid}")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                print("Process terminated.")
            except subprocess.TimeoutExpired:
                print("Process did not terminate in time. Killing...")
                self.process.kill()
                print("Process killed.")
        else:
            print("No running process to stop.")