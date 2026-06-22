#!/bin/bash
set -euo pipefail

VENV_PATH="/opt/noiseport/.venv/bin/activate"
PROJECT_ROOT="/opt/noiseport/app"
SCRIPT_PATH="$PROJECT_ROOT/03_inference/inference_tflite_optimized.py"

ARGS=(-w 1 -p "/root/data/audio" -s 5 -t 0.3)

# Activar entorno virtual
source "$VENV_PATH"

# Ir al root del proyecto
cd "$PROJECT_ROOT"

# Asegurar imports desde el root del repo
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

echo "Launching inference script at $(date)"
SECONDS=0

python "$SCRIPT_PATH" "${ARGS[@]}"

duration=$SECONDS
echo "Finished at $(date)"
echo "Execution time: ${duration} seconds"