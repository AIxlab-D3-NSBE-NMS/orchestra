#!/bin/bash
set -u
OUTPUT_DIR="/data/2026_03_12/"
LOG_FILE="${OUTPUT_DIR}/owl_camera.log"
RESTART_DELAY=2
MAX_RESTART_ATTEMPTS=0
RESTART_ATTEMPT=0
mkdir -p "$OUTPUT_DIR"
cleanup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Shutting down gracefully..." | tee -a "$LOG_FILE"
    exit 0
}
trap cleanup SIGINT SIGTERM
get_output_file() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    echo "${OUTPUT_DIR}/owl_camera_${timestamp}.mkv"
}
run_ffmpeg() {
    local output_file=$(get_output_file)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting FFmpeg recording to: $output_file" | tee -a "$LOG_FILE"
    ffmpeg -use_wallclock_as_timestamps 1 -f v4l2 -input_format mjpeg -video_size 3840x2160 -i /dev/video0 -f pulse -thread_queue_size 64 -i alsa_input.usb-Owl_Labs__Inc._Meeting_Owl_4_Plus.analog-stereo -map 0:v:0 -map 1:a:0 -c:v h264_nvenc  -preset p1  -b:v 50M  -maxrate 50M  -bufsize 100M  -bf 0 -c:a aac -b:a 128k -ar 48000  -ac 2 -y "$output_file" 2>&1 | tee -a "$LOG_FILE"
    return $?
}
main() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Owl Camera Recorder started" | tee -a "$LOG_FILE"
    while true; do
        if [ "$MAX_RESTART_ATTEMPTS" -gt 0 ] && [ "$RESTART_ATTEMPT" -ge "$MAX_RESTART_ATTEMPTS" ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Max restart attempts ($MAX_RESTART_ATTEMPTS) reached. Exiting." | tee -a "$LOG_FILE"
            exit 1
        fi
        RESTART_ATTEMPT=$((RESTART_ATTEMPT + 1))
        if [ "$MAX_RESTART_ATTEMPTS" -eq 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Recording attempt #$RESTART_ATTEMPT (unlimited)" | tee -a "$LOG_FILE"
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Recording attempt #$RESTART_ATTEMPT/$MAX_RESTART_ATTEMPTS" | tee -a "$LOG_FILE"
        fi
        run_ffmpeg
        EXIT_CODE=$?
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] FFmpeg exited with code: $EXIT_CODE" | tee -a "$LOG_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting ${RESTART_DELAY}s before restart..." | tee -a "$LOG_FILE"
        sleep "$RESTART_DELAY"
    done
}
main
