#!/usr/bin/env bash
#
# enable-trixie-gadget.sh — turn an existing Raspberry Pi OS Trixie install into
# a USB Ethernet gadget using the official rpi-usb-gadget package.
#
# Runs ON THE PI. Use this when you flashed a Trixie Lite image without
# pre-configuring gadget mode in the boot partition.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

[ "$(id -u)" -eq 0 ] || die "Run as root (sudo $0)."

codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-unknown}")"
log "OS codename: ${codename}"
if [ "${codename}" != "trixie" ]; then
  warn "This helper targets Trixie. On '${codename}' use the Bookworm fallback (docs/03)."
  confirm "Continue anyway?"
fi

log "Installing rpi-usb-gadget ..."
apt update
apt install -y rpi-usb-gadget

log "Enabling gadget mode ..."
rpi-usb-gadget on

log "Done. Reboot to bring up the gadget link:"
log "  sudo reboot"
log "After reboot, connect the correct USB port to the host and SSH in:"
log "  ssh ${PI_USER:-<user>}@${PI_HOSTNAME:-<host>}.local   (fallback: 10.12.194.1)"
