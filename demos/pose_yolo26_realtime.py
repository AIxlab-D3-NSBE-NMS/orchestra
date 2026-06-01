"""
Realtime pose detection demo for Ultralytics pose models such as yolo26n-pose.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import torch
from ultralytics import YOLO


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = SCRIPT_DIR / "models" / "yolo26n-pose.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an Ultralytics pose model on a live webcam feed."
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help=f"Path to the Ultralytics pose checkpoint (default: {DEFAULT_MODEL_PATH}).",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera index passed to cv2.VideoCapture (default: 0).",
    )
    parser.add_argument(
        "--img-size",
        type=int,
        default=640,
        help="Inference image size (default: 640).",
    )
    parser.add_argument(
        "--conf-thresh",
        type=float,
        default=0.25,
        help="Confidence threshold for detections (default: 0.25).",
    )
    return parser.parse_args()


def load_model(model_path: Path, device: torch.device) -> YOLO:
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = YOLO(str(model_path))
    model.to("cuda" if device.type == "cuda" else "cpu")
    return model


def run_inference(model: YOLO, frame, args: argparse.Namespace, device: torch.device):
    device_arg = 0 if device.type == "cuda" else "cpu"
    results = model.predict(
        source=frame,
        conf=args.conf_thresh,
        imgsz=args.img_size,
        device=device_arg,
        verbose=False,
    )
    result = results[0]
    rendered = result.plot()
    pose_count = 0 if result.boxes is None else len(result.boxes)
    return rendered, pose_count


def main() -> int:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    try:
        model = load_model(args.model.resolve(), device)
        print("Model loaded successfully!")
    except Exception as exc:
        print(f"Error loading model: {exc}")
        return 1

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Error: Could not open webcam {args.camera}")
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Press 'q' to quit")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Error: Could not read frame")
            break

        output_frame, pose_count = run_inference(model, frame, args, device)

        cv2.putText(
            output_frame,
            f"Poses detected: {pose_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        cv2.imshow("YOLO26 Pose Detection", output_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
