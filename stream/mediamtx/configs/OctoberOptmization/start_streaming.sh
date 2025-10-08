#!/bin/bash

MEDIAMTX_PATH="./mediamtx_v1.15.1"
# MEDIAMTX_PATH = "./mediamtx_v1.15.1"
# MEDIAMTX_PATH = "./mediamtx_v1.13.1"

FFMPEG_PATH="./ffmpeg_6.1.1-3ubuntu5"
#FFMPEG_PATH='/usr/local/bin/ffmpeg'
export FFMPEG_PATH

exec "$MEDIAMTX_PATH" ./owl_x265.yaml
