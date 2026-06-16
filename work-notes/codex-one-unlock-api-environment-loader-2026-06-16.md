# CodeX One-Unlock API Environment Loader

Date: 2026-06-16

## Result

Repaired the CodeX secret-loading path so Codex tools can use API credentials after one 1Password-backed load instead of triggering 1Password repeatedly per tool call.

## Changed

- Added `/Users/stephengodman/000_AI/bin/codex-load-api-keys-once`.
- Added symlink `/Users/stephengodman/bin/codex-load-api-keys-once`.
- Updated `/Users/stephengodman/000_AI/bin/codex-op` to populate the macOS user environment before launch.
- Updated `/Users/stephengodman/000_AI/bin/codex-app-op` to populate/import the macOS user environment and launch Codex directly instead of wrapping the whole app in `op run`.
- Updated `/Users/stephengodman/Candice-Code/mcp_servers/trello_mcp_launcher.sh` so Trello checks inherited env, then `launchctl` macOS user env, then 1Password fallback.
- Updated `/Users/stephengodman/.codex/config.toml` Trello MCP timeout from 12 to 35 seconds.
- Added `/Users/stephengodman/_handoff/codex/TICKET-stale-api-key-env-audit.md` for later stale-key review.
- Added explicit 1Password/Computer Use permission language to `/Users/stephengodman/.codex/AGENTS.md` and `/Users/stephengodman/Candice-Code/AGENTS.md`.
- Added CodeX MCP build latitude language to `/Users/stephengodman/Candice-Code/AGENTS.md`.

## Verification

- Shell syntax passed for:
  - `codex-load-api-keys-once`
  - `codex-op`
  - `codex-app-op`
  - `trello_mcp_launcher.sh`
- Codex TOML parse passed.
- One-shot loader resolved and loaded 29 variables into the macOS user environment.
- Redacted launchctl presence check showed Trello, OpenAI, Anthropic, Pushover, Google, and Gemini variables present.
- Trello MCP status returned `credential_source=mac_user_environment`, `op_env_loaded=false`, and `op_resolution.status=not_attempted`.
- Read-only Trello smoke test found the Byrd card successfully without writing to Trello.

## Notes

- The current already-running Codex process still cannot mutate its own parent environment. New child tools can read the macOS user environment path, and new Codex sessions launched through the repaired launchers should inherit the loaded variables.
- No plaintext secret file was written. No secret values were printed in this receipt.
