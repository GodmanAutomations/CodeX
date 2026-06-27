#!/usr/bin/env bash
set -euo pipefail

PYTHON="/Users/stephengodman/GodmanAutomations/godman-lab/.venv/bin/python"
SERVER="/Users/stephengodman/CodeX/codex_continuity/codex_continuity_mcp.py"

exec "$PYTHON" "$SERVER"
