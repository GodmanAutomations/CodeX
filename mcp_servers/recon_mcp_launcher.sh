#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${RECON_MCP_PYTHON:-/Users/stephengodman/000_AI/bin/python3}"
SERVER_PATH="${RECON_MCP_SERVER:-/Users/stephengodman/CodeX/mcp_servers/recon_mcp_server.py}"
export RECON_DATA_ROOT="${RECON_DATA_ROOT:-/Users/stephengodman/GodmanAutomations/data}"

if [[ "${1:-}" == "--status" ]]; then
  "$PYTHON_BIN" - <<'PY'
import importlib.util
import json
import os
import sys
from pathlib import Path

server_path = Path(os.environ.get("RECON_MCP_SERVER", "/Users/stephengodman/CodeX/mcp_servers/recon_mcp_server.py"))
sys.path.insert(0, str(server_path.parent))
spec = importlib.util.spec_from_file_location("recon_mcp_server_status", server_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
payload = module.store.status()
payload["launcher"] = {
    "server_path": str(server_path),
    "server_exists": server_path.exists(),
    "python": os.environ.get("RECON_MCP_PYTHON", "/Users/stephengodman/000_AI/bin/python3"),
}
print(json.dumps(payload, indent=2, sort_keys=True))
PY
  exit 0
fi

exec "$PYTHON_BIN" "$SERVER_PATH" "$@"
