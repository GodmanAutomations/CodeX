#!/usr/bin/env bash
#
# write-user-data.sh — write a Trixie cloud-init user-data file onto a freshly
# flashed boot partition to enable USB gadget networking + SSH on first boot.
#
# Runs on the HOST, after flashing Raspberry Pi OS Trixie (image dated
# 2025-10-20 or later, which ships rpi-usb-gadget + cloud-init on the boot part).
#
# Usage:
#   ./write-user-data.sh                 # plaintext password from gadget.env
#   ./write-user-data.sh --ssh-key       # SSH public key only (recommended)
#   ./write-user-data.sh --ssh-key /path/to/key.pub
#
# Config (from config/gadget.env, overridable via env):
#   BOOTFS, PI_HOSTNAME, PI_USER, PI_PASSWORD, PI_TIMEZONE, PI_SSH_PUBKEY_FILE
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

USE_KEY=0
KEY_FILE=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --ssh-key)
      USE_KEY=1
      # Optional path argument may follow.
      if [ "${2:-}" ] && [ "${2#-}" = "${2}" ]; then
        KEY_FILE="$2"
        shift
      fi
      ;;
    -h | --help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) die "Unknown argument: $1" ;;
  esac
  shift
done

require BOOTFS
require PI_HOSTNAME
require PI_USER
: "${PI_TIMEZONE:=America/Chicago}"

[ -d "${BOOTFS}" ] || die "BOOTFS is not a directory: ${BOOTFS}"
# On genuine Trixie boot partitions cloud-init ships a user-data stub. We warn
# rather than hard-fail so the script also works on a manually prepared volume.
[ -f "${BOOTFS}/user-data" ] || warn "No existing user-data in ${BOOTFS} (continuing anyway)."

GROUPS_LINE="users,adm,dialout,audio,netdev,video,plugdev,cdrom,games,input,gpio,spi,i2c,render,sudo"
TARGET="${BOOTFS}/user-data"

if [ "${USE_KEY}" = "1" ]; then
  : "${KEY_FILE:=${PI_SSH_PUBKEY_FILE:-}}"
  [ -n "${KEY_FILE}" ] || die "SSH key mode: set PI_SSH_PUBKEY_FILE or pass a path."
  [ -f "${KEY_FILE}" ] || die "SSH public key not found: ${KEY_FILE}"
  # Indent every non-blank key line into the YAML list. This supports a file
  # containing multiple keys and preserves each key's trailing comment.
  PUBKEYS="$(sed '/^[[:space:]]*$/d; s/^/      - /' "${KEY_FILE}")"
  [ -n "${PUBKEYS}" ] || die "No usable keys found in ${KEY_FILE}."
  log "Writing key-authenticated user-data (key: ${KEY_FILE})"
  cat > "${TARGET}" <<EOF
#cloud-config
hostname: ${PI_HOSTNAME}
manage_etc_hosts: true
timezone: ${PI_TIMEZONE}

users:
  - name: ${PI_USER}
    groups: ${GROUPS_LINE}
    shell: /bin/bash
    lock_passwd: true
    ssh_authorized_keys:
${PUBKEYS}
    sudo: ALL=(ALL) NOPASSWD:ALL

rpi:
  enable_usb_gadget: true

enable_ssh: true
ssh_pwauth: false
EOF
else
  require PI_PASSWORD
  [ "${PI_PASSWORD}" = "CHANGE-ME-NOW" ] && warn "PI_PASSWORD is still the placeholder — change it in config/gadget.env."
  log "Writing password-authenticated user-data (consider --ssh-key instead)"
  # Escape for a YAML double-quoted scalar so a password containing " or \\ can't
  # produce invalid user-data: backslashes first, then double-quotes.
  pw_yaml="${PI_PASSWORD//\\/\\\\}"
  pw_yaml="${pw_yaml//\"/\\\"}"
  cat > "${TARGET}" <<EOF
#cloud-config
hostname: ${PI_HOSTNAME}
manage_etc_hosts: true
timezone: ${PI_TIMEZONE}

users:
  - name: ${PI_USER}
    groups: ${GROUPS_LINE}
    shell: /bin/bash
    lock_passwd: false
    # Password login is enabled, so require the password for sudo (defense in
    # depth vs a compromised account). The key-only variant uses NOPASSWD
    # because it locks the password and has nothing to authenticate sudo with.
    sudo: ALL=(ALL) ALL

# Set the login password via the chpasswd module (the supported cloud-init
# mechanism; the per-user 'plain_text_passwd' key is unreliable across versions).
chpasswd:
  expire: false
  users:
    - name: ${PI_USER}
      password: "${pw_yaml}"
      type: text

rpi:
  enable_usb_gadget: true

enable_ssh: true
EOF
fi

sync
log "Wrote ${TARGET}"
log "Next: eject the card, connect the correct USB port to the host, and boot."
