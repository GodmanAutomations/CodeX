#!/usr/bin/env bash
#
# setup-ssd-data.sh — turn an attached SSD into a persistent data volume mounted
# at $SSD_MOUNT (default /srv/data), with home-directory symlinks.
#
# Runs ON THE PI. DESTRUCTIVE: it repartitions and formats $SSD_DEV. On the
# original Pi Zero W this is the recommended way to use an SSD (keep the OS on
# microSD; USB mass-storage boot support starts at Zero 2 W). See docs/05-ssd.md.
#
# Config (config/gadget.env): SSD_DEV, SSD_PART, SSD_MOUNT, PI_USER
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

[ "$(id -u)" -eq 0 ] || die "Run as root (sudo $0)."

require SSD_DEV
require SSD_PART
: "${SSD_MOUNT:=/srv/data}"
: "${PI_USER:=${SUDO_USER:-pi}}"

need_cmd parted
need_cmd mkfs.ext4
need_cmd blkid

[ -b "${SSD_DEV}" ] || die "${SSD_DEV} is not a block device."

log "Target disk layout:"
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT,MODEL "${SSD_DEV}" || true
warn "ALL DATA on ${SSD_DEV} will be ERASED."
confirm "Repartition and format ${SSD_DEV} now?"

log "Creating GPT + single ext4 partition on ${SSD_DEV} ..."
parted -s "${SSD_DEV}" mklabel gpt
parted -s "${SSD_DEV}" mkpart primary ext4 1MiB 100%

# Give the kernel a moment to settle the new partition node.
partprobe "${SSD_DEV}" 2>/dev/null || true
udevadm settle 2>/dev/null || true

[ -b "${SSD_PART}" ] || die "Expected partition ${SSD_PART} did not appear. Check SSD_PART in gadget.env."

log "Formatting ${SSD_PART} as ext4 (label: pidata) ..."
mkfs.ext4 -F -L pidata "${SSD_PART}"

mkdir -p "${SSD_MOUNT}"

UUID="$(blkid -s UUID -o value "${SSD_PART}")"
[ -n "${UUID}" ] || die "Could not read UUID of ${SSD_PART}."

FSTAB_LINE="UUID=${UUID} ${SSD_MOUNT} ext4 defaults,nofail,x-systemd.device-timeout=10s 0 2"
if grep -q "UUID=${UUID}" /etc/fstab; then
  log "fstab already has an entry for this UUID"
else
  echo "${FSTAB_LINE}" >> /etc/fstab
  log "Appended to /etc/fstab: ${FSTAB_LINE}"
fi

mount -a
chown "${PI_USER}:${PI_USER}" "${SSD_MOUNT}"
mkdir -p "${SSD_MOUNT}/projects" "${SSD_MOUNT}/transfers"
chown -R "${PI_USER}:${PI_USER}" "${SSD_MOUNT}/projects" "${SSD_MOUNT}/transfers"

home="/home/${PI_USER}"
if [ -d "${home}" ]; then
  ln -sfn "${SSD_MOUNT}/projects"  "${home}/projects"
  ln -sfn "${SSD_MOUNT}/transfers" "${home}/transfers"
  log "Linked ${home}/projects and ${home}/transfers -> ${SSD_MOUNT}"
fi

log "SSD data volume ready at ${SSD_MOUNT}"
df -h "${SSD_MOUNT}"
