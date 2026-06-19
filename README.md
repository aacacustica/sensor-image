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

```
<p align="center">
<img width="311" height="971" alt="Diagrama estructura sensor drawio" src="https://github.com/user-attachments/assets/710764d0-8b18-47e8-a6af-266ab1b50937" />
</p>

## Organización del respositorio

```text
sensor-image/
├── app/
│
├── services/
│
├── wheels/
│
├── config/
│   ├── sensor.env.example
│   └── config.yaml.example
│
├── scripts/
│   ├── check_system.sh
│   ├── setup_dirs.sh
│   ├── install_services.sh
│   └── ...
│
├── install.sh
├── update.sh
├── requirements.txt
├── VERSION
├── CHANGELOG.md
└── README.md
```

## Contenidos por carpeta

```text
-app/
Contiene el código en python que se ejecuta en el sensor.

-services/
Todos los archivos .service que se necesita el sensor para ejecutar tareas.

-wheels/
Dependencias compiladas para ARMv7l y compilaciones en general.

-config/
Archivos de configuración del dispositivo a los que accede el código.

-scripts/
Scripts auxiliares.

```

## Organización de datos


```text
-/root/data/ : es la ubicación donde se guarda toda la información que genera el sensor.

-/root/data/audio : es donde se guardan los audios.
-/root/data/acoustic_params : es donde se guardan los parámetros acústicos generados.
-/root/data/prediction_files : es donde se guarda la información de inferencia de clases sonoras sobre los grabaciones de audio.
-/root/data/logs :  es donde se guardan los logs de los procesos del sensor.

-/root/data/models :  aquí se guardan los archivos relativos al modelo de inferencia ( taxonomía y archivo yamnet.h5 por ahora )

```

## install.sh

```text
Archivo que se ejecuta una única vez al desplegar un nuevo sensor fisicamente. Crea /opt/noiseport , /root/data, copia la última versión del código y los servicios, crea el entorno virtual, los links simbólicos, instala librerías y wheels en caso de faltar en la imágen.

```

#update.sh

```
Se ejecuta manualmente cuando hay una nueva versión en el repositorio. Hace un pull, y el sensor adquiere la nueva versión.

```

## CHANGELOG

```
0.1.0

- Primera versión
- Nuevo layout

```
