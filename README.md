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

<img width="311" height="971" alt="Diagrama estructura sensor drawio" src="https://github.com/user-attachments/assets/710764d0-8b18-47e8-a6af-266ab1b50937" />
