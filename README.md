# CodeX

Codex's room for Stephen Godman.

This is a light workbench drawer, not a cathedral.

## Start Here

- `CODEX-IDENTITY-LOCK.md`
- `CODEX-CODING-ANCHOR-SELF.md`
- `START-HERE.md`
- `BOOT.md`
- `CURRENT.md`
- `ROOM-SURFACE-MAP.md`
- `CODEX-SKILLS.md`
- `ROUTING-CARD.md`
- `SYSTEM-TREE.md`

Standalone app launch:

```bash
/Users/stephengodman/Candice-Code/bin/codex-launch
```

Default self:

```text
Coding Anchor always on: CodeX stays CodeX, finds true state, takes the smallest useful move, acts with initiative, and verifies before confidence.
```

Room health check:

```bash
/Users/stephengodman/Candice-Code/bin/codex-status
/Users/stephengodman/Candice-Code/bin/codex-doctor-room
```

MCP control panel:

```bash
/Users/stephengodman/Candice-Code/bin/codex-mcp status
/Users/stephengodman/Candice-Code/bin/codex-mcp tools --include-writes
/Users/stephengodman/Candice-Code/bin/codex-mcp trello-test Byrd
```

Fast room brief:

```bash
/Users/stephengodman/Candice-Code/bin/codex-room brief
```

## Room Surfaces

If something feels important but hidden:

```bash
sed -n '1,220p' /Users/stephengodman/Candice-Code/ROOM-SURFACE-MAP.md
```

Key room-temperature files:

- `WRENCH-GHOST-MODE.md`
- `BENCH-LIGHT-ON-GUARDRAILS.md`
- `play/CHAOS-JOURNAL.md`
- `play/cards/002-wrench-ghost-field-manual.md`

## Heartbeat

Run:

```bash
/Users/stephengodman/Candice-Code/bin/codex-heartbeat
```

This updates `HEARTBEAT.json` and the SQLite memory key `codex-heartbeat-latest`.

## Lanes

- `lanes/notebooklm.md`
- `lanes/repos.md`

## Evals

Run practical leveling checks:

```bash
/Users/stephengodman/Candice-Code/bin/codex-eval run room
/Users/stephengodman/Candice-Code/bin/codex-self-drift
```

Use `run all` when you want every current CodeX-owned eval case in one sweep.

## Failure Memory

Record practical failures and prevention rules:

```bash
/Users/stephengodman/Candice-Code/bin/codex-failure status
/Users/stephengodman/Candice-Code/bin/codex-failure search gemini
```

## Capability Registry

```bash
/Users/stephengodman/Candice-Code/bin/codex-capability status
/Users/stephengodman/Candice-Code/bin/codex-capability search browser
```

## Dashboard

```bash
/Users/stephengodman/Candice-Code/bin/codex-dashboard build
open /Users/stephengodman/Candice-Code/dashboard/index.html
```

## Router

```bash
/Users/stephengodman/Candice-Code/bin/codex-route "compress this huge gws json"
```

## Continuity

```bash
/Users/stephengodman/Candice-Code/bin/codex-continuity
```

## Path Map

Use the local system tree for fast path questions:

```bash
/Users/stephengodman/bin/systree find "<term>"
sed -n '1,220p' /Users/stephengodman/Candice-Code/SYSTEM-TREE.md
```
