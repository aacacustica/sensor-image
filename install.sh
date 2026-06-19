#!/bin/sh

set -e

APP_NAME="IoT_microphone_scripts-main"
INSTALL_DIR="/opt/noiseport"
DATA_DIR="/root/data"
VENV_DIR="$INSTALL_DIR"/.venv"
PYTHON_BIN="python3"

echo "=== [1/8] Creando directorios ==="
mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR/logs"
mkdir -p "$DATA_DIR/audio"
mkdir -p "$DATA_DIR/acoustic_params"
mkdir -p "$DATA_DIR/prediction_files"
mkdir -p "$DATA_DIR/models"
mkdir -p "$DATA_DIR/spool"

echo "=== [2/8] Copiando aplicación ==="
rm -rf "$INSTALL_DIR/app"
cp -r app "$INSTALL_DIR/app"

echo "=== [3/8] Copiando configuración ==="

mkdir -p "$INSTALL_DIR/config"
if [-d config]; then
	cp -r config/* "$INSTALL_DIR/config/" 2>/dev/null || true
fi

if [ ! -f "$INSTALL_DIR/config/sensor.env" ] && [ -f "$INSTALL_DIR/config/sensor.env.example" ]; then
	cp "$INSTALL_DIR/config/sensor.env/example" "$INSTALL_DIR/config/sensor.env"
fi

echo "=== [4/8] Copiando wheels ==="
rm -rf "$INSTALL_DIR/wheels"
cp -r wheels/* "$INSTALL_DIR/wheels/" 2>/dev/null || true
fi

echo "=== [5/8] Copiando requirements ==="
cp requirements.txt "$INSTALL_DIR/requirements.txt"

echo "=== [6/8] Creando entorno virtual ==="
if [ ! -d "$VENV_DIR" ]; then
	"$PYTHON_BIN" -m venv "$VENV_DIR"
fi

. "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip

if [ -d "$INSTALL_DIR/wheels" ]; then
	python -m pip install --find-links --default-timeout=100 --no-cache "$INSTALL_DIR/wheels/*.whl" -r "$INSTALL_DIR/requirements.txt"
	cp -r "$INSTALL_DIR/*.so" "$VENV_DIR/.venv/lib/python3.12/site-packages/"
else 
	python -m pip install -r "$INSTALL_DIR/requirements.txt" --default-timeout=100 --no-cache

echo "=== [5/8] Creando enlaces simbólicos a datos persistentens ==="
ln -sfn "$DATA_DIR/logs" "$INSTALL_DIR/logs"
ln -sfn "$DATA_DIR/audio" "$INSTALL_DIR/audio"
ln -sfn "$DATA_DIR/tmp" "$INSTALL_DIR/tmp"
ln -sfn "$DATA_DIR/acoustic_params" "$INSTALL_DIR/acoustic_params"
ln -sfn "$DATA_DIR/prediction_files" "$INSTALL_DIR/prediction_files"
ln -sfn "$DATA_DIR/models" "$INSTALL_DIR/models"

echo "=== [8/8] Cargando archivos .service en systemd ==="
if [ -d services ]; then
	cp services/*.service /etc/systemd/system/ 2>/dev/null || true
	systemctl daemon-reload

	for service_file in services/*service; do
		if [ -f "$service_file" ]; then
			service_name = "$(basename "$service_file")"
			echo "Habilitando $service_name"
			systemctl enable "$service_name" || true
		fi
	done
fi

echo "=== Instalación completada ==="
echo "Código:	$INSTALL_DIR"
echo "Datos:	$DATA_DIR"
echo "Venv:	$VENV_DIR"
echo ""
echo "Revisar configuración en $INSTALL_DIR/config/sensor.env"

