#!/usr/bin/env bash
set -euo pipefail

fail=0

say() {
  printf '%s\n' "$*"
}

check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    say "FAIL missing command: $1"
    fail=1
    return 1
  fi
  return 0
}

say "1PASSWORD ENVIRONMENTS CLI CHECK"
say "================================"

if ! check_command op; then
  say
  say "Install 1Password CLI before attempting Environments CLI work."
  exit 1
fi

op_path="$(command -v op)"
op_version="$(op --version 2>/dev/null || true)"

say "op path: ${op_path}"
say "op version: ${op_version:-unknown}"
say

if op environment --help >/tmp/codex-op-environment-help.$$ 2>/tmp/codex-op-environment-err.$$; then
  say "PASS op environment command is available"
  if grep -qE '(^|[[:space:]])read([[:space:]]|$)' /tmp/codex-op-environment-help.$$; then
    say "PASS op environment help mentions read"
  else
    say "WARN op environment exists, but help output did not obviously mention read"
  fi
else
  say "FAIL op environment command is not available"
  sed -n '1,8p' /tmp/codex-op-environment-err.$$ | sed 's/^/  /'
  fail=1
fi

rm -f /tmp/codex-op-environment-help.$$ /tmp/codex-op-environment-err.$$

if op run --help 2>/dev/null | grep -q -- '--environment'; then
  say "PASS op run exposes --environment"
else
  say "FAIL op run does not expose --environment"
  fail=1
fi

say
if [ "$fail" -eq 0 ]; then
  say "RESULT pass: local op appears compatible with documented 1Password Environments CLI syntax."
else
  say "RESULT fail: do not use op environment or op run --environment locally yet."
  say "Use the configured 1password Codex MCP server for Environments work, or install the documented beta CLI channel first."
fi

exit "$fail"

