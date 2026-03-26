#!/bin/bash
set -u
OUTPUT_DIR="/data/testvideo/"
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
    echo "${OUTPUT_DIR}/owl_camera_${timestamp}.mp4"
}
run_ffmpeg() {
    local output_file=$(get_output_file)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting FFmpeg recording to: $output_file" | tee -a "$LOG_FILE"
    ffmpeg -use_wallclock_as_timestamps 1 -f v4l2 -input_format nv12 -video_size 1920x1080 -i /dev/video0 -thread_queue_size 64 -bf 0 -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf:text='%{localtime\:%H\\%M\\%S}.%{localtime\:%3N}':x=0:y=0:fontsize=16:fontcolor=white:box=1:boxcolor=black,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf:text='Frame\:%{n}':x=0:y=16:fontsize=16:fontcolor=white:box=1:boxcolor=black" -c:v h264_nvenc -preset p1 -y "$output_file" 2>&1 | tee -a "$LOG_FILE"
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
