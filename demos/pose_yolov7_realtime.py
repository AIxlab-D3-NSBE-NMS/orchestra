"""
Human Pose Detection using YOLOv7-Pose with OpenCV Webcam.

This demo needs both:
1. the YOLOv7 pose checkpoint, and
2. the YOLOv7 source tree, because the checkpoint unpickles classes from
   the original repository such as `models.yolo`.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import cv2
import numpy as np
import torch

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = SCRIPT_DIR / "yolov7-w6-pose.pt"
DEFAULT_YOLOV7_DIR = SCRIPT_DIR / "yolov7"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run YOLOv7 pose detection on a live webcam feed."
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help=f"Path to the YOLOv7 pose checkpoint (default: {DEFAULT_MODEL_PATH}).",
    )
    parser.add_argument(
        "--yolov7-dir",
        type=Path,
        default=DEFAULT_YOLOV7_DIR,
        help=(
            "Path to a YOLOv7 source checkout containing models/yolo.py "
            f"(default: {DEFAULT_YOLOV7_DIR})."
        ),
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
        help="Square inference size used for preprocessing (default: 640).",
    )
    parser.add_argument(
        "--conf-thresh",
        type=float,
        default=0.25,
        help="Confidence threshold for person detections (default: 0.25).",
    )
    parser.add_argument(
        "--no-download-source",
        action="store_true",
        help="Do not auto-download the YOLOv7 source tree if it is missing.",
    )
    return parser.parse_args()


def download_model(model_path: Path) -> None:
    """Download YOLOv7-pose model if not present."""
    url = "https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7-w6-pose.pt"
    print(f"Downloading YOLOv7-pose model to {model_path}...")
    urllib.request.urlretrieve(url, model_path)
    print("Download complete!")


def download_yolov7_source(target_dir: Path) -> Path:
    """Download the YOLOv7 source tree needed to unpickle the checkpoint."""
    url = "https://github.com/WongKinYiu/yolov7/archive/refs/heads/main.zip"
    print(f"Downloading YOLOv7 source to {target_dir}...")
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="yolov7_src_") as tmp_dir:
        archive_path = Path(tmp_dir) / "yolov7.zip"
        urllib.request.urlretrieve(url, archive_path)

        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(tmp_dir)

        extracted_root = Path(tmp_dir) / "yolov7-main"
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.move(str(extracted_root), str(target_dir))

    print("YOLOv7 source download complete!")
    return target_dir


def resolve_yolov7_dir(requested_dir: Path, allow_download: bool) -> Path:
    """Find or bootstrap a YOLOv7 checkout containing models/yolo.py."""
    candidates = [
        requested_dir,
        SCRIPT_DIR / "yolov7",
        Path.cwd() / "yolov7",
        SCRIPT_DIR.parent / "yolov7",
    ]

    for candidate in candidates:
        if (candidate / "models" / "yolo.py").is_file():
            return candidate.resolve()

    if allow_download:
        downloaded_dir = download_yolov7_source(requested_dir.resolve())
        if (downloaded_dir / "models" / "yolo.py").is_file():
            return downloaded_dir

    raise RuntimeError(
        "Could not find a YOLOv7 source checkout containing models/yolo.py. "
        "Pass --yolov7-dir /path/to/yolov7 or allow the script to download it."
    )


def prepare_yolov7_imports(yolov7_dir: Path) -> None:
    """Add the YOLOv7 repo root to sys.path so torch.load can import its classes."""
    yolov7_dir_str = str(yolov7_dir)
    if yolov7_dir_str not in sys.path:
        sys.path.insert(0, yolov7_dir_str)


def load_model(model_path: Path, device: torch.device):
    """Load YOLOv7-pose model."""
    if not model_path.exists():
        download_model(model_path)

    # weights_only=False required for YOLOv7 checkpoints (contains model architecture)
    # Only use this with trusted model sources
    model = torch.load(model_path, map_location=device, weights_only=False)

    if 'model' in model:
        model = model['model']
    model = model.float().eval()

    if device.type != 'cpu':
        model = model.half()

    return model


def get_pose_utils():
    """Import YOLOv7 pose helpers after the repo root has been added to sys.path."""
    from utils.general import non_max_suppression_kpt
    from utils.plots import output_to_keypoint, plot_one_box, plot_skeleton_kpts

    return non_max_suppression_kpt, output_to_keypoint, plot_one_box, plot_skeleton_kpts


def preprocess_frame(frame: np.ndarray, img_size: int = 640) -> tuple:
    """Preprocess frame for YOLOv7 inference."""
    h, w = frame.shape[:2]

    scale = min(img_size / h, img_size / w)
    new_h, new_w = int(h * scale), int(w * scale)

    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    padded = np.full((img_size, img_size, 3), 114, dtype=np.uint8)
    pad_h, pad_w = (img_size - new_h) // 2, (img_size - new_w) // 2
    padded[pad_h:pad_h + new_h, pad_w:pad_w + new_w] = resized

    img_tensor = padded[:, :, ::-1].transpose(2, 0, 1)
    img_tensor = np.ascontiguousarray(img_tensor)
    img_tensor = torch.from_numpy(img_tensor).float() / 255.0

    return img_tensor.unsqueeze(0), scale, (pad_w, pad_h)


def postprocess_predictions(predictions, scale: float, pad: tuple, conf_thresh: float = 0.25):
    """Convert YOLOv7 keypoint detections back to original frame coordinates."""
    if predictions is None or len(predictions) == 0:
        return []

    poses = []
    pad_w, pad_h = pad

    for det in predictions:
        if det is None or len(det) < 7:
            continue

        conf = float(det[6])
        if conf < conf_thresh:
            continue

        center_x = float(det[2])
        center_y = float(det[3])
        width = float(det[4])
        height = float(det[5])

        x1 = (center_x - width / 2 - pad_w) / scale
        y1 = (center_y - height / 2 - pad_h) / scale
        x2 = (center_x + width / 2 - pad_w) / scale
        y2 = (center_y + height / 2 - pad_h) / scale

        keypoints = []
        kpts = det[7:]
        for i in range(0, len(kpts), 3):
            if i + 2 >= len(kpts):
                break

            kx = (float(kpts[i]) - pad_w) / scale
            ky = (float(kpts[i + 1]) - pad_h) / scale
            kc = float(kpts[i + 2])
            keypoints.append((kx, ky, kc))

        poses.append({
            'bbox': (x1, y1, x2, y2),
            'confidence': conf,
            'keypoints': keypoints
        })

    return poses


def draw_poses(frame: np.ndarray, poses: list, plot_one_box, plot_skeleton_kpts) -> np.ndarray:
    """Render detections with YOLOv7's native plotting helpers."""
    output = frame.copy()

    for pose in poses:
        x1, y1, x2, y2 = pose["bbox"]
        label = f"Person {pose['confidence']:.2f}"
        plot_one_box([x1, y1, x2, y2], output, label=label, color=[0, 255, 0], line_thickness=2)

        keypoints = pose["keypoints"]
        if keypoints:
            flat_kpts = []
            for kx, ky, kc in keypoints:
                flat_kpts.extend((kx, ky, kc))
            plot_skeleton_kpts(output, flat_kpts, 3)

    return output


def main() -> int:
    args = parse_args()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    model_path = args.model.resolve()
    try:
        yolov7_dir = resolve_yolov7_dir(
            args.yolov7_dir,
            allow_download=not args.no_download_source,
        )
        prepare_yolov7_imports(yolov7_dir)
        non_max_suppression_kpt, output_to_keypoint, plot_one_box, plot_skeleton_kpts = get_pose_utils()
        model = load_model(model_path, device)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        return 1

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Error: Could not open webcam {args.camera}")
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break

        img_tensor, scale, pad = preprocess_frame(frame, img_size=args.img_size)
        img_tensor = img_tensor.to(device)

        if device.type != 'cpu':
            img_tensor = img_tensor.half()

        with torch.no_grad():
            predictions = model(img_tensor)

        raw_preds = predictions[0] if isinstance(predictions, (list, tuple)) else predictions
        preds = non_max_suppression_kpt(
            raw_preds,
            conf_thres=args.conf_thresh,
            iou_thres=0.65,
            nc=model.yaml["nc"],
            nkpt=model.yaml["nkpt"],
            kpt_label=True,
        )

        keypoint_output = output_to_keypoint(preds)
        poses = postprocess_predictions(keypoint_output, scale, pad, conf_thresh=args.conf_thresh)

        output_frame = draw_poses(frame, poses, plot_one_box, plot_skeleton_kpts)

        cv2.putText(output_frame, f"Poses detected: {len(poses)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('YOLOv7 Pose Detection', output_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
