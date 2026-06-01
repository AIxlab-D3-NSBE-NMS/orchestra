#!/bin/bash
cd "$(dirname "$0")"
source ~/.bashrc
pkill mediamtx
pkill evince
pkill chrome
rm -rf ~/.cache/evince
cd /home/participant/aixlab/orchestra
source /home/participant/aixlab/orchestra/.venv/bin/activate && python /home/participant/aixlab/orchestra/prr_experiments/garden.py
