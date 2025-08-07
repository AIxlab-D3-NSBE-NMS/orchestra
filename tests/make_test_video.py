import cv2
import numpy as np
from tqdm import tqdm

# Video settings
width, height = 320, 240
fps = 30
duration_seconds = 2 * 60 * 60
total_frames = duration_seconds * fps

# Output video writer
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('/home/labadmin/Desktop/black_white_flash.avi', fourcc, fps, (width, height))

# Frame generation with progress bar
for frame_num in tqdm(range(total_frames), desc="Generating video"):
    seconds = frame_num / fps
    # Flash white for 1 second every 10 seconds, starting at second 10
    if int(seconds) % 10 == 9:
        frame = np.ones((height, width, 3), dtype=np.uint8) * 255  # White
    else:
        frame = np.zeros((height, width, 3), dtype=np.uint8)       # Black
    out.write(frame)

out.release()
print("done")
