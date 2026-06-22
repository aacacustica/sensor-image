#!/bin/bash
set -euo pipefail

VENV_PATH="/opt/noiseport/.venv/bin/activate"
PROJECT_ROOT="/opt/noiseport/app"
SCRIPT_PATH="$PROJECT_ROOT/01_recording/record_audio.py"
CODEC_PATH="$PROJECT_ROOT/activarcodec.sh"

# args en array (mejor que string)
ARGS=(-t 60)

echo "Activating venv"
source "$VENV_PATH"
cd "$PROJECT_ROOT"

echo "Activating audio codec"
bash "$CODEC_PATH"
echo "Launching script"
python3 "$SCRIPT_PATH" "${ARGS[@]}"