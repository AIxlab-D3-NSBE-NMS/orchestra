#!/bin/bash
set -u

OUTPUT_DIR="/data/owl_and_webcam/"
LOG_FILE="${OUTPUT_DIR}/owl_camera.log"
RESTART_DELAY=2
MAX_RESTART_ATTEMPTS=0
RESTART_ATTEMPT=0

get_camera_device() {
    v4l2-ctl --list-devices | awk -v name="$1" '
        $0 ~ name { found=1; next }
        found && /\/dev\/video/ { print; next }
        found && !/\/dev\// { found=0 }
    ' | sort -t'o' -k2 -n | head -1 | tr -d '[:space:]'
}

INTEGRATED_CAM=$(get_camera_device "Integrated Camera")
OWL_CAM=$(get_camera_device "Meeting Owl")


BUS_DEVICE=$(lsusb | grep "2e43:0320" | awk '{print $2":"$4}' | tr -d ',')
echo "Bus and Device: $BUS_DEVICE"
ISERIAL=$(sudo lsusb -v -s $BUS_DEVICE 2>/dev/null | grep iSerial | awk '{print $3}')
echo "Device iSerial: $ISERIAL"

mkdir -p "$OUTPUT_DIR"
cleanup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Shutting down gracefully..." | tee -a "$LOG_FILE"
    exit 0
}
trap cleanup SIGINT SIGTERM
get_output_file() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    echo "${OUTPUT_DIR}/owl_camera_${ISERIAL}_${timestamp}.mkv"
}
run_ffmpeg() {
    local output_file=$(get_output_file)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting FFmpeg recording to: $output_file" | tee -a "$LOG_FILE"

    local cmd=(
        ffmpeg -hide_banner
        -f v4l2 -video_size 2560x1440 -input_format mjpeg -thread_queue_size 1024 -i "$OWL_CAM"
        -f pulse -thread_queue_size 1024 -i plughw:CARD=plus,DEV=0
        -bf 0
        -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf:text='%{localtime\:%H\\%M\\%S}.%{localtime\:%3N}':x=0:y=0:fontsize=16:fontcolor=white:box=1:boxcolor=black,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf:text='Frame\:%{n}':x=0:y=16:fontsize=16:fontcolor=white:box=1:boxcolor=black"
        -c:v h264_nvenc -preset p1 -c:a aac -b:a 128k
        -y "$output_file"
    )

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] FFmpeg command: ${cmd[*]}" | tee -a "$LOG_FILE"
    "${cmd[@]}" 2>&1 | tee -a "$LOG_FILE"
    return ${PIPESTATUS[0]}
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
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Re-capturing now..." | tee -a "$LOG_FILE"
        run_ffmpeg
        EXIT_CODE=$?
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] FFmpeg exited with code: $EXIT_CODE" | tee -a "$LOG_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting ${RESTART_DELAY}s before restart..." | tee -a "$LOG_FILE"
        sleep "$RESTART_DELAY"
    done
}
main
