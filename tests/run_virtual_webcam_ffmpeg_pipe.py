"""
Send webcam frames through ffmpeg to a V4L2 loopback device with timestamps.

Inputs:
    W, H, FPS constants, camera index 0, optional logo image, and output
    loopback device /dev/video10 in the ffmpeg command.

Expected output:
    Streams timestamped frames to the virtual webcam until capture stops.
"""

import cv2
import subprocess
import datetime
import sys

if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
    print(__doc__.strip())
    raise SystemExit(0)

W, H, FPS = 640, 480, 30

logo = None

cmd = [
    "ffmpeg",
    "-loglevel", "error",
    "-re",
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-s", f"{W}x{H}",
    "-r", str(FPS),
    "-i", "-",
    "-f", "v4l2",
    "-pix_fmt", "yuyv422",
    "/dev/video10"
]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
cap.set(cv2.CAP_PROP_FPS, FPS)

while True:
    ok, frame = cap.read()
    if not ok:
        break

    # Add timestamp
    now = datetime.datetime.now()
    timestamp = f"{now:%Y-%m-%d %H:%M:%S}.{now.microsecond:06d}"[:23]
    cv2.rectangle(frame, (0, 0), (220, 20), (0, 0, 0), cv2.FILLED)
    cv2.putText(frame, timestamp, (0, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_8, False)

    # Add logo (optional)
    if logo is not None:
        lh, lw = logo.shape[:2]
        frame[10:10+lh, 10:10+lw] = logo[:, :, :3]

    proc.stdin.write(frame.tobytes())

proc.stdin.close()
proc.wait()

