#!/usr/bin/env bash
#
# setup-ufw.sh — install ufw and allow SSH/VNC only over the USB gadget link
# (usb0), with optional trusted-LAN allowances.
#
# Runs ON THE PI. See docs/06-security.md.
#
# Env knobs:
#   GADGET_IFACE   gadget interface name (default: usb0)
#   TRUSTED_LAN    optional CIDR to also allow, e.g. 192.168.0.0/16 (default: none)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

[ "$(id -u)" -eq 0 ] || die "Run as root (sudo $0)."

: "${GADGET_IFACE:=usb0}"
: "${TRUSTED_LAN:=}"

log "Installing ufw ..."
apt update
apt install -y ufw

ufw default deny incoming
ufw default allow outgoing

log "Allowing SSH (22) and VNC (5900) in on ${GADGET_IFACE} ..."
ufw allow in on "${GADGET_IFACE}" proto tcp to any port 22 comment 'SSH over USB'
ufw allow in on "${GADGET_IFACE}" proto tcp to any port 5900 comment 'VNC over USB'

if [ -n "${TRUSTED_LAN}" ]; then
  log "Allowing SSH/VNC from trusted LAN ${TRUSTED_LAN} ..."
  ufw allow proto tcp from "${TRUSTED_LAN}" to any port 22 comment 'SSH on trusted LAN'
  ufw allow proto tcp from "${TRUSTED_LAN}" to any port 5900 comment 'VNC on trusted LAN'
fi

ufw --force enable
ufw status verbose
log "Firewall active. Control traffic is limited to ${GADGET_IFACE}${TRUSTED_LAN:+ and ${TRUSTED_LAN}}."
