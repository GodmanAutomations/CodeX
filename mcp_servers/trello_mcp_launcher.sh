#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${TRELLO_MCP_ENV_FILE:-/Users/stephengodman/.env.1password}"
PYTHON_BIN="${TRELLO_MCP_PYTHON:-/Users/stephengodman/000_AI/bin/python3}"
SERVER_PATH="${TRELLO_MCP_SERVER:-/Users/stephengodman/CodeX/mcp_servers/trello_mcp_server.py}"
OP_BIN="${OP_BIN:-op}"
if ! command -v "$OP_BIN" >/dev/null 2>&1 && [[ -x /opt/homebrew/bin/op ]]; then
  OP_BIN="/opt/homebrew/bin/op"
fi
OP_TIMEOUT="${TRELLO_OP_RUN_TIMEOUT_SECONDS:-35}"
LAST_OP_ENV_STATUS="not_attempted"
LAST_OP_ENV_DETAIL=""

export TRELLO_DISABLE_OP_FALLBACK="${TRELLO_DISABLE_OP_FALLBACK:-1}"

has_trello_env() {
  [[ -n "${TRELLO_API_KEY:-${TRELLO_KEY:-}}" && -n "${TRELLO_API_TOKEN:-${TRELLO_TOKEN:-}}" ]]
}

load_launchctl_env() {
  local name value
  for name in TRELLO_API_KEY TRELLO_KEY TRELLO_API_TOKEN TRELLO_TOKEN; do
    value="$(/bin/launchctl getenv "$name" 2>/dev/null || true)"
    [[ -n "$value" ]] && export "$name=$value"
  done
  return 0
}

load_op_env() {
  LAST_OP_ENV_STATUS="attempted"
  LAST_OP_ENV_DETAIL=""

  if ! command -v "$OP_BIN" >/dev/null 2>&1; then
    LAST_OP_ENV_STATUS="missing_op_cli"
    return 1
  fi
  if [[ ! -f "$ENV_FILE" ]]; then
    LAST_OP_ENV_STATUS="env_file_missing"
    return 1
  fi
  local tmp
  tmp="$(mktemp "${TMPDIR:-/tmp}/trello-mcp-env.XXXXXX")"
  chmod 600 "$tmp"
  trap 'rm -f "$tmp"' RETURN

  local op_status=0
  if command -v timeout >/dev/null 2>&1; then
    timeout "$OP_TIMEOUT" "$OP_BIN" run --env-file "$ENV_FILE" -- "$PYTHON_BIN" -c '
import os
import sys
from pathlib import Path

target = Path(sys.argv[1])
names = (
    "TRELLO_API_KEY",
    "TRELLO_KEY",
    "TRELLO_API_TOKEN",
    "TRELLO_TOKEN",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENERATIVE_AI_API_KEY",
)
target.write_text("".join("%s=%s\n" % (name, os.environ.get(name, "")) for name in names), encoding="utf-8")
' "$tmp" 2>/dev/null || op_status=$?
  else
    "$PYTHON_BIN" - "$OP_TIMEOUT" "$OP_BIN" "$ENV_FILE" "$PYTHON_BIN" "$tmp" 2>/dev/null <<'PY' || op_status=$?
import subprocess
import sys

timeout_seconds = int(sys.argv[1])
op_bin = sys.argv[2]
env_file = sys.argv[3]
python_bin = sys.argv[4]
target_path = sys.argv[5]
probe = """
import os
import sys
from pathlib import Path

target = Path(sys.argv[1])
names = (
    "TRELLO_API_KEY",
    "TRELLO_KEY",
    "TRELLO_API_TOKEN",
    "TRELLO_TOKEN",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENERATIVE_AI_API_KEY",
)
target.write_text("".join("%s=%s\\n" % (name, os.environ.get(name, "")) for name in names), encoding="utf-8")
"""

try:
    completed = subprocess.run(
        [op_bin, "run", "--env-file", env_file, "--", python_bin, "-c", probe, target_path],
        timeout=timeout_seconds,
    )
except subprocess.TimeoutExpired:
    sys.exit(124)
sys.exit(completed.returncode)
PY
  fi
  if [[ "$op_status" -ne 0 ]]; then
    if [[ "$op_status" -eq 124 ]]; then
      LAST_OP_ENV_STATUS="op_run_timeout"
    else
      LAST_OP_ENV_STATUS="op_run_failed"
    fi
    LAST_OP_ENV_DETAIL="exit_${op_status}"
    return 1
  fi

  while IFS='=' read -r name value; do
    case "$name" in
      TRELLO_API_KEY|TRELLO_KEY|TRELLO_API_TOKEN|TRELLO_TOKEN|GEMINI_API_KEY|GOOGLE_API_KEY|GOOGLE_GENERATIVE_AI_API_KEY)
        [[ -n "$value" ]] && export "$name=$value"
        ;;
    esac
  done <"$tmp"

  if has_trello_env; then
    LAST_OP_ENV_STATUS="loaded"
    return 0
  fi

  LAST_OP_ENV_STATUS="incomplete_trello_env"
  return 1
}

status_json() {
  local source="$1"
  local op_loaded="$2"
  local elapsed="$3"
  local env_file_mode=""
  local launcher_mode=""

  [[ -f "$ENV_FILE" ]] && env_file_mode="$("$PYTHON_BIN" -c 'import os,sys; print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' "$ENV_FILE" 2>/dev/null || true)"
  launcher_mode="$("$PYTHON_BIN" -c 'import os,sys; print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' "$0" 2>/dev/null || true)"

  TRELLO_MCP_STATUS_SOURCE="$source" \
  TRELLO_MCP_STATUS_OP_LOADED="$op_loaded" \
  TRELLO_MCP_STATUS_ELAPSED="$elapsed" \
  TRELLO_MCP_STATUS_ENV_FILE_MODE="$env_file_mode" \
  TRELLO_MCP_STATUS_LAUNCHER_MODE="$launcher_mode" \
  TRELLO_MCP_STATUS_OP_ENV_STATUS="$LAST_OP_ENV_STATUS" \
  TRELLO_MCP_STATUS_OP_ENV_DETAIL="$LAST_OP_ENV_DETAIL" \
  TRELLO_MCP_STATUS_OP_TIMEOUT="$OP_TIMEOUT" \
  "$PYTHON_BIN" - <<'PY'
import json
import os
from pathlib import Path

env_file = Path(os.environ.get("TRELLO_MCP_ENV_FILE", "/Users/stephengodman/.env.1password"))
server_path = Path(os.environ.get("TRELLO_MCP_SERVER", "/Users/stephengodman/CodeX/mcp_servers/trello_mcp_server.py"))

payload = {
    "ok": bool((os.getenv("TRELLO_API_KEY") or os.getenv("TRELLO_KEY")) and (os.getenv("TRELLO_API_TOKEN") or os.getenv("TRELLO_TOKEN"))),
    "credential_source": os.getenv("TRELLO_MCP_STATUS_SOURCE") or "unknown",
    "op_env_loaded": os.getenv("TRELLO_MCP_STATUS_OP_LOADED") == "true",
    "op_timeout_seconds": os.getenv("TRELLO_MCP_STATUS_OP_TIMEOUT") or os.getenv("TRELLO_OP_RUN_TIMEOUT_SECONDS", "35"),
    "elapsed_seconds": int(os.getenv("TRELLO_MCP_STATUS_ELAPSED") or "0"),
    "op_resolution": {
        "status": os.getenv("TRELLO_MCP_STATUS_OP_ENV_STATUS") or "unknown",
        "detail": os.getenv("TRELLO_MCP_STATUS_OP_ENV_DETAIL") or None,
    },
    "environment": {
        "key_present": bool(os.getenv("TRELLO_API_KEY") or os.getenv("TRELLO_KEY")),
        "token_present": bool(os.getenv("TRELLO_API_TOKEN") or os.getenv("TRELLO_TOKEN")),
        "gemini_key_present": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")),
    },
    "paths": {
        "env_file": str(env_file),
        "env_file_exists": env_file.exists(),
        "env_file_mode": os.getenv("TRELLO_MCP_STATUS_ENV_FILE_MODE") or None,
        "server_path": str(server_path),
        "server_exists": server_path.exists(),
        "launcher_mode": os.getenv("TRELLO_MCP_STATUS_LAUNCHER_MODE") or None,
    },
    "safety": {
        "secrets_returned": False,
        "trello_writes": False,
        "google_drive_writes": False,
        "pi5_writes": False,
    },
}
print(json.dumps(payload, indent=2, sort_keys=True))
PY
}

doctor_json() {
  local include_live="$1"
  local source="$2"
  local op_loaded="$3"
  local elapsed="$4"

  TRELLO_MCP_STATUS_SOURCE="$source" \
  TRELLO_MCP_STATUS_OP_LOADED="$op_loaded" \
  TRELLO_MCP_STATUS_ELAPSED="$elapsed" \
  TRELLO_MCP_STATUS_OP_ENV_STATUS="$LAST_OP_ENV_STATUS" \
  TRELLO_MCP_STATUS_OP_ENV_DETAIL="$LAST_OP_ENV_DETAIL" \
  TRELLO_MCP_DOCTOR_INCLUDE_LIVE="$include_live" \
  "$PYTHON_BIN" - <<'PY'
import importlib.util
import json
import os

server_path = os.environ.get("TRELLO_MCP_SERVER", "/Users/stephengodman/CodeX/mcp_servers/trello_mcp_server.py")
include_live = os.environ.get("TRELLO_MCP_DOCTOR_INCLUDE_LIVE") == "true"

spec = importlib.util.spec_from_file_location("trello_mcp_server_doctor", server_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
payload = module.trello_runtime_diagnostics(include_live_health=include_live)
payload["launcher_runtime"] = {
    "credential_source": os.environ.get("TRELLO_MCP_STATUS_SOURCE") or "unknown",
    "op_env_loaded": os.environ.get("TRELLO_MCP_STATUS_OP_LOADED") == "true",
    "elapsed_seconds": int(os.environ.get("TRELLO_MCP_STATUS_ELAPSED") or "0"),
    "doctor_live_requested": include_live,
    "op_resolution": {
        "status": os.environ.get("TRELLO_MCP_STATUS_OP_ENV_STATUS") or "unknown",
        "detail": os.environ.get("TRELLO_MCP_STATUS_OP_ENV_DETAIL") or None,
    },
}
payload.setdefault("safety", {})["secrets_returned"] = False
print(json.dumps(payload, indent=2, sort_keys=True))
PY
}

if [[ "${1:-}" == "--status" ]]; then
  start_seconds="$SECONDS"
  source="unavailable"
  op_loaded="false"
  if has_trello_env; then
    source="existing_environment"
  else
    load_launchctl_env
    if has_trello_env; then
      source="mac_user_environment"
    elif load_op_env && has_trello_env; then
      source="op_env_file"
      op_loaded="true"
    fi
  fi
  status_json "$source" "$op_loaded" "$((SECONDS - start_seconds))"
  exit 0
fi

if [[ "${1:-}" == "--doctor" || "${1:-}" == "--doctor-live" ]]; then
  start_seconds="$SECONDS"
  source="unavailable"
  op_loaded="false"
  include_live="false"
  [[ "${1:-}" == "--doctor-live" ]] && include_live="true"
  if has_trello_env; then
    source="existing_environment"
  else
    load_launchctl_env
    if has_trello_env; then
      source="mac_user_environment"
    elif load_op_env && has_trello_env; then
      source="op_env_file"
      op_loaded="true"
    fi
  fi
  doctor_json "$include_live" "$source" "$op_loaded" "$((SECONDS - start_seconds))"
  exit 0
fi

load_launchctl_env
has_trello_env || load_op_env || true

exec "$PYTHON_BIN" "$SERVER_PATH" "$@"
