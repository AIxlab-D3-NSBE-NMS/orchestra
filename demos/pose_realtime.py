"""Realtime pose overlay demo using MediaPipe Tasks and OpenCV.

This script targets MediaPipe 0.10.x installs that expose the Tasks API
instead of the legacy `mediapipe.solutions` package.

Usage:
    uv run python prr/demos/pose_realtime.py --model /path/to/pose_landmarker.task
    uv run python prr/demos/pose_realtime.py --model ./models/pose_landmarker.task --camera 1
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode,
)


POSE_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 7),
    (0, 4),
    (4, 5),
    (5, 6),
    (6, 8),
    (9, 10),
    (11, 12),
    (11, 13),
    (13, 15),
    (15, 17),
    (15, 19),
    (15, 21),
    (17, 19),
    (12, 14),
    (14, 16),
    (16, 18),
    (16, 20),
    (16, 22),
    (18, 20),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (24, 26),
    (25, 27),
    (26, 28),
    (27, 29),
    (28, 30),
    (29, 31),
    (30, 32),
    (27, 31),
    (28, 32),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Overlay MediaPipe pose landmarks on a live OpenCV camera feed."
    )
    parser.add_argument(
        "--model",
        type=Path,
        required=True,
        help="Path to a MediaPipe pose landmarker .task model file.",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera index passed to cv2.VideoCapture (default: 0).",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Requested capture width (default: 1280).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Requested capture height (default: 720).",
    )
    parser.add_argument(
        "--min-detection-confidence",
        type=float,
        default=0.5,
        help="Minimum pose detection confidence (default: 0.5).",
    )
    parser.add_argument(
        "--min-presence-confidence",
        type=float,
        default=0.5,
        help="Minimum pose presence confidence (default: 0.5).",
    )
    parser.add_argument(
        "--min-tracking-confidence",
        type=float,
        default=0.5,
        help="Minimum pose tracking confidence (default: 0.5).",
    )
    parser.add_argument(
        "--num-poses",
        type=int,
        default=1,
        help="Maximum number of poses to track (default: 1).",
    )
    return parser.parse_args()


def draw_pose(frame, landmarks) -> None:
    height, width = frame.shape[:2]
    points = []

    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        visible = landmark.visibility >= 0.5 if hasattr(landmark, "visibility") else True
        present = landmark.presence >= 0.5 if hasattr(landmark, "presence") else True
        points.append((x, y, visible and present))

    for start_idx, end_idx in POSE_CONNECTIONS:
        if start_idx >= len(points) or end_idx >= len(points):
            continue
        x1, y1, ok1 = points[start_idx]
        x2, y2, ok2 = points[end_idx]
        if ok1 and ok2:
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2, cv2.LINE_AA)

    for x, y, ok in points:
        if ok:
            cv2.circle(frame, (x, y), 4, (0, 128, 255), -1, cv2.LINE_AA)


def create_landmarker(args: argparse.Namespace) -> PoseLandmarker:
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(args.model)),
        running_mode=VisionTaskRunningMode.IMAGE,
        num_poses=args.num_poses,
        min_pose_detection_confidence=args.min_detection_confidence,
        min_pose_presence_confidence=args.min_presence_confidence,
        min_tracking_confidence=args.min_tracking_confidence,
        output_segmentation_masks=False,
    )
    return PoseLandmarker.create_from_options(options)


def main() -> int:
    args = parse_args()

    if not args.model.is_file():
        print(f"Model file not found: {args.model}", file=sys.stderr)
        return 1

    cap = cv2.VideoCapture(args.camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        print(f"Could not open camera index {args.camera}.", file=sys.stderr)
        return 1

    try:
        landmarker = create_landmarker(args)
    except Exception as exc:
        print(f"Failed to create PoseLandmarker: {exc}", file=sys.stderr)
        cap.release()
        return 1

    with landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read frame from camera.", file=sys.stderr)
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = landmarker.detect(mp_image)

            for landmarks in result.pose_landmarks:
                draw_pose(frame, landmarks)

            cv2.putText(
                frame,
                "Press q to quit",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow("MediaPipe Pose Realtime", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

            time.sleep(0.001)

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
