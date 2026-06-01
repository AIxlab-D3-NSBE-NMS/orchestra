import argparse
import math
import shutil
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np
from deepface import DeepFace
from deepface.modules.exceptions import FaceNotDetected

try:
    from mediapipe.solutions import pose as mp_pose

    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    mp_pose = None


EMOTION_COLORS = {
    "angry": (0, 0, 255),
    "disgust": (115, 150, 232),
    "fear": (128, 0, 128),
    "happy": (0, 165, 0),
    "sad": (255, 0, 0),
    "surprise": (0, 255, 255),
    "neutral": (128, 128, 128),
}

EMOTION_ORDER = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


def update_ema(current_value, new_value, alpha=0.2):
    """Update an exponential moving average."""
    if current_value is None:
        return new_value
    return current_value * (1 - alpha) + new_value * alpha


def process_faces(image):
    """
    Process faces in the image for emotion detection.

    Returns:
        tuple: (faces_detected, emotions_data, inference_ms)
    """
    start_time = time.perf_counter()

    try:
        faces = DeepFace.extract_faces(image, enforce_detection=False)

        if not faces:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return False, None, elapsed_ms

        emotions_data = []

        for face in faces:
            facial_area = face["facial_area"]
            x = facial_area["x"]
            y = facial_area["y"]
            w = facial_area["w"]
            h = facial_area["h"]

            try:
                face_region = image[y : y + h, x : x + w]
                emotions = DeepFace.analyze(
                    face_region,
                    actions=["emotion"],
                    enforce_detection=False,
                )
                emotion_dict = emotions[0]["emotion"]

                emotions_data.append(
                    {
                        "coords": (x, y, w, h),
                        "emotions": emotion_dict,
                    }
                )
            except FaceNotDetected:
                continue
            except Exception as exc:
                print(f"Error analyzing emotion: {exc}")
                continue

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return len(emotions_data) > 0, emotions_data, elapsed_ms

    except FaceNotDetected:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return False, None, elapsed_ms
    except Exception as exc:
        print(f"Error in face detection: {exc}")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return False, None, elapsed_ms


def process_pose(image, pose_detector):
    """
    Process pose estimation on the image.

    Returns:
        tuple: (pose_detected, pose_landmarks, inference_ms)
    """
    if not MEDIAPIPE_AVAILABLE or pose_detector is None:
        return False, None, 0.0

    start_time = time.perf_counter()

    try:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose_detector.process(image_rgb)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        if results.pose_landmarks is None:
            return False, None, elapsed_ms

        return True, results.pose_landmarks, elapsed_ms

    except Exception as exc:
        print(f"Error in pose detection: {exc}")
        return False, None, 0.0


def draw_emotion_bars(
    overlay,
    x,
    y,
    w,
    h,
    emotions_dict,
    bar_width=100,
    bar_height=140,
    overlay_scale=1.0,
):
    """
    Draw emotion probability bars onto an overlay image.
    """
    bar_width = max(20, int(bar_width * overlay_scale))
    bar_height = max(28, int(bar_height * overlay_scale))
    margin = max(4, int(10 * overlay_scale))
    label_x_padding = max(2, int(3 * overlay_scale))
    border_thickness = max(1, int(round(overlay_scale)))
    font_scale = max(0.3, 0.35 * overlay_scale)
    font_thickness = max(1, int(round(overlay_scale)))

    img_height, img_width = overlay.shape[:2]

    bar_x = x + w + margin
    bar_y = y

    if bar_x + bar_width > img_width:
        bar_x = max(margin, x - bar_width - margin)
    if bar_y + bar_height > img_height:
        bar_y = max(margin, img_height - bar_height - margin)

    sorted_emotions = sorted(emotions_dict.items())
    num_emotions = len(sorted_emotions)

    if num_emotions == 0:
        return

    bar_spacing = bar_height / num_emotions
    bar_individual_height = max(10, int(bar_spacing * 0.85))

    for idx, (emotion_name, emotion_value) in enumerate(sorted_emotions):
        current_y = int(bar_y + idx * bar_spacing + (bar_spacing - bar_individual_height) / 2)
        bar_bottom = current_y + bar_individual_height

        cv2.rectangle(
            overlay,
            (bar_x, current_y),
            (bar_x + bar_width, bar_bottom),
            (40, 40, 40),
            -1,
        )
        cv2.rectangle(
            overlay,
            (bar_x, current_y),
            (bar_x + bar_width, bar_bottom),
            (200, 200, 200),
            border_thickness,
        )

        normalized_value = emotion_value / 100.0
        fill_width = int(normalized_value * bar_width)

        color = EMOTION_COLORS.get(emotion_name.lower(), (128, 128, 128))
        if fill_width > 0:
            cv2.rectangle(
                overlay,
                (bar_x, current_y),
                (bar_x + fill_width, bar_bottom),
                color,
                -1,
            )

        text_y = current_y + max(bar_individual_height - 2, int(10 * overlay_scale))
        cv2.putText(
            overlay,
            emotion_name.upper(),
            (bar_x + label_x_padding, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            font_thickness,
        )


def draw_pose(image, pose_landmarks, alpha_pose=0.7):
    """
    Draw pose skeleton on the image.
    """
    if not MEDIAPIPE_AVAILABLE or mp_pose is None or pose_landmarks is None:
        return image

    img_height, img_width = image.shape[:2]
    overlay = image.copy()

    for landmark in pose_landmarks.landmark:
        x = int(landmark.x * img_width)
        y = int(landmark.y * img_height)
        if landmark.visibility > 0.5:
            cv2.circle(overlay, (x, y), 4, (0, 255, 0), -1)
            cv2.circle(overlay, (x, y), 4, (255, 255, 255), 1)

    try:
        for start_idx, end_idx in mp_pose.POSE_CONNECTIONS:
            start = pose_landmarks.landmark[start_idx]
            end = pose_landmarks.landmark[end_idx]

            if start.visibility > 0.5 and end.visibility > 0.5:
                start_x = int(start.x * img_width)
                start_y = int(start.y * img_height)
                end_x = int(end.x * img_width)
                end_y = int(end.y * img_height)
                cv2.line(overlay, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
    except AttributeError:
        print("Warning: Could not access POSE_CONNECTIONS")

    cv2.addWeighted(overlay, alpha_pose, image, 1 - alpha_pose, 0, image)
    return image


def draw_overlays(image, emotions_data, alpha_bar=0.7, overlay_scale=1.0):
    """
    Draw bounding boxes and emotion bars on the image.
    """
    if emotions_data is None:
        return image

    overlay = image.copy()

    for face_data in emotions_data:
        x, y, w, h = face_data["coords"]
        emotions = face_data["emotions"]

        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), 2)
        draw_emotion_bars(
            overlay,
            x,
            y,
            w,
            h,
            emotions,
            overlay_scale=overlay_scale,
        )

    cv2.addWeighted(overlay, alpha_bar, image, 1 - alpha_bar, 0, image)
    return image


def compute_normalized_emotion_distribution(emotions_data):
    """Sum all detected subjects' emotion scores and normalize the total to 1.0."""
    if not emotions_data:
        return None

    totals = {}
    for face_data in emotions_data:
        emotions = face_data.get("emotions", {})
        for emotion_name, emotion_value in emotions.items():
            try:
                value = max(0.0, float(emotion_value))
            except (TypeError, ValueError):
                continue
            key = emotion_name.lower()
            totals[key] = totals.get(key, 0.0) + value

    total_score = sum(totals.values())
    if total_score <= 0.0:
        return None

    return {emotion_name: value / total_score for emotion_name, value in totals.items()}


def get_emotion_plot_names(history, current_distribution=None):
    """Return stable emotion names for plotting, preserving the canonical order."""
    emotion_names = set()
    if current_distribution:
        emotion_names.update(current_distribution.keys())
    for _, sample in history:
        emotion_names.update(sample.keys())

    ordered_names = [emotion for emotion in EMOTION_ORDER if emotion in emotion_names]
    ordered_names.extend(sorted(emotion_names - set(ordered_names)))
    return ordered_names or EMOTION_ORDER


def update_filtered_emotion_distribution(previous, target, dt, smoothing_s):
    """Move the displayed plot value toward the latest emotion result each frame."""
    target = target or {}
    emotion_names = set(EMOTION_ORDER)
    emotion_names.update(target.keys())
    if previous:
        emotion_names.update(previous.keys())

    if previous is None or smoothing_s <= 0.0:
        return {emotion_name: target.get(emotion_name, 0.0) for emotion_name in emotion_names}

    alpha = 1.0 - math.exp(-max(0.0, dt) / smoothing_s)
    return {
        emotion_name: (
            previous.get(emotion_name, 0.0) * (1.0 - alpha)
            + target.get(emotion_name, 0.0) * alpha
        )
        for emotion_name in emotion_names
    }


def prune_emotion_plot_history(history, now, history_seconds):
    """Keep only samples inside the requested real-time plot window."""
    cutoff = now - history_seconds
    while history and history[0][0] < cutoff:
        history.popleft()


def draw_emotion_timeseries_plot(
    image,
    history,
    now,
    history_seconds,
    plot_height=140,
    alpha=0.6,
    current_distribution=None,
):
    """Draw a rolling oscilloscope-style emotion probability plot at the bottom."""
    if plot_height <= 0 or len(history) < 2:
        return image

    img_height, img_width = image.shape[:2]
    plot_height = min(plot_height, max(40, img_height - 50))
    plot_y = img_height - plot_height
    padding_top = 18
    padding_bottom = 12
    graph_top = plot_y + padding_top
    graph_bottom = img_height - padding_bottom
    graph_height = max(1, graph_bottom - graph_top)

    overlay = image.copy()
    cv2.rectangle(overlay, (0, plot_y), (img_width, img_height), (15, 15, 15), -1)

    for fraction in (0.25, 0.5, 0.75):
        y = int(graph_bottom - fraction * graph_height)
        cv2.line(overlay, (0, y), (img_width, y), (70, 70, 70), 1)

    cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)

    emotion_names = get_emotion_plot_names(history, current_distribution)
    time_start = now - history_seconds

    for emotion_name in emotion_names:
        color = EMOTION_COLORS.get(emotion_name, (220, 220, 220))
        points = []
        for sample_time, sample in history:
            value = max(0.0, min(float(sample.get(emotion_name, 0.0)), 1.0))
            elapsed_fraction = (sample_time - time_start) / history_seconds
            x = int(max(0.0, min(elapsed_fraction, 1.0)) * (img_width - 1))
            y = int(graph_bottom - value * graph_height)
            points.append((x, y))

        if len(points) >= 2:
            cv2.polylines(image, [np.array(points, dtype=np.int32)], False, color, 2)

    legend_x = 8
    legend_y = plot_y + 13
    for emotion_name in emotion_names:
        color = EMOTION_COLORS.get(emotion_name, (220, 220, 220))
        value = 0.0 if current_distribution is None else current_distribution.get(emotion_name, 0.0)
        label = f"{emotion_name[:3].upper()} {value * 100:4.1f}"
        cv2.putText(
            image,
            label,
            (legend_x, legend_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            color,
            1,
            cv2.LINE_AA,
        )
        legend_x += 72
        if legend_x > img_width - 70:
            legend_x = 8
            legend_y += 14

    return image


def resolve_media_path(media_path):
    """Validate an optional media path for ffplay playback."""
    if media_path is None:
        return None

    path = Path(media_path).expanduser()
    if not path.is_file():
        print(f"Warning: media path is not a file: {path}")
        return None

    if shutil.which("ffplay") is None:
        print("Warning: ffplay is not available on PATH")
        return None

    print(f"Media playback ready: {path}")
    return path


def start_media_player(media_path):
    """Start ffplay for the configured media file."""
    if media_path is None:
        print("No media video loaded")
        return None

    return subprocess.Popen(
        ["ffplay", "-autoexit", "-loglevel", "error", str(media_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def stop_media_player(media_process):
    """Stop a running ffplay process."""
    if media_process is None or media_process.poll() is not None:
        return None

    media_process.terminate()
    try:
        media_process.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        media_process.kill()
        media_process.wait(timeout=1.0)

    return None


def emotion_worker_loop(shared_state, state_lock, stop_event):
    """Run DeepFace emotion inference in the background on the latest submitted frame."""
    last_processed_frame_id = -1

    while not stop_event.is_set():
        frame = None
        frame_id = -1

        with state_lock:
            submitted_frame = shared_state["submitted_frame"]
            submitted_frame_id = shared_state["submitted_frame_id"]
            emotion_interval_s = shared_state["emotion_interval_s"]

            if submitted_frame is not None and submitted_frame_id != last_processed_frame_id:
                frame = submitted_frame.copy()
                frame_id = submitted_frame_id

        if frame is None:
            stop_event.wait(0.01)
            continue

        faces_detected, emotions_data, inference_ms = process_faces(frame)
        completed_at = time.monotonic()

        with state_lock:
            shared_state["emotion_inference_ms_ema"] = update_ema(
                shared_state["emotion_inference_ms_ema"],
                inference_ms,
            )
            shared_state["emotion_updates"] += 1
            shared_state["last_emotion_completed_at"] = completed_at

            if faces_detected and emotions_data:
                shared_state["last_emotions_data"] = emotions_data
                shared_state["last_emotion_result_at"] = completed_at

        last_processed_frame_id = frame_id
        stop_event.wait(emotion_interval_s)


def main():
    parser = argparse.ArgumentParser(
        description="Real-time facial recognition, emotion detection, and pose estimation"
    )
    parser.add_argument(
        "--skipframes",
        type=int,
        default=1,
        help="Number of frames to skip between emotion submissions (default: 1)",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera device index (default: 0)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Target frames per second (default: 30)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="Frame width (default: 640)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="Frame height (default: 480)",
    )
    parser.add_argument(
        "--alpha-bar",
        type=float,
        default=0.7,
        help="Opacity of emotion bars (0.0-1.0, default: 0.7)",
    )
    parser.add_argument(
        "--alpha-pose",
        type=float,
        default=0.7,
        help="Opacity of pose skeleton (0.0-1.0, default: 0.7)",
    )
    parser.add_argument(
        "--enable-pose",
        action="store_true",
        default=False,
        help="Enable pose estimation (default: disabled for faster processing)",
    )
    parser.add_argument(
        "--skip-pose-frames",
        type=int,
        default=1,
        help="Number of frames to skip for pose processing checks (default: 1)",
    )
    parser.add_argument(
        "--emotion-overlay-scale",
        type=float,
        default=1.0,
        help="Visual scale factor for emotion bar overlays (default: 1.0)",
    )
    parser.add_argument(
        "--emotion-fps",
        type=float,
        default=6.0,
        help="Maximum rate for emotion inference updates (default: 6.0)",
    )
    parser.add_argument(
        "--pose-fps",
        type=float,
        default=10.0,
        help="Maximum rate for pose inference updates when enabled (default: 10.0)",
    )
    parser.add_argument(
        "--emotion-ttl",
        type=float,
        default=1.0,
        help="How long to keep the last emotion overlay visible in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--pose-ttl",
        type=float,
        default=0.5,
        help="How long to keep the last pose overlay visible in seconds (default: 0.5)",
    )
    parser.add_argument(
        "--hide-emotion-plot",
        action="store_true",
        default=False,
        help="Hide the rolling emotion probability plot at the bottom",
    )
    parser.add_argument(
        "--emotion-plot-height",
        type=int,
        default=140,
        help="Height of the rolling emotion probability plot in pixels (default: 140)",
    )
    parser.add_argument(
        "--emotion-plot-history",
        type=float,
        default=12.0,
        help="Visible history window for the rolling emotion plot in seconds (default: 12.0)",
    )
    parser.add_argument(
        "--emotion-plot-alpha",
        type=float,
        default=0.6,
        help="Opacity of the emotion plot background (0.0-1.0, default: 0.6)",
    )
    parser.add_argument(
        "--emotion-plot-smoothing",
        type=float,
        default=0.35,
        help=(
            "EMA response time for the emotion plot in seconds; "
            "use 0 to disable filtering (default: 0.35)"
        ),
    )
    parser.add_argument(
        "--media",
        type=str,
        default=None,
        help="Optional path to a media file to play with ffplay when pressing 'v'",
    )

    args = parser.parse_args()

    if not 0.0 <= args.alpha_bar <= 1.0:
        print("Warning: alpha_bar should be between 0.0 and 1.0. Using default 0.7")
        args.alpha_bar = 0.7

    if not 0.0 <= args.alpha_pose <= 1.0:
        print("Warning: alpha_pose should be between 0.0 and 1.0. Using default 0.7")
        args.alpha_pose = 0.7

    if args.emotion_overlay_scale <= 0.0:
        print("Warning: emotion_overlay_scale should be greater than 0. Using default 1.0")
        args.emotion_overlay_scale = 1.0

    if args.emotion_fps <= 0.0:
        print("Warning: emotion_fps should be greater than 0. Using default 6.0")
        args.emotion_fps = 6.0

    if args.pose_fps <= 0.0:
        print("Warning: pose_fps should be greater than 0. Using default 10.0")
        args.pose_fps = 10.0

    if args.emotion_ttl < 0.0:
        print("Warning: emotion_ttl should be non-negative. Using default 1.0")
        args.emotion_ttl = 1.0

    if args.pose_ttl < 0.0:
        print("Warning: pose_ttl should be non-negative. Using default 0.5")
        args.pose_ttl = 0.5

    if args.emotion_plot_height < 0:
        print("Warning: emotion_plot_height should be non-negative. Using default 140")
        args.emotion_plot_height = 140

    if args.emotion_plot_history <= 0.0:
        print("Warning: emotion_plot_history should be greater than 0. Using default 12.0")
        args.emotion_plot_history = 12.0

    if not 0.0 <= args.emotion_plot_alpha <= 1.0:
        print("Warning: emotion_plot_alpha should be between 0.0 and 1.0. Using default 0.6")
        args.emotion_plot_alpha = 0.6

    if args.emotion_plot_smoothing < 0.0:
        print("Warning: emotion_plot_smoothing should be non-negative. Using default 0.35")
        args.emotion_plot_smoothing = 0.35

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Error: Could not open camera device {args.camera}")
        return

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, args.fps)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)

    if actual_width != args.width or actual_height != args.height:
        print(
            f"Warning: Requested resolution {args.width}x{args.height} "
            f"but camera returned {actual_width}x{actual_height}"
        )
    else:
        print(f"Camera resolution set to {actual_width}x{actual_height}")

    if actual_fps != args.fps:
        print(f"Note: Requested FPS {args.fps} but camera set to {actual_fps:.1f}")

    media_path = resolve_media_path(args.media)
    media_process = None

    pose_detector = None
    if args.enable_pose:
        if not MEDIAPIPE_AVAILABLE:
            print("Error: MediaPipe is required for pose estimation. Install with: pip install mediapipe")
            args.enable_pose = False
        else:
            pose_detector = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            print(f"Pose estimation enabled (skip frames: {args.skip_pose_frames})")

    frame_delay = int(1000 / args.fps)
    emotion_interval_s = 1.0 / args.emotion_fps
    pose_interval_s = 1.0 / args.pose_fps

    frame_count = 0
    start_time = time.time()
    emotion_updates = 0
    pose_count = 0
    last_pose_landmarks = None
    last_pose_result_at = None
    pose_inference_ms_ema = None
    last_emotion_submit_at = 0.0
    last_pose_process_at = 0.0
    emotion_plot_history = deque()
    filtered_emotion_distribution = None
    last_plot_update_at = time.monotonic()

    state_lock = threading.Lock()
    stop_event = threading.Event()
    shared_state = {
        "submitted_frame": None,
        "submitted_frame_id": -1,
        "emotion_interval_s": emotion_interval_s,
        "last_emotions_data": None,
        "last_emotion_result_at": None,
        "last_emotion_completed_at": None,
        "emotion_inference_ms_ema": None,
        "emotion_updates": 0,
    }
    emotion_thread = threading.Thread(
        target=emotion_worker_loop,
        args=(shared_state, state_lock, stop_event),
        daemon=True,
    )
    emotion_thread.start()

    print("Starting real-time emotion detection and pose estimation...")
    print(f"Skip frames (emotion submit): {args.skipframes}")
    print(f"Target FPS: {args.fps}")
    print(f"Emotion update rate: {args.emotion_fps:.1f} Hz")
    print(f"Emotion result TTL: {args.emotion_ttl:.2f} s")
    print(f"Emotion bar opacity: {args.alpha_bar}")
    print(f"Emotion overlay scale: {args.emotion_overlay_scale}")
    if not args.hide_emotion_plot:
        print(f"Emotion plot history: {args.emotion_plot_history:.1f} s")
        print(f"Emotion plot height: {args.emotion_plot_height} px")
        print(f"Emotion plot smoothing: {args.emotion_plot_smoothing:.2f} s")
    if args.enable_pose:
        print(f"Pose update rate: {args.pose_fps:.1f} Hz")
        print(f"Pose result TTL: {args.pose_ttl:.2f} s")
        print(f"Pose skeleton opacity: {args.alpha_pose}")
    print("Press 'q' to quit, 'p' to toggle pose, 'v' to toggle media video")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to read frame from camera")
                break

            now = time.monotonic()

            should_submit_emotion = (
                frame_count % args.skipframes == 0
                and (now - last_emotion_submit_at) >= emotion_interval_s
            )
            if should_submit_emotion:
                with state_lock:
                    shared_state["submitted_frame"] = frame.copy()
                    shared_state["submitted_frame_id"] += 1
                last_emotion_submit_at = now

            should_process_pose = (
                args.enable_pose
                and pose_detector is not None
                and frame_count % args.skip_pose_frames == 0
                and (now - last_pose_process_at) >= pose_interval_s
            )
            if should_process_pose:
                pose_detected, pose_landmarks, pose_inference_ms = process_pose(frame, pose_detector)
                pose_inference_ms_ema = update_ema(pose_inference_ms_ema, pose_inference_ms)
                last_pose_process_at = now

                if pose_detected and pose_landmarks is not None:
                    last_pose_landmarks = pose_landmarks
                    last_pose_result_at = now
                    pose_count += 1

            with state_lock:
                last_emotions_data = shared_state["last_emotions_data"]
                last_emotion_result_at = shared_state["last_emotion_result_at"]
                emotion_inference_ms_ema = shared_state["emotion_inference_ms_ema"]
                emotion_updates = shared_state["emotion_updates"]

            current_emotion_distribution = None
            if (
                last_emotions_data is not None
                and last_emotion_result_at is not None
                and (now - last_emotion_result_at) <= args.emotion_ttl
            ):
                current_emotion_distribution = compute_normalized_emotion_distribution(
                    last_emotions_data
                )
                frame = draw_overlays(
                    frame,
                    last_emotions_data,
                    alpha_bar=args.alpha_bar,
                    overlay_scale=args.emotion_overlay_scale,
                )

            if (
                args.enable_pose
                and last_pose_landmarks is not None
                and last_pose_result_at is not None
                and (now - last_pose_result_at) <= args.pose_ttl
            ):
                frame = draw_pose(frame, last_pose_landmarks, alpha_pose=args.alpha_pose)

            plot_dt = now - last_plot_update_at
            last_plot_update_at = now
            filtered_emotion_distribution = update_filtered_emotion_distribution(
                filtered_emotion_distribution,
                current_emotion_distribution,
                plot_dt,
                args.emotion_plot_smoothing,
            )
            emotion_plot_history.append((now, filtered_emotion_distribution))
            prune_emotion_plot_history(emotion_plot_history, now, args.emotion_plot_history)

            if not args.hide_emotion_plot:
                frame = draw_emotion_timeseries_plot(
                    frame,
                    emotion_plot_history,
                    now,
                    args.emotion_plot_history,
                    plot_height=args.emotion_plot_height,
                    alpha=args.emotion_plot_alpha,
                    current_distribution=filtered_emotion_distribution,
                )

            elapsed = time.time() - start_time
            if elapsed > 0:
                fps = frame_count / elapsed
                emotion_ms_text = "--" if emotion_inference_ms_ema is None else f"{emotion_inference_ms_ema:.0f}"
                status_text = f"FPS: {fps:.1f} | Emotion updates: {emotion_updates} | Emotion ms: {emotion_ms_text}"
                if args.enable_pose:
                    pose_ms_text = "--" if pose_inference_ms_ema is None else f"{pose_inference_ms_ema:.0f}"
                    status_text += f" | Poses: {pose_count} | Pose ms: {pose_ms_text}"

                cv2.putText(
                    frame,
                    status_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

            cv2.imshow("Emotion Detection & Pose Estimation - Press Q to Quit", frame)

            key = cv2.waitKey(frame_delay) & 0xFF
            if key == ord("q"):
                break
            if key == ord("p"):
                if MEDIAPIPE_AVAILABLE:
                    args.enable_pose = not args.enable_pose
                    if args.enable_pose and pose_detector is None:
                        pose_detector = mp_pose.Pose(
                            static_image_mode=False,
                            model_complexity=1,
                            smooth_landmarks=True,
                            min_detection_confidence=0.5,
                            min_tracking_confidence=0.5,
                        )
                        print("Pose estimation enabled")
                    elif not args.enable_pose:
                        print("Pose estimation disabled")
                else:
                    print("MediaPipe not available")
            if key == ord("v"):
                if media_path is not None:
                    if media_process is None or media_process.poll() is not None:
                        media_process = start_media_player(media_path)
                        print("Media playback started")
                    else:
                        media_process = stop_media_player(media_process)
                        print("Media playback stopped")
                else:
                    print("No media video loaded")

            frame_count += 1

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as exc:
        print(f"Error: {exc}")
    finally:
        stop_event.set()
        emotion_thread.join(timeout=1.0)
        media_process = stop_media_player(media_process)
        cap.release()
        cv2.destroyAllWindows()

        if pose_detector:
            pose_detector.close()

        elapsed = time.time() - start_time
        print("\nSession Statistics:")
        print(f"Total frames: {frame_count}")
        print(f"Emotion updates: {emotion_updates}")
        if shared_state["emotion_inference_ms_ema"] is not None:
            print(f"Average emotion inference (EMA): {shared_state['emotion_inference_ms_ema']:.1f} ms")
        if args.enable_pose:
            print(f"Pose detections: {pose_count}")
            if pose_inference_ms_ema is not None:
                print(f"Average pose inference (EMA): {pose_inference_ms_ema:.1f} ms")
        print(f"Duration: {elapsed:.1f} seconds")
        if elapsed > 0:
            print(f"Average FPS: {frame_count / elapsed:.1f}")


if __name__ == "__main__":
    main()
# uv run emot_realtime.py --width 1920 --height 1080 --emotion-overlay-scale 2 --emotion-fps 5 --emotion-ttl 1.2 --camera 0 --emotion-plot-height 180 --emotion-plot-history 20 --emotion-plot-smoothing 2 --media "/home/labadmin/aixlab/outreach/Baby Laughing Hysterically at Ripping Paper (Original).mp4"
