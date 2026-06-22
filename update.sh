#!/bin/sh
set -e

INSTALL_DIR="/opt/noiseport"
APP_DIR="$INSTALL_DIR/app"
CONFIG_DIR="$INSTALL_DIR/config"
WHEELS_DIR="$INSTALL_DIR/wheels"
DATA_DIR="/root/data"
VENV_DIR="$INSTALL_DIR/.venv"

echo "=== Actualización noiseport ==="

if [ "$(id -u)" != "0" ]; then
    echo "ERROR: ejecuta este script como root."
    exit 1
fi

echo "[1/7] Actualizando repositorio local"
git pull || true

echo "[2/7] Actualizando aplicación..."
rm -rf "$APP_DIR"
cp -r app "$APP_DIR"

echo "[3/7] Actualizando configuración versionada"
mkdir -p "$CONFIG_DIR"

if [ -d config ]; then
    for file in config/*; do
        [ -f "$file" ] || continue
        base="$(basename "$file")"

        case "$base" in
            sensor.env|config.yaml)
                echo "No sobrescribo config real: $base"
                ;;
            *)
                cp "$file" "$CONFIG_DIR/"
                ;;
        esac
    done
fi

if [ ! -f "$CONFIG_DIR/sensor.env" ] && [ -f "$CONFIG_DIR/sensor.env.example" ]; then
    cp "$CONFIG_DIR/sensor.env.example" "$CONFIG_DIR/sensor.env"
fi

if [ ! -f "$CONFIG_DIR/config.yaml" ] && [ -f "$CONFIG_DIR/config.yaml.example" ]; then
    cp "$CONFIG_DIR/config.yaml.example" "$CONFIG_DIR/config.yaml"
fi

ln -sfn "$CONFIG_DIR/config.yaml" "$APP_DIR/config.yaml"

echo "[4/7] Actualizando wheels y requirements..."
rm -rf "$WHEELS_DIR"
mkdir -p "$WHEELS_DIR"

if [ -d wheels ]; then
    cp -r wheels/* "$WHEELS_DIR/" 2>/dev/null || true
fi

cp requirements.txt "$INSTALL_DIR/requirements.txt"

echo "[5/7] Actualizando entorno virtual"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

. "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip

python -m pip install \
    --find-links "$WHEELS_DIR" \
    --default-timeout=100 \
    --no-cache-dir \
    -r "$INSTALL_DIR/requirements.txt"

SITE_PACKAGES="$(python -c 'import site; print(site.getsitepackages()[0])')"

for so_file in "$WHEELS_DIR"/*.so; do
    if [ -f "$so_file" ]; then
        echo "Copiando $(basename "$so_file") a $SITE_PACKAGES"
        cp "$so_file" "$SITE_PACKAGES/"
    fi
done

deactivate

echo "[6/7] Asegurando directorios persistentes"
mkdir -p "$DATA_DIR/logs" "$DATA_DIR/audio" "$DATA_DIR/tmp"
mkdir -p "$DATA_DIR/acoustic_params" "$DATA_DIR/prediction_files"
mkdir -p "$DATA_DIR/models" "$DATA_DIR/spool" "$DATA_DIR/tailscale"

ln -sfn "$DATA_DIR/logs" "$INSTALL_DIR/logs"
ln -sfn "$DATA_DIR/audio" "$INSTALL_DIR/audio"
ln -sfn "$DATA_DIR/tmp" "$INSTALL_DIR/tmp"
ln -sfn "$DATA_DIR/acoustic_params" "$INSTALL_DIR/acoustic_params"
ln -sfn "$DATA_DIR/prediction_files" "$INSTALL_DIR/prediction_files"
ln -sfn "$DATA_DIR/models" "$INSTALL_DIR/models"

echo "[7/7] Actualizando/reiniciando servicios"
if [ -d services ]; then
    cp services/*.service /etc/systemd/system/ 2>/dev/null || true
    systemctl daemon-reload

    for service_file in services/*.service; do
        if [ -f "$service_file" ]; then
            service_name="$(basename "$service_file")"
            echo "Reiniciando $service_name"
            systemctl restart "$service_name" || true
        fi
    done
fi

echo "=== Actualización completada ==="
