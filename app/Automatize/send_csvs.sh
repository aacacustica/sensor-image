#!/bin/sh

SENSOR_NAME=$(hostname)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

source /opt/noiseport/config/sensor.env

if [ "$USE_PROXY" = "true" ]; then
    PROXY="$HTTP_PROXY"
else
    PROXY=""
fi

DATA_DIR="/root/data"

send_file() {
    f="$1"
    subpath="$2"
    base="$(basename "$f")"
    server="${SERVER_BASE}/${subpath}"

    python3 - "$f" "$base" "$server" "$PROXY" <<'PY'
import sys
import urllib.request
from urllib.parse import quote

fpath, base, server, proxy = sys.argv[1:]

url = f"{server}?name={quote(base)}"

with open(fpath, "rb") as fh:
    data = fh.read()

req = urllib.request.Request(url, data=data, method="POST")

req.add_header("X-Filename", base)
req.add_header("Connection", "close")
req.add_header("Proxy-Connection", "close")
req.add_header("Content-Type", "application/octet-stream")

if proxy:
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    )
else:
    # Fuerza NO usar proxy, ni siquiera variables de entorno
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({})
    )

with opener.open(req, timeout=60) as resp:
    if resp.status != 200:
        raise RuntimeError(f"HTTP {resp.status}")
PY
}

send_dir() {
    DIR="$1"
    SUBPATH="$2"

    for f in "$DIR"/*.csv
    do
        [ -f "$f" ] || continue

        base=$(basename "$f")

        # Extraer fecha automáticamente 
        fecha=$(echo "$base" | grep -oE '[0-9]{8}' | head -n1)

        destino="${SENSOR_NAME}/${SUBPATH}/${fecha}"

        if send_file "$f" "$destino"; then
            rm "$f"
        else
            echo "Error sending $f" >&2
        fi
    done
}

send_dir "$DATA_DIR/acoustic_params" "acoustics"
send_dir "$DATA_DIR/prediction_files" "predictions"

# Opcional: envío de un wav aleatorio
#wav_random=$(find /root/data/NOISEPORT-TENERIFE/3-Medidas/P1_CONTENEDORES/AUDIOMOTH/wav_files -type f -name '*.wav' | shuf -n 1)
#[ -n "$wav_random" ] && send_file "$wav_random" "wav"