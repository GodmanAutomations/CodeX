#!/usr/bin/env bash
#
# backup-sd.sh — raw image backup of an SD card / SSD before you overwrite it.
#
# Runs on the HOST (Linux or macOS). Produces a dated .img plus a .sha256.
#
# Usage:
#   ./backup-sd.sh                 # interactive: lists disks, prompts for target
#   ./backup-sd.sh /dev/sdX        # Linux block device
#   ./backup-sd.sh /dev/diskN      # macOS whole disk (uses /dev/rdiskN)
#
# It will NOT proceed without an explicit confirmation of the device.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

OUTDIR="${HOME}/pi-backups"
mkdir -p "${OUTDIR}"
STAMP="$(date +%F)"

os="$(uname -s)"
dev="${1:-}"

if [ "${os}" = "Darwin" ]; then
  need_cmd diskutil
  if [ -z "${dev}" ]; then
    log "Available disks:"
    diskutil list
    printf 'Enter the SD card disk (e.g. /dev/disk4): ' >&2
    read -r dev
  fi
  [ -n "${dev}" ] || die "No device given."
  confirm "About to READ ${dev} into a backup image. Correct disk?"
  diskutil unmountDisk "${dev}"
  # /dev/rdiskN is the raw (fast) node on macOS: /dev/disk4 -> /dev/rdisk4.
  raw="${dev/disk/rdisk}"
  out="${OUTDIR}/${STAMP}-pi-sd.img"
  log "Reading ${raw} -> ${out}"
  sudo dd if="${raw}" of="${out}" bs=4m status=progress
  shasum -a 256 "${out}" > "${out}.sha256"
else
  need_cmd lsblk
  if [ -z "${dev}" ]; then
    log "Available block devices:"
    lsblk -o NAME,SIZE,MODEL,TRAN
    printf 'Enter the SD card device (e.g. /dev/sdb): ' >&2
    read -r dev
  fi
  [ -n "${dev}" ] || die "No device given."
  [ -b "${dev}" ] || die "${dev} is not a block device."
  confirm "About to READ ${dev} into a backup image. Correct device?"
  # Unmount any mounted partitions of the device (ignore failures).
  sudo umount "${dev}"* 2>/dev/null || true
  out="${OUTDIR}/${STAMP}-pi-sd.img"
  log "Reading ${dev} -> ${out}"
  sudo dd if="${dev}" of="${out}" bs=4M status=progress conv=fsync
  sha256sum "${out}" > "${out}.sha256"
fi

log "Backup complete: ${out}"
log "Checksum:        ${out}.sha256"
