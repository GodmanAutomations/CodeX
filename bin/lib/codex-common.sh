#!/usr/bin/env bash
# Shared Bash plumbing for CodeX room wrappers. Keep this file small and
# business-logic free; callers own their own traps and policy decisions.

codex_init_paths() {
  CODEX_COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CODEX_ROOT="${CODEX_ROOT:-$(cd "$CODEX_COMMON_DIR/../.." && pwd)}"
  CODEX_BIN_DIR="$CODEX_ROOT/bin"
  CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
  export CODEX_COMMON_DIR CODEX_ROOT CODEX_BIN_DIR CODEX_HOME
}

codex_require_cmd() {
  local cmd="${1:-}"
  local hint="${2:-}"
  if [ -z "$cmd" ]; then
    printf 'error: codex_require_cmd needs a command name\n' >&2
    return 2
  fi
  if command -v "$cmd" >/dev/null 2>&1; then
    return 0
  fi
  if [ -n "$hint" ]; then
    printf 'error: required command not found: %s (%s)\n' "$cmd" "$hint" >&2
  else
    printf 'error: required command not found: %s\n' "$cmd" >&2
  fi
  return 1
}

case "$(declare -p CODEX_CLEANUP_PATHS 2>/dev/null || true)" in
  "declare -a "*|"declare -ax "*) ;;
  *) CODEX_CLEANUP_PATHS=() ;;
esac

codex_cleanup_add() {
  local path
  for path in "$@"; do
    [ -n "$path" ] || continue
    CODEX_CLEANUP_PATHS+=("$path")
  done
}

codex_cleanup_run() {
  local path
  if [ "${CODEX_CLEANUP_PATHS+x}" ]; then
    for path in "${CODEX_CLEANUP_PATHS[@]}"; do
      [ -n "$path" ] || continue
      local cleanup_root
      cleanup_root="${TMPDIR:-/tmp}"
      cleanup_root="${cleanup_root%/}"
      case "$path" in
        /|"${HOME:-__codex_home_unset__}"|"${HOME:-__codex_home_unset__}"/*|"${CODEX_ROOT:-__codex_root_unset__}"|"${CODEX_ROOT:-__codex_root_unset__}"/*)
          printf 'error: refusing unsafe cleanup path: %s\n' "$path" >&2
          return 2
          ;;
      esac
      case "$path" in
        "$cleanup_root"/*|/tmp/*|/var/folders/*) ;;
        *)
          printf 'error: cleanup path is outside temp roots: %s\n' "$path" >&2
          return 2
          ;;
      esac
      if [ -e "$path" ] || [ -L "$path" ]; then
        rm -rf -- "$path"
      fi
    done
  fi
}

codex_mktemp_dir() {
  local prefix="${1:-codex}"
  mktemp -d "${TMPDIR:-/tmp}/${prefix}.XXXXXX"
}

codex_run_capture() {
  local outfile="${1:-}"
  if [ -z "$outfile" ]; then
    printf 'error: codex_run_capture needs an output file\n' >&2
    return 2
  fi
  shift
  if [ "$#" -eq 0 ]; then
    printf 'error: codex_run_capture needs a command\n' >&2
    return 2
  fi
  "$@" >"$outfile" 2>&1
}

codex_append_log() {
  local file="${1:-}"
  if [ -z "$file" ]; then
    printf 'error: codex_append_log needs a file\n' >&2
    return 2
  fi
  shift
  printf '%s\n' "$*" >>"$file"
}

codex_run_without_env() {
  (
    local var
    local saw_separator=0
    while [ "$#" -gt 0 ]; do
      if [ "$1" = "--" ]; then
        saw_separator=1
        shift
        break
      fi
      var="$1"
      case "$var" in
        ''|*[!A-Za-z0-9_]*|[0-9]*)
          printf 'error: invalid environment variable name: %s\n' "$var" >&2
          return 2
          ;;
      esac
      shift
      unset "$var"
    done
    if [ "$saw_separator" -eq 0 ]; then
      printf 'error: codex_run_without_env needs -- before the command\n' >&2
      return 2
    fi
    if [ "$#" -eq 0 ]; then
      printf 'error: codex_run_without_env needs a command after --\n' >&2
      return 2
    fi
    exec "$@"
  )
}
