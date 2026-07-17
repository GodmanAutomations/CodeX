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

# Declare every external command used after the destructive step up-front, so a
# missing tool fails fast before we repartition/format rather than mid-flight.
# (partprobe/udevadm/umount are best-effort and guarded with `|| true` below.)
for _c in parted mkfs.ext4 blkid lsblk mountpoint getent df; do
  need_cmd "${_c}"
done

[ -b "${SSD_DEV}" ] || die "${SSD_DEV} is not a block device."

log "Target disk layout:"
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT,MODEL "${SSD_DEV}" || true
warn "ALL DATA on ${SSD_DEV} will be ERASED."
confirm "Repartition and format ${SSD_DEV} now?"

# Unmount any active mounts on the target device to avoid "resource busy".
umount "${SSD_DEV}"* 2>/dev/null || true

log "Creating GPT + single ext4 partition on ${SSD_DEV} ..."
parted -s "${SSD_DEV}" mklabel gpt
parted -s "${SSD_DEV}" mkpart primary ext4 1MiB 100%

# Give the kernel a moment to settle the new partition node.
partprobe "${SSD_DEV}" 2>/dev/null || true
udevadm settle 2>/dev/null || true

[ -b "${SSD_PART}" ] || die "Expected partition ${SSD_PART} did not appear. Check SSD_PART in gadget.env."

# The user confirmed SSD_DEV, but SSD_PART is a separate config value. Make sure
# it's actually a partition of the disk we just repartitioned before formatting,
# so a misconfigured SSD_PART can't wipe a partition on some other disk.
_parent="$(lsblk -no PKNAME "${SSD_PART}" 2>/dev/null | head -n1)"
if [ -z "${_parent}" ] || [ "/dev/${_parent}" != "${SSD_DEV}" ]; then
  die "${SSD_PART} is not a partition of ${SSD_DEV} (parent: /dev/${_parent:-unknown}). Refusing to format. Check SSD_PART in gadget.env."
fi

log "Formatting ${SSD_PART} as ext4 (label: pidata) ..."
mkfs.ext4 -F -L pidata "${SSD_PART}"

mkdir -p "${SSD_MOUNT}"

UUID="$(blkid -s UUID -o value "${SSD_PART}")"
[ -n "${UUID}" ] || die "Could not read UUID of ${SSD_PART}."

FSTAB_LINE="UUID=${UUID} ${SSD_MOUNT} ext4 defaults,nofail,x-systemd.device-timeout=10s 0 2"
if grep -q "UUID=${UUID}" /etc/fstab; then
  log "fstab already has an entry for this UUID"
elif grep -qE "[[:space:]]${SSD_MOUNT}[[:space:]]" /etc/fstab; then
  warn "fstab already mounts ${SSD_MOUNT} (different device). Not appending, to avoid a duplicate mount point."
else
  echo "${FSTAB_LINE}" >> /etc/fstab
  log "Appended to /etc/fstab: ${FSTAB_LINE}"
fi

mount -a
# The fstab entry uses `nofail`, so `mount -a` can silently skip a failed mount.
# Verify something is actually mounted at SSD_MOUNT before chowning/mkdir'ing —
# otherwise we'd modify the underlying directory on the root filesystem.
mountpoint -q "${SSD_MOUNT}" \
  || die "${SSD_MOUNT} is not mounted after 'mount -a' (nofail may have skipped it). Refusing to write to the underlying root filesystem."

chown "${PI_USER}:${PI_USER}" "${SSD_MOUNT}"
mkdir -p "${SSD_MOUNT}/projects" "${SSD_MOUNT}/transfers"
chown -R "${PI_USER}:${PI_USER}" "${SSD_MOUNT}/projects" "${SSD_MOUNT}/transfers"

home="$(getent passwd "${PI_USER}" | cut -d: -f6)"
: "${home:=/home/${PI_USER}}"
if [ -d "${home}" ]; then
  for _name in projects transfers; do
    link="${home}/${_name}"
    # `ln -sfn` into an existing REAL directory would nest the link inside it
    # rather than replace it, silently leaving the home path unchanged. Only
    # (re)create the symlink when the path is absent or already a symlink.
    if [ -d "${link}" ] && [ ! -L "${link}" ]; then
      warn "${link} already exists as a real directory; leaving it. Move its contents into ${SSD_MOUNT}/${_name} manually if you want it on the SSD."
    else
      ln -sfn "${SSD_MOUNT}/${_name}" "${link}"
      log "Linked ${link} -> ${SSD_MOUNT}/${_name}"
    fi
  done
fi

log "SSD data volume ready at ${SSD_MOUNT}"
df -h "${SSD_MOUNT}"
