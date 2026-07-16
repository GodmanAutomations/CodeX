#!/usr/bin/env bash
#
# harden-ssh.sh — disable password/root SSH login and lock access to $PI_USER.
#
# Runs ON THE PI. Only run this AFTER you have confirmed key-based SSH works —
# otherwise you can lock yourself out. It refuses to run if no authorized_keys
# exists for the user, unless you pass --force.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

[ "$(id -u)" -eq 0 ] || die "Run as root (sudo $0)."

: "${PI_USER:=${SUDO_USER:-pi}}"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

user_home="$(getent passwd "${PI_USER}" | cut -d: -f6)"
: "${user_home:=/home/${PI_USER}}"
keyfile="${user_home}/.ssh/authorized_keys"
if [ ! -s "${keyfile}" ] && [ "${FORCE}" -ne 1 ]; then
  die "No authorized_keys for ${PI_USER} at ${keyfile}. Set up a key first, or pass --force to proceed anyway (risky)."
fi

drop="/etc/ssh/sshd_config.d/99-hardening.conf"
mkdir -p /etc/ssh/sshd_config.d
cat > "${drop}" <<EOF
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
UsePAM yes
AllowUsers ${PI_USER}
EOF
log "Wrote ${drop}"

# Validate config before reloading so a typo can't break sshd.
if sshd -t; then
  systemctl reload ssh
  log "sshd config valid; reloaded."
else
  rm -f "${drop}"
  die "sshd -t failed; removed ${drop} and did NOT reload. No changes applied."
fi

log "SSH hardened: password + root login disabled, access limited to ${PI_USER}."
log "Keep your existing session open and verify a NEW key login before disconnecting."
