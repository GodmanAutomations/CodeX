#!/usr/bin/env bash
# Shared helpers for Gadget-Pi scripts.
#
# Source this near the top of every script:
#
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   # shellcheck source=common.sh
#   . "${SCRIPT_DIR}/../common.sh"
#
# It loads config/gadget.env (if present) without clobbering variables that are
# already set in the environment, and provides small logging/confirm helpers.

# Guard against double-sourcing. common.sh is meant to be sourced, not executed;
# the `|| exit 0` is a defensive no-op for the run-directly case.
if [ -n "${_GADGET_PI_COMMON_LOADED:-}" ]; then
  # shellcheck disable=SC2317  # reachable only when sourced a second time
  return 0 2>/dev/null || exit 0
fi
_GADGET_PI_COMMON_LOADED=1

# Locate the project root relative to this file (scripts/common.sh -> ..).
_COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GADGET_PI_ROOT="$(cd "${_COMMON_DIR}/.." && pwd)"
export GADGET_PI_ROOT

# Load config/gadget.env if it exists. The shipped gadget.env.example uses the
# `export VAR="${VAR:-default}"` form, so a value already set in the environment
# takes precedence — an inline `VAR=... ./script` override wins over the file.
_gadget_env="${GADGET_PI_ROOT}/config/gadget.env"
if [ -f "${_gadget_env}" ]; then
  # shellcheck source=/dev/null
  . "${_gadget_env}"
fi

# ---- Logging --------------------------------------------------------------
log()  { printf '\033[1;34m[gadget-pi]\033[0m %s\n' "$*" >&2; }
warn() { printf '\033[1;33m[gadget-pi] WARN:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[gadget-pi] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# require VAR — die if the named variable is empty.
require() {
  local name="$1"
  local val="${!name:-}"
  [ -n "${val}" ] || die "Required variable '${name}' is not set. Edit config/gadget.env or export it."
}

# confirm "message" — prompt y/N; die on anything but yes. Auto-confirms when
# GADGET_PI_ASSUME_YES=1 (useful for tests/automation).
confirm() {
  local msg="$1"
  if [ "${GADGET_PI_ASSUME_YES:-0}" = "1" ]; then
    log "Auto-confirming (GADGET_PI_ASSUME_YES=1): ${msg}"
    return 0
  fi
  printf '\033[1;33m%s [y/N] \033[0m' "${msg}" >&2
  local reply=""
  read -r reply || true
  case "${reply}" in
    y | Y | yes | YES) return 0 ;;
    *) die "Aborted by user." ;;
  esac
}

# need_cmd cmd — die if a required command is missing.
need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}
