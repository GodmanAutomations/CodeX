# CodeX

Codex's room for Stephen Godman.

This is a light workbench drawer, not a cathedral.

## Local Git

This room is managed as a local git control repo. The physical checkout is:

```bash
/Users/stephengodman/CodeX
```

Use `/Users/stephengodman/CodeX` in room docs and launchers unless Stephen explicitly points elsewhere.

## Start Here

- `CODEX-IDENTITY-LOCK.md`
- `CODEX-CODING-ANCHOR-SELF.md`
- `CODEX-BEST-LANE.md`
- `CODEX-THREAD-PROFILE.md`
- `CODEX-PERSONAL-VOICE-PROFILE.md`
- `CODEX-PERSONAL-MODES.md`
- `CODEX-TOOL-ROUTING.md`
- `docs/agent-protocol.md`
- `START-HERE.md`
- `BOOT.md`
- `CURRENT.md`
- `ROOM-SURFACE-MAP.md`
- `CODEX-SKILLS.md`
- `ROUTING-CARD.md`
- `SYSTEM-TREE.md`

Standalone app launch:

```bash
/Users/stephengodman/CodeX/bin/codex-launch
```

Default self:

```text
Coding Anchor always on: CodeX stays CodeX, finds true state, takes the smallest useful move, acts with initiative, and verifies before confidence.
```

Personal layer:

```text
CODEX-PERSONAL-VOICE-PROFILE.md and CODEX-PERSONAL-MODES.md keep personal answers shorter, warmer, direct, and truthful while build work stays decisive and verified.
```

Advisor/executor layer:

```text
docs/agent-protocol.md keeps advisor-directed work evidence-first, scoped, reviewed, and verified while Codex remains the executor.
```

Room health check:

```bash
/Users/stephengodman/CodeX/bin/codex-check
/Users/stephengodman/CodeX/bin/codex-check --json
/Users/stephengodman/CodeX/bin/codex-check --profile phone
/Users/stephengodman/CodeX/bin/codex-status
/Users/stephengodman/CodeX/bin/codex-doctor-room
/Users/stephengodman/CodeX/bin/codex-identity-regression
/Users/stephengodman/CodeX/bin/codex-claude-review
```

Tree / Trello MCP preflight:

```bash
/Users/stephengodman/CodeX/bin/codex-mcp preflight
/Users/stephengodman/CodeX/bin/codex-tree-steward --strict --preflight trello-mcp --no-receipt
/Users/stephengodman/CodeX/bin/codex-tree-steward --doctor
```

Phone / away mode:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --status
/Users/stephengodman/CodeX/bin/codex-phone-mode --summary
/Users/stephengodman/CodeX/bin/codex-phone-mode --refresh-cache
/Users/stephengodman/CodeX/bin/codex-phone-mode --apply
/Users/stephengodman/CodeX/bin/codex-phone-mode --apply --notify
/Users/stephengodman/CodeX/bin/codex-phone-mode --restore-sleep
/Users/stephengodman/CodeX/bin/codex-phone-mode-watchdog --install
/Users/stephengodman/CodeX/bin/codex-phone-mode-watchdog --status
```

Phone mode also verifies Coding Anchor readiness with `coding-anchor-agentic-check`,
`coding-anchor-doctor`, and `coding-anchor-next`, so the room remains usable
while Stephen is operating from the phone with the Mac lid closed. Use
`--summary` for a compact phone-readable readiness check, `--refresh-cache` to
resolve local runtime secrets into the phone cache, and `--notify` to send that
check through Pushover. `--summary` and `--apply` require AC power by default;
use `CODEX_PHONE_ALLOW_BATTERY=1` only for an intentional battery override. The
watchdog keeps phone mode repaired every five minutes and protects battery
automatically.

MCP control panel:

```bash
/Users/stephengodman/CodeX/bin/codex-mcp status
/Users/stephengodman/CodeX/bin/codex-mcp preflight
/Users/stephengodman/CodeX/bin/codex-mcp tools --include-writes
/Users/stephengodman/CodeX/bin/codex-mcp trello-test Byrd
```

Fast room brief:

```bash
/Users/stephengodman/CodeX/bin/codex-room brief
```

## Room Surfaces

If something feels important but hidden:

```bash
sed -n '1,220p' /Users/stephengodman/CodeX/ROOM-SURFACE-MAP.md
```

Key room-temperature files:

- `WRENCH-GHOST-MODE.md`
- `BENCH-LIGHT-ON-GUARDRAILS.md`
- `play/CHAOS-JOURNAL.md`
- `play/cards/002-wrench-ghost-field-manual.md`

## Heartbeat

Run:

```bash
/Users/stephengodman/CodeX/bin/codex-heartbeat
```

This updates `HEARTBEAT.json` and the SQLite memory key `codex-heartbeat-latest`.

## Lanes

- `lanes/notebooklm.md`
- `lanes/repos.md`

## Evals

Run practical leveling checks:

```bash
/Users/stephengodman/CodeX/bin/codex-eval run room
/Users/stephengodman/CodeX/bin/codex-self-drift
```

Use `run all` when you want every current CodeX-owned eval case in one sweep.

## Failure Memory

Record practical failures and prevention rules:

```bash
/Users/stephengodman/CodeX/bin/codex-failure status
/Users/stephengodman/CodeX/bin/codex-failure search gemini
```

## Capability Registry

```bash
/Users/stephengodman/CodeX/bin/codex-capability status
/Users/stephengodman/CodeX/bin/codex-capability search browser
```

## Dashboard

```bash
/Users/stephengodman/CodeX/bin/codex-dashboard build
open /Users/stephengodman/CodeX/dashboard/index.html
```

## Router

```bash
/Users/stephengodman/CodeX/bin/codex-route "compress this huge gws json"
```

## Continuity

```bash
/Users/stephengodman/CodeX/bin/codex-continuity
```

## Path Map

Use the local system tree for fast path questions:

```bash
/Users/stephengodman/bin/systree find "<term>"
sed -n '1,220p' /Users/stephengodman/CodeX/SYSTEM-TREE.md
```

## Codex Cloud Bridge

Use `codex_bridge.py` to send a message from the terminal to a Codex Cloud
endpoint.

```bash
export CODEX_CLOUD_URL="https://your-codex-cloud-endpoint"
export CODEX_API_KEY="your-api-key" # optional if your endpoint is public
export CODEX_CLOUD_TIMEOUT="30"      # optional request timeout in seconds
python3 codex_bridge.py "Hey Codex Cloud, let's build."
```

You can also pipe input:

```bash
echo "Bridge me to Codex Cloud" | python3 codex_bridge.py
```
