# CodeX Friction Control Surface - 2026-06-16

## Result

Reduced the biggest CodeX friction points in one slice:

- CodeX launch is app-only by default.
- CLI launch compatibility now routes to the Codex desktop app.
- Added one plain status dashboard.
- Added one plain MCP control panel.
- Added one work-notes receipt index.
- Added global shortcuts in `/Users/stephengodman/bin`.
- Updated room docs and routing so future CodeX knows the intended surfaces.

## App-Only Launch

Changed:

- `/Users/stephengodman/Candice-Code/bin/codex-launch`
- `/Users/stephengodman/000_AI/bin/codex-op`
- `/Users/stephengodman/Candice-Code/bin/codex-ensure-standalone`
- `/Users/stephengodman/Candice-Code/AGENTS.md`
- `/Users/stephengodman/Candice-Code/README.md`
- `/Users/stephengodman/Candice-Code/QUICKSTART.md`

Behavior:

- `/Users/stephengodman/Candice-Code/bin/codex-launch` now opens the Codex desktop app through `/Users/stephengodman/bin/codex-app-op`.
- `/Users/stephengodman/bin/codex-op` remains as a compatibility command, but it also launches the app instead of starting a Codex CLI session.
- `/Users/stephengodman/Candice-Code/bin/codex-ensure-standalone` now treats app-only mode as normal and skips CLI-only MCP checks unless `CODEX_ALLOW_CLI_PREFLIGHT=1` is set.

Backups:

- `/Users/stephengodman/Candice-Code/backups/app-only-codex-20260616-0238/`

## New Commands

- `/Users/stephengodman/Candice-Code/bin/codex-status`
- `/Users/stephengodman/Candice-Code/bin/codex-mcp`
- `/Users/stephengodman/Candice-Code/bin/codex-receipts-index`

Global shortcuts:

- `/Users/stephengodman/bin/codex-status`
- `/Users/stephengodman/bin/codex-mcp`
- `/Users/stephengodman/bin/codex-receipts-index`
- `/Users/stephengodman/bin/trello-find-card`
- `/Users/stephengodman/bin/trello-read-work-order`
- `/Users/stephengodman/bin/trello-attach-card-photo`

## What They Do

`codex-status`

- Shows app-only mode.
- Shows Codex app and 1Password app process status.
- Shows redacted API environment presence from current process and macOS user environment.
- Shows Trello MCP credential source and tool count.
- Checks Pi/Candice home path.
- Lists latest receipts and handoffs.

`codex-mcp`

- `codex-mcp status`
- `codex-mcp tools`
- `codex-mcp tools --include-writes`
- `codex-mcp trello-test Byrd`
- `codex-mcp doctor`
- `codex-mcp reload`

`codex-receipts-index`

- Writes `/Users/stephengodman/Candice-Code/work-notes/INDEX.md`.
- Gives Stephen a plain newest-first table of recent receipts by lane and title.

## Verification

Passed:

- `bash -n` for app-only launch scripts.
- Python compile for `codex-status`, `codex-mcp`, and `codex-receipts-index`.
- `codex-mcp status` returned Trello OK with `credential_source=mac_user_environment`.
- `codex-mcp tools --include-writes` found 47 Trello MCP tools.
- `codex-mcp trello-test Byrd` found the Billy Byrd card read-only.
- `codex-mcp doctor` returned OK and did not attempt 1Password.
- `codex-mcp reload` loaded 29 variables and Trello still used `mac_user_environment`.
- `codex-status --skip-pi` returned OK, showed app-only mode OK, Codex app running, Trello MCP OK, and 47 tools.
- `codex-status` with Pi check reached the Pi and found `candice_home=/opt/telegram/candice_v2`.
- `codex-ensure-standalone --check` passed app-only preflight and skipped CLI MCP checks.
- `codex-receipts-index --limit 120` wrote `/Users/stephengodman/Candice-Code/work-notes/INDEX.md`.

## Safety

- No Trello writes were made.
- No Pi writes were made.
- No plaintext secret file was created.
- No secret values were printed in receipts or command output.
