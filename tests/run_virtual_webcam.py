"""
Relay frames from one V4L2 camera device to a loopback webcam device.

Inputs:
    input_device and output_device constants, usually physical /dev/video0
    and a v4l2loopback device such as /dev/video11.

Expected output:
    Continuously copies frames to the virtual webcam until interrupted.
"""

import cv2
import numpy as np
import sys

if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
    print(__doc__.strip())
    raise SystemExit(0)

# Input webcam device
input_device = "/dev/video0"

# Output loopback device
output_device = "/dev/video11"

# Open input video capture
cap = cv2.VideoCapture(input_device, cv2.CAP_V4L2)
if not cap.isOpened():
    raise RuntimeError(f"Cannot open input device {input_device}")

# Get frame properties
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30  # fallback to 30 if fps is 0

# Open output video writer
out = cv2.VideoWriter(
    output_device,
    0,
    fps,
    (width, height),
    True
)

if not out.isOpened():
    raise RuntimeError(f"Cannot open output device {output_device}")

print(f"Relaying frames from {input_device} to {output_device}...")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        out.write(frame)

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    cap.release()
    out.release()

