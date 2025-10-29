from csv import DictReader
import matplotlib
# matplotlib.use("qtagg")
matplotlib.use("tkagg")
import matplotlib.pyplot as plt
import cv2
import numpy as np
from tqdm import tqdm
import numpy as np
import random

# Video settings
DRY_RUN = False
width, height = 640, 480
fps = 30
duration_seconds = 15*60  # used to be 2*60*60 for a 2 hour video
total_frames = duration_seconds * fps
flash_interval = 10

ekman_en_pt = [('anger',    'raiva'),
               ('disgust',  'nojo'),
               ('sadness',  'tristeza'),
               ('surprise', 'surpresa'),
               ('happiness','alegria'),
               ('fear',     'medo'),
               ('contempt', 'desprezo')]
emoseq = random.choices(ekman_en_pt, k=duration_seconds // flash_interval)
flash_occurences = 0
state_white = False

# Output video writer
if not DRY_RUN:
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('/home/labadmin/Desktop/black_white_ekman7.avi', fourcc, fps, (width, height))

# Frame generation with progress bar
for frame_num in tqdm(range(total_frames), desc="Generating video"):
    seconds = frame_num / fps
    # Flash white for 1 second every 10 seconds, starting at second 10
    if int(seconds) % 10 == 9:
        frame = np.ones((height, width, 3), dtype=np.uint8) * 255  # White
        if state_white is False:
            flash_occurences += 1
            state_white = True
        en_txt_width = cv2.getTextSize(str.upper(emoseq[0][0]), cv2.FONT_HERSHEY_SIMPLEX, 2, 2)[0][0]
        pt_txt_width = cv2.getTextSize(str.upper(emoseq[0][1]), cv2.FONT_HERSHEY_SIMPLEX, 2, 2)[0][0]
        cv2.putText(frame, # img
                    str.upper(emoseq[flash_occurences-1][0]), # text
                    ((width-en_txt_width)//2, 170),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (0, 0, 0),
                    thickness=2)
        cv2.putText(frame,  # img
                    str.upper(emoseq[flash_occurences-1][1]),  # text
                    ((width-pt_txt_width)//2, 280),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (0, 0, 0),
                    thickness=2)
        a_white_frame = frame
    else:
        frame = np.zeros((height, width, 3), dtype=np.uint8)       # Black
        state_white = False
    if not DRY_RUN:
        out.write(frame)

if not DRY_RUN:
    out.release()
print(flash_occurences)
print("done")
plt.imshow(a_white_frame)
plt.show()

