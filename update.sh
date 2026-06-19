#!/bin/sh
set -e

INSTALL_DIR="/opt/noiseport/"
DATA_DIR="/root/data"
VENV_DIR="$INSTALL_DIR/.venv"

echo "=== Actualización noiseport ==="

if [ "$(id -u)" != "0" ]; then
	echo "ERROR: ejecuta este script como root."
	exit 1
fi

echo "[1/6] Copiando desde repositorio remoto"
git pull || true

echo "[2/6] Actualizando código"
rm -rf "$INSTALL_DIR/app"
cp -r app "$INSTALL_DIR/app"

echo "[3/6] Actualizando configuración wheels y requirements"
mkdir -p "$INSTALL_DIR/wheels"
cp -r config/* "$INSTALL_DIR/wheels/" 2>/dev/null || true

echo "[4/6] Actualizando entorno virtual"
if [ ! -d "$VENV_DIR" ]; then
	python -m venv "$VENV_DIR"
fi

. "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install --find-links "$INSTALL_DIR/wheels" -r "$INSTALL_DIR/requirements.txt"
cp "INSTALL_DIR/wheels/*.so" "$VENV_DIR/lib/python3.12/site-packages/"

deactivate

echo "[5/6] Asegurando directorios "
mkdir -p "$DATA_DIR/logs" "$DATA_DIR/audio" "$DATA_DIR/tmp"
mkdir -p "$DATA_DIR/acoustic_params" "$DATA_DIR/prediction_files"
mkdir -p "$DATA_DIR/models" "$DATA_DIR/spool"

ln -sfn "$DATA_DIR/logs" "$INSTALL_DIR/logs"
ln -sfn "$DATA_DIR/audio" "$INSTALL_DIR/audio"
ln -sfn "$DATA_DIR/tmp" "$INSTALL_DIR/tmp"
ln -sfn "$DATA_DIR/acoustic_params" "$INSTALL_DIR/acoustic_params"
ln -sfn "$DATA_DIR/prediction_files" "$INSTALL_DIR/prediction_files"
ln -sfn "$DATA_DIR/models" "$INSTALL_DIR/models"

echo "[6/6] Reiniciando servicios"
cp services/*.service etc/systemd/system 2>/dev/null || true
systemctl daemon-reload

for service_file in services/*.service
	if [ -f "$service_file"]; then
		service_name="$(basename "$service_file")"
		systemctl restart "$service_name" || true
	fi
done

echo "=== Actualización completada ==="



