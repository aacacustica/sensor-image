#!/bin/bash
set -euo pipefail

VENV_PATH="/root/venvs/tflite/bin/activate"
PROJECT_ROOT="/root/IoT_microphone_scripts-main"
SCRIPT_PATH="$PROJECT_ROOT/00_retrieve_audios/retrieve_audios.py"

echo "Launching script"
python3 "$SCRIPT_PATH" 