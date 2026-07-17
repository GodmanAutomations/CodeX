#!/usr/bin/env bash
#
# verify-gadget.sh — print the state that matters for USB gadget networking.
# Runs ON THE PI. Read-only; safe to run any time.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

section() { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }

section "Host / OS"
hostnamectl 2>/dev/null || true
grep VERSION_CODENAME /etc/os-release 2>/dev/null || true

section "Network interfaces"
ip -br addr 2>/dev/null || true
printf '\nRoutes:\n'
ip route 2>/dev/null || true
if command -v nmcli >/dev/null 2>&1; then
  printf '\nActive NetworkManager connections:\n'
  nmcli -t con show --active 2>/dev/null || true
fi

section "USB gadget / kernel"
printf 'UDC (USB device controllers):\n'
# ls exits 0 on an empty-but-existing dir, so capture and test contents instead.
udc_list="$(ls -A /sys/class/udc 2>/dev/null || true)"
if [ -n "${udc_list}" ]; then
  printf '%s\n' "${udc_list}"
else
  echo "  (none — no device-mode controller bound)"
fi
printf '\nGadget modules:\n'
lsmod | grep -E 'dwc2|g_ether|g_serial|g_multi|libcomposite' || echo "  (none loaded)"
printf '\nRecent gadget kernel messages:\n'
journalctl -k -b --no-pager 2>/dev/null | grep -iE 'dwc2|g_ether|usb0|configfs' | tail -n 20 || true

section "Services / listening ports"
systemctl is-active ssh 2>/dev/null && echo "ssh: active" || echo "ssh: not active"
systemctl is-active wayvnc.service 2>/dev/null && echo "wayvnc: active" || echo "wayvnc: not active"
printf '\nListening on 22 / 5900:\n'
ss -ltnp 2>/dev/null | grep -E ':(22|5900)\s' || echo "  (nothing listening on 22/5900)"

printf '\n'
log "If usb0 has no address and there is no UDC, re-check the USB PORT and CABLE first."
