#!/bin/bash

# Owl Camera Recording with Auto-Restart
# Restarts FFmpeg automatically if it crashes

set -u

# Configuration
OUTPUT_DIR="/data/videotest/"
LOG_FILE="${OUTPUT_DIR}/owl_camera.log"
PID_FILE="${OUTPUT_DIR}/.owl_camera.pid"
RESTART_DELAY=2
MAX_RESTART_ATTEMPTS=0  # 0 = unlimited
RESTART_ATTEMPT=0

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Cleanup function
cleanup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Shutting down gracefully..." | tee -a "$LOG_FILE"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill -TERM "$PID"
            sleep 2
            if kill -0 "$PID" 2>/dev/null; then
                kill -9 "$PID"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    exit 0
}

# Set trap for graceful shutdown
trap cleanup SIGINT SIGTERM

# Generate output filename with timestamp
get_output_file() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    echo "${OUTPUT_DIR}/owl_camera_${timestamp}.mp4"
}

# Main recording function
run_ffmpeg() {
    local output_file=$(get_output_file)
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting FFmpeg recording to: $output_file" | tee -a "$LOG_FILE"
    
    ffmpeg \
      -use_wallclock_as_timestamps 1 \
      -f v4l2 \
      -input_format nv12 \
      -i /dev/video0 \
      -video_size 1920x1080 \
      -thread_queue_size 64 \
      -framerate 30 \
      -bf 0 \
      -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf:text='%{localtime\:%H\\%M\\%S}.%{localtime\:%3N}':x=0:y=0:fontsize=16:fontcolor=white:box=1:boxcolor=black,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf:text='Frame\:%{n}':x=0:y=16:fontsize=16:fontcolor=white:box=1:boxcolor=black"
      -c:v h264_nvenc \
      -preset p1 \
      -y \
      "$output_file" 2>&1 | tee -a "$LOG_FILE"
    
    return $?
}

# Main loop
main() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Owl Camera Recorder started" | tee -a "$LOG_FILE"
    
    while true; do
        # Check restart attempt limit
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
        
        # Run FFmpeg
        run_ffmpeg
        EXIT_CODE=$?
        
        # Log the exit
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] FFmpeg exited with code: $EXIT_CODE" | tee -a "$LOG_FILE"
        
        # Wait before restarting
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting ${RESTART_DELAY}s before restart..." | tee -a "$LOG_FILE"
        sleep "$RESTART_DELAY"
    done
}

# Run main function
main
