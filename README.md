# sensor-image

Imagen, configuración y scripts de despliegue para el sensor acústico basado en CCMP13-DVK de Digi.

## Estructura

```text
/opt/noiseport
├── app/              Código de aplicación
├── .venv/            Entorno virtual Python
├── config/           Configuración del sensor
├── wheels/           Wheels compiladas para la arquitectura objetivo
├── logs -> /root/data/logs
├── audio -> /root/data/audio
├── tmp -> /root/data/tmp
├── acoustic_params -> /root/data/acoustic_params
└── prediction_files -> /root/data/prediction_files
