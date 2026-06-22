#!/bin/bash
set -euo pipefail

VENV_PATH="/opt/noiseport/.venv/bin/activate"
PROJECT_ROOT="/opt/noiseport/app"
SCRIPT_PATH="$PROJECT_ROOT/00_retrieve_audios/retrieve_audios.py"

echo "Launching script"
python3 "$SCRIPT_PATH" 