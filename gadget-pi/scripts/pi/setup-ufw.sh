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
apt-get update
apt-get install -y ufw

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

# Lockout guard: if you're connected over SSH on some other interface (e.g.
# Wi-Fi), enabling default-deny with only usb0 allowed would kill your session.
if [ -n "${SSH_CONNECTION:-}" ]; then
  server_ip="$(echo "${SSH_CONNECTION}" | awk '{print $3}')"
  # Compare exact addresses, not a regex/substring match: extract the bare IPs
  # configured on the gadget iface and test for an exact whole-line match, so a
  # look-alike IP (e.g. 10.55.0.10 vs 10.55.0.1) can't be a false positive.
  iface_ips="$(ip -o addr show dev "${GADGET_IFACE}" 2>/dev/null | awk '{print $4}' | cut -d/ -f1)"
  if [ -n "${server_ip}" ] && ! printf '%s\n' "${iface_ips}" | grep -qxF "${server_ip}"; then
    warn "Your SSH session is on ${server_ip}, which is NOT on ${GADGET_IFACE}."
    warn "Enabling the firewall now may terminate this session and lock you out."
    confirm "Proceed with enabling the firewall?"
  fi
fi

ufw --force enable
ufw status verbose
log "Firewall active. Control traffic is limited to ${GADGET_IFACE}${TRUSTED_LAN:+ and ${TRUSTED_LAN}}."
