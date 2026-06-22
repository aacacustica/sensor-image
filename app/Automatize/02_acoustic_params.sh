#!/bin/bash
set -euo pipefail

VENV_PATH="/opt/noiseport/.venv/bin/activate"
PROJECT_ROOT="/opt/noiseport/app"
SCRIPT_PATH="$PROJECT_ROOT/02_acoustic_params/acoustic_params_optimized.py"

ARGS=()

source "$VENV_PATH"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

echo "Launching script at $(date)"
SECONDS=0
python "$SCRIPT_PATH" "${ARGS[@]}"
duration=$SECONDS
echo "Finished at $(date)"
echo "Execution time: ${duration} seconds"