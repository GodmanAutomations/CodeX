#!/usr/bin/env bash
#
# usb-gmulti.sh — composite USB gadget via configfs: ECM (Ethernet) + ACM
# (serial) + READ-ONLY mass storage.
#
# Runs ON THE PI. Managed by systemd/usb-gmulti.service, or run manually:
#   sudo ./usb-gmulti.sh start | stop | restart
#
# SAFETY: the mass-storage LUN is exported READ-ONLY from a dedicated image file
# (/pi-share.img). NEVER back a writable LUN with your live root filesystem — the
# host and the Pi writing the same block device concurrently corrupts data.
# See docs/04-advanced-gadgets.md.
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Run as root (sudo $0 ...)" >&2; exit 1; }

ACTION="${1:-start}"
G=/sys/kernel/config/usb_gadget/g1
LUN_IMG="${LUN_IMG:-/pi-share.img}"
LUN_SIZE_MB="${LUN_SIZE_MB:-256}"
GADGET_MANUFACTURER="${GADGET_MANUFACTURER:-Gadget-Pi}"
GADGET_PRODUCT="${GADGET_PRODUCT:-Pi USB Multi}"
# ECM MAC addresses. Override these if you connect multiple Gadget-Pi devices to
# the same host (or bridge them) to avoid address collisions.
GADGET_DEV_MAC="${GADGET_DEV_MAC:-02:12:34:56:78:9a}"
GADGET_HOST_MAC="${GADGET_HOST_MAC:-06:12:34:56:78:9a}"

start() {
  modprobe libcomposite
  mkdir -p /sys/kernel/config
  mount -t configfs none /sys/kernel/config 2>/dev/null || true
  # The mount is best-effort (it may already be mounted); confirm the gadget
  # subsystem is present so later configfs writes don't fail cryptically.
  [ -d /sys/kernel/config/usb_gadget ] || {
    echo "configfs usb_gadget not available — need root, a gadget-capable kernel, and libcomposite. Aborting." >&2
    exit 1
  }

  mkdir -p "$G"
  echo 0x1d6b > "$G/idVendor"    # Linux Foundation
  echo 0x0104 > "$G/idProduct"   # Multifunction Composite Gadget
  echo 0x0200 > "$G/bcdUSB"
  echo 0x0100 > "$G/bcdDevice"

  mkdir -p "$G/strings/0x409"
  echo "$GADGET_MANUFACTURER" > "$G/strings/0x409/manufacturer"
  echo "$GADGET_PRODUCT"      > "$G/strings/0x409/product"
  local serial
  serial="$(awk '/Serial/ {print $3}' /proc/cpuinfo)"
  # Some hosts refuse to enumerate a gadget with an empty serial number.
  echo "${serial:-0000000000000000}" > "$G/strings/0x409/serialnumber"

  mkdir -p "$G/configs/c.1/strings/0x409"
  echo "ECM+Serial+ROStorage" > "$G/configs/c.1/strings/0x409/configuration"
  echo 250 > "$G/configs/c.1/MaxPower"

  mkdir -p "$G/functions/ecm.usb0"
  mkdir -p "$G/functions/acm.gs0"
  mkdir -p "$G/functions/mass_storage.0"

  echo "$GADGET_DEV_MAC"  > "$G/functions/ecm.usb0/dev_addr"
  echo "$GADGET_HOST_MAC" > "$G/functions/ecm.usb0/host_addr"

  # LUN_SIZE_MB is passed to dd count=; reject anything that isn't a positive
  # integer before it can make dd fail or misbehave.
  case "$LUN_SIZE_MB" in
    "" | *[!0-9]*) echo "LUN_SIZE_MB must be a positive integer (MB), got: '$LUN_SIZE_MB'" >&2; exit 1 ;;
  esac
  [ "$LUN_SIZE_MB" -gt 0 ] || { echo "LUN_SIZE_MB must be greater than 0" >&2; exit 1; }

  # Guard the backing-image path: a device node or other non-regular file here
  # would let the dd below irreversibly overwrite a real disk (e.g. /dev/sda).
  case "$LUN_IMG" in
    /dev/*) echo "Refusing: LUN_IMG ($LUN_IMG) is under /dev." >&2; exit 1 ;;
  esac
  if [ -e "$LUN_IMG" ] && [ ! -f "$LUN_IMG" ]; then
    echo "Refusing: LUN_IMG ($LUN_IMG) exists and is not a regular file." >&2; exit 1
  fi

  # Create + format the backing image the first time so the host sees a mountable
  # filesystem (FAT32 for broad iPad/macOS/Windows compatibility) rather than a
  # blank, unformatted, write-protected volume.
  if [ ! -f "$LUN_IMG" ]; then
    # FAT32 specifically, for iPad/macOS/Windows compatibility. No ext4 fallback:
    # an ext4 image wouldn't mount on any of those hosts, defeating the purpose.
    command -v mkfs.vfat >/dev/null 2>&1 \
      || { echo "mkfs.vfat not found — install it: sudo apt install -y dosfstools" >&2; exit 1; }
    dd if=/dev/zero of="$LUN_IMG" bs=1M count="$LUN_SIZE_MB" status=none
    mkfs.vfat -F 32 "$LUN_IMG" >/dev/null
  fi
  echo 1          > "$G/functions/mass_storage.0/stall"
  echo 1          > "$G/functions/mass_storage.0/lun.0/ro"
  echo "$LUN_IMG" > "$G/functions/mass_storage.0/lun.0/file"

  ln -snf "$G/functions/ecm.usb0"         "$G/configs/c.1/"
  ln -snf "$G/functions/acm.gs0"          "$G/configs/c.1/"
  ln -snf "$G/functions/mass_storage.0"   "$G/configs/c.1/"

  local udc=""
  local d
  for d in /sys/class/udc/*/; do
    [ -d "$d" ] || continue   # skip the literal glob when no UDC exists
    udc="$(basename "$d")"
    break
  done
  [ -n "$udc" ] || { echo "No UDC available" >&2; exit 1; }
  echo "$udc" > "$G/UDC"
}

stop() {
  if [ -d "$G" ]; then
    echo "" > "$G/UDC" 2>/dev/null || true
    rm -f "$G/configs/c.1/ecm.usb0" || true
    rm -f "$G/configs/c.1/acm.gs0" || true
    rm -f "$G/configs/c.1/mass_storage.0" || true
    rmdir "$G/functions/ecm.usb0" || true
    rmdir "$G/functions/acm.gs0" || true
    # configfs auto-creates lun.0 under the mass_storage function; remove it
    # first or the function directory can't be rmdir'd.
    rmdir "$G/functions/mass_storage.0/lun.0" 2>/dev/null || true
    rmdir "$G/functions/mass_storage.0" || true
    rmdir "$G/configs/c.1/strings/0x409" || true
    rmdir "$G/configs/c.1" || true
    rmdir "$G/strings/0x409" || true
    rmdir "$G" || true
  fi
}

case "$ACTION" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  *) echo "Usage: $0 {start|stop|restart}" >&2; exit 1 ;;
esac
