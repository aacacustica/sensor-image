#!/bin/sh
set -e

DISK="/dev/mmcblk1"
PART="${DISK}p10"
MOUNTPOINT="/root/data"

echo "[data] Preparando partición de datos..."

mkdir -p "$MOUNTPOINT"

if ! command -v sfdisk >/dev/null 2>&1; then
    echo "ERROR: falta sfdisk. Pídelo en la imagen Yocto base."
    exit 1
fi

if ! command -v mkfs.ext4 >/dev/null 2>&1; then
    echo "ERROR: falta mkfs.ext4. Pídelo en la imagen Yocto base."
    exit 1
fi

CURRENT_SIZE_MB="$(blockdev --getsize64 "$PART" 2>/dev/null | awk '{print int($1/1024/1024)}' || echo 0)"

if [ "$CURRENT_SIZE_MB" -gt 10000 ]; then
    echo "[data] $PART ya parece grande (${CURRENT_SIZE_MB} MB). No se modifica."
else
    echo "[data] Recreando $PART usando el resto del disco..."
    START="$(sfdisk -d "$DISK" | awk -F'[=,]' '/mmcblk1p10/ {gsub(/ /,"",$2); print $2}')"

    if [ -z "$START" ]; then
        echo "ERROR: no se pudo obtener sector inicial de p10."
        exit 1
    fi

    umount "$PART" 2>/dev/null || true

    sfdisk --delete "$DISK" 10
    echo "${START},,L" | sfdisk --append "$DISK"

    partprobe "$DISK" 2>/dev/null || true
    sleep 2

    mkfs.ext4 -F -L data "$PART"
fi

grep -q "$MOUNTPOINT" /etc/fstab || echo "LABEL=data  $MOUNTPOINT  ext4  defaults,nofail  0  0" >> /etc/fstab

mount "$MOUNTPOINT" 2>/dev/null || mount "$PART" "$MOUNTPOINT"
echo "[data] OK: $PART montada en $MOUNTPOINT"