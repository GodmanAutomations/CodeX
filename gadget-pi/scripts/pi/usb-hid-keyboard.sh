#!/usr/bin/env bash
#
# usb-hid-keyboard.sh — make the Pi emulate a USB HID keyboard to the host via
# configfs. Writing 8-byte reports to /dev/hidg0 injects keystrokes.
#
# Runs ON THE PI. Included for completeness only. This is the WRONG DIRECTION for
# controlling the Pi from an iPad — it lets the Pi type INTO the host, not the
# other way around. For iPad control use g_ether. See docs/04-advanced-gadgets.md.
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Run as root (sudo $0)" >&2; exit 1; }

G=/sys/kernel/config/usb_gadget/hidkbd
GADGET_MANUFACTURER="${GADGET_MANUFACTURER:-Gadget-Pi}"
GADGET_PRODUCT="${GADGET_PRODUCT:-Pi HID Keyboard}"
modprobe libcomposite
mkdir -p /sys/kernel/config
mount -t configfs none /sys/kernel/config 2>/dev/null || true
# The mount is best-effort (it may already be mounted); confirm the gadget
# subsystem is actually present so later writes don't fail with a cryptic error.
[ -d /sys/kernel/config/usb_gadget ] || {
  echo "configfs usb_gadget not available — need root, a gadget-capable kernel, and libcomposite. Aborting." >&2
  exit 1
}

mkdir -p "$G"
echo 0x1d6b > "$G/idVendor"
echo 0x0104 > "$G/idProduct"
mkdir -p "$G/strings/0x409"
echo "$GADGET_MANUFACTURER" > "$G/strings/0x409/manufacturer"
echo "$GADGET_PRODUCT"      > "$G/strings/0x409/product"
echo "0001"            > "$G/strings/0x409/serialnumber"

mkdir -p "$G/configs/c.1/strings/0x409"
echo "HID Keyboard" > "$G/configs/c.1/strings/0x409/configuration"
mkdir -p "$G/functions/hid.usb0"
echo 1 > "$G/functions/hid.usb0/protocol"      # keyboard
echo 1 > "$G/functions/hid.usb0/subclass"      # boot interface
echo 8 > "$G/functions/hid.usb0/report_length" # 8-byte reports

# Standard boot-keyboard report descriptor.
printf '\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x03\x95\x05\x75\x01\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x03\x95\x06\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0' \
  > "$G/functions/hid.usb0/report_desc"

ln -snf "$G/functions/hid.usb0" "$G/configs/c.1/"
udc=""
for d in /sys/class/udc/*/; do
  [ -d "$d" ] || continue   # skip the literal glob when no UDC exists
  udc="$(basename "$d")"
  break
done
[ -n "$udc" ] || { echo "No UDC available" >&2; exit 1; }
echo "$udc" > "$G/UDC"

echo "HID keyboard gadget up. Device node: /dev/hidg0" >&2
