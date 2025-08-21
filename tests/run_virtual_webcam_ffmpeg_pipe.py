import cv2, subprocess, numpy as np

W, H, FPS = 640, 480, 30

# Choose a pixel format supported by /dev/video10 (YUYV or MJPEG)
# YUYV example:
cmd = [
    "ffmpeg",
    "-loglevel", "error",
    "-re",                      # pace frames in real-time
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",        # what we write from Python
    "-s", f"{W}x{H}",
    "-r", str(FPS),
    "-i", "-",                  # stdin
    "-f", "v4l2",
    "-pix_fmt", "yuyv422",      # or use "-codec mjpeg" for MJPEG
    "/dev/video10"
]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
cap.set(cv2.CAP_PROP_FPS, FPS)

while True:
    ok, frame = cap.read()
    if not ok: break
    # Ensure size matches W x H
    if frame.shape[1] != W or frame.shape[0] != H:
        frame = cv2.resize(frame, (W, H))
    proc.stdin.write(frame.tobytes())

proc.stdin.close()
proc.wait()

