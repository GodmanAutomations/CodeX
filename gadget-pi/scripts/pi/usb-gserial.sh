#!/usr/bin/env bash
#
# usb-gserial.sh — bring up a simple USB serial gadget (g_serial). The device
# side appears as /dev/ttyGS0; the host sees a CDC-ACM / USB serial port.
#
# Runs ON THE PI. Useful as a recovery/console fallback — NOT a substitute for
# g_ether when you want to control the Pi from an iPad. See docs/04-advanced-gadgets.md.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

[ "$(id -u)" -eq 0 ] || die "Run as root (sudo $0)."

log "Loading g_serial ..."
modprobe g_serial

# Optionally spawn a login prompt on the gadget serial line.
if [ "${1:-}" = "--console" ]; then
  log "Enabling serial-getty on ttyGS0 ..."
  systemctl enable --now serial-getty@ttyGS0.service
fi

ls -l /dev/ttyGS0 2>/dev/null || warn "/dev/ttyGS0 not present yet (check that a UDC is available)."
log "Serial gadget up. Host connects to the new USB serial device (e.g. screen /dev/tty.usbmodem* 115200)."
