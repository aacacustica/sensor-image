# Changelog

## [0.1.0] - 2026-06-19

### Añadido
- Estructura base de despliegue en `/opt/noiseport`.
- Datos persistentes en `/root/data`.
- Entorno virtual Python en `/opt/noiseport/.venv`.
- Soporte para `audio`, `logs`, `acoustic_params`, `prediction_files`, `models`, `tmp` y `spool`.
- Scripts `install.sh` y `update.sh`.
- Preparación para imagen Yocto base con partición `data`.

### Pendiente
- Automatizar expansión de `/dev/mmcblk1p10` en imagen Yocto base.
- Revisar servicios definitivos de grabación, pipeline y Tailscale.