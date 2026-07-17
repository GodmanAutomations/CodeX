#!/usr/bin/env bash
#
# patch-bookworm-bootfs.sh — legacy fallback. Patch a freshly flashed Bookworm
# boot partition for USB Ethernet gadget mode (dwc2 + g_ether) and teach
# NetworkManager not to ignore the gadget interface.
#
# Runs on the HOST. Prefer the Trixie path (write-user-data.sh) unless you must
# stay on Bookworm. See docs/03-bookworm-fallback.md.
#
# Usage:
#   ./patch-bookworm-bootfs.sh                 # uses BOOTFS from gadget.env
#   ./patch-bookworm-bootfs.sh /path/to/bootfs
#
# Idempotent: safe to run twice. Backs up cmdline.txt before editing.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

BOOTFS="${1:-${BOOTFS:-}}"
require BOOTFS
[ -d "${BOOTFS}" ] || die "BOOTFS is not a directory: ${BOOTFS}"

CONFIG_TXT="${BOOTFS}/config.txt"
CMDLINE_TXT="${BOOTFS}/cmdline.txt"
FIRSTRUN_SH="${BOOTFS}/firstrun.sh"

[ -f "${CONFIG_TXT}" ]  || die "Missing ${CONFIG_TXT} (is this a Bookworm boot partition prepared by Raspberry Pi Imager?)"
[ -f "${CMDLINE_TXT}" ] || die "Missing ${CMDLINE_TXT}"
[ -f "${FIRSTRUN_SH}" ] || die "Missing ${FIRSTRUN_SH} (set a username/SSH in Raspberry Pi Imager so firstrun.sh exists, or see docs)."

# Back up the boot files we may edit (once — don't clobber an existing .bak).
for _f in "${CONFIG_TXT}" "${CMDLINE_TXT}" "${FIRSTRUN_SH}"; do
  [ -f "${_f}.bak" ] || cp "${_f}" "${_f}.bak"
done

# 1. Enable the dwc2 overlay. Match dwc2 with or without parameters
#    (e.g. dtoverlay=dwc2,dr_mode=peripheral) or trailing space so a real-world
#    config.txt doesn't get a duplicate appended.
if grep -qE '^dtoverlay=dwc2([,[:space:]].*)?$' "${CONFIG_TXT}"; then
  log "dwc2 overlay already present in config.txt"
else
  printf '\n[all]\ndtoverlay=dwc2\n' >> "${CONFIG_TXT}"
  log "Added dtoverlay=dwc2 to config.txt"
fi

# 2. Load dwc2,g_ether early via cmdline.txt (a single-line, space-separated
#    file). Append the token at end-of-line rather than depending on a specific
#    neighbour like `rootwait` (which may be the last token or absent), then
#    verify it landed so we never log success on a silent no-op.
if grep -q 'modules-load=dwc2,g_ether' "${CMDLINE_TXT}"; then
  log "cmdline.txt already loads dwc2,g_ether"
else
  # Use a temp file instead of `sed -i` — GNU and BSD/macOS sed disagree on the
  # `-i` syntax, and this script runs host-side on both. (The original was
  # already backed up to .bak above.)
  sed 's/[[:space:]]*$/ modules-load=dwc2,g_ether/' "${CMDLINE_TXT}" > "${CMDLINE_TXT}.tmp"
  mv "${CMDLINE_TXT}.tmp" "${CMDLINE_TXT}"
  grep -q 'modules-load=dwc2,g_ether' "${CMDLINE_TXT}" \
    || die "Failed to add modules-load to cmdline.txt (restore ${CMDLINE_TXT}.bak)."
  log "Patched cmdline.txt (backup: cmdline.txt.bak)"
fi

# 3. Inject NetworkManager connections + unmanaged-rule override into firstrun.sh
#    just before it deletes itself.
if grep -q 'usb0-dhcp' "${FIRSTRUN_SH}"; then
  log "firstrun.sh already patched for usb0"
else
  awk '
    /rm -f \/boot\/firstrun\.sh/ && !done {
      print "mkdir -p /etc/udev/rules.d"
      print "cp /usr/lib/udev/rules.d/85-nm-unmanaged.rules /etc/udev/rules.d/85-nm-unmanaged.rules"
      print "sed -i '\''s/^[^#]*gadget/# &/'\'' /etc/udev/rules.d/85-nm-unmanaged.rules"
      print "mkdir -p /etc/NetworkManager/system-connections"
      print "CONNFILE1=/etc/NetworkManager/system-connections/usb0-dhcp.nmconnection"
      print "UUID1=$(cat /proc/sys/kernel/random/uuid)"
      print "cat > ${CONNFILE1} <<EOFUSB1"
      print "[connection]"
      print "id=usb0-dhcp"
      print "uuid=${UUID1}"
      print "type=ethernet"
      print "interface-name=usb0"
      print "autoconnect-priority=100"
      print "autoconnect-retries=2"
      print ""
      print "[ethernet]"
      print ""
      print "[ipv4]"
      print "dhcp-timeout=3"
      print "method=auto"
      print ""
      print "[ipv6]"
      print "addr-gen-mode=default"
      print "method=auto"
      print ""
      print "[proxy]"
      print "EOFUSB1"
      print "CONNFILE2=/etc/NetworkManager/system-connections/usb0-ll.nmconnection"
      print "UUID2=$(cat /proc/sys/kernel/random/uuid)"
      print "cat > ${CONNFILE2} <<EOFUSB2"
      print "[connection]"
      print "id=usb0-ll"
      print "uuid=${UUID2}"
      print "type=ethernet"
      print "interface-name=usb0"
      print "autoconnect-priority=50"
      print ""
      print "[ethernet]"
      print ""
      print "[ipv4]"
      print "method=link-local"
      print ""
      print "[ipv6]"
      print "addr-gen-mode=default"
      print "method=auto"
      print ""
      print "[proxy]"
      print "EOFUSB2"
      print "chmod 600 ${CONNFILE1} ${CONNFILE2}"
      done=1
    }
    { print }
  ' "${FIRSTRUN_SH}" > "${FIRSTRUN_SH}.new"
  mv "${FIRSTRUN_SH}.new" "${FIRSTRUN_SH}"
  chmod +x "${FIRSTRUN_SH}"
  log "Patched firstrun.sh with usb0 NetworkManager connections"
fi

sync
log "Bookworm boot partition patched at ${BOOTFS}"
log "Remember: also place a userconf.txt + empty 'ssh' file if not set via Imager (see docs/03)."
