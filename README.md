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

Room health check:

```bash
/Users/stephengodman/CodeX/bin/codex-status
/Users/stephengodman/CodeX/bin/codex-doctor-room
```

Tree / Trello MCP preflight:

```bash
/Users/stephengodman/CodeX/bin/codex-tree-steward --strict
/Users/stephengodman/CodeX/bin/codex-mcp preflight
```

Phone / away mode:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --status
/Users/stephengodman/CodeX/bin/codex-phone-mode --apply
/Users/stephengodman/CodeX/bin/codex-phone-mode --restore-sleep
```

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
