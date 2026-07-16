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

start() {
  modprobe libcomposite
  mkdir -p /sys/kernel/config
  mount -t configfs none /sys/kernel/config 2>/dev/null || true

  mkdir -p "$G"
  echo 0x1d6b > "$G/idVendor"    # Linux Foundation
  echo 0x0104 > "$G/idProduct"   # Multifunction Composite Gadget
  echo 0x0200 > "$G/bcdUSB"
  echo 0x0100 > "$G/bcdDevice"

  mkdir -p "$G/strings/0x409"
  echo "StephenPi"      > "$G/strings/0x409/manufacturer"
  echo "Pi USB Multi"   > "$G/strings/0x409/product"
  awk '/Serial/ {print $3}' /proc/cpuinfo > "$G/strings/0x409/serialnumber"

  mkdir -p "$G/configs/c.1/strings/0x409"
  echo "ECM+Serial+ROStorage" > "$G/configs/c.1/strings/0x409/configuration"
  echo 250 > "$G/configs/c.1/MaxPower"

  mkdir -p "$G/functions/ecm.usb0"
  mkdir -p "$G/functions/acm.gs0"
  mkdir -p "$G/functions/mass_storage.0"

  echo 02:12:34:56:78:9a > "$G/functions/ecm.usb0/dev_addr"
  echo 06:12:34:56:78:9a > "$G/functions/ecm.usb0/host_addr"

  [ -f "$LUN_IMG" ] || dd if=/dev/zero of="$LUN_IMG" bs=1M count="$LUN_SIZE_MB" status=none
  echo 1          > "$G/functions/mass_storage.0/stall"
  echo 1          > "$G/functions/mass_storage.0/lun.0/ro"
  echo "$LUN_IMG" > "$G/functions/mass_storage.0/lun.0/file"

  ln -snf "$G/functions/ecm.usb0"         "$G/configs/c.1/"
  ln -snf "$G/functions/acm.gs0"          "$G/configs/c.1/"
  ln -snf "$G/functions/mass_storage.0"   "$G/configs/c.1/"

  local udc=""
  local d
  for d in /sys/class/udc/*/; do udc="$(basename "$d")"; break; done
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
