# CodeX Auto-Mode Work Packet

This is the room-level live packet for longer CodeX runs.

Auto mode is not a vibe. It is a visible operating loop: one goal, one plan,
one next action, clear blockers, and receipts that make resume possible.

## Current Packet

Current goal:

- Mirror Auto-Mode Work Packets v2 into the `codex-thread` backend bridge.

Mode:

- Done.

Started:

- 2026-06-27 02:16 CDT

Last update:

- 2026-06-27 01:19 CDT

Active plan:

- Verify the reported Auto-Mode v2 commit and tracked docs.
- Align the packet docs with the fuller v2 backend field shape.
- Upgrade `/Users/stephengodman/bin/codex-thread --work*` to write the v2 shape.
- Verify work start/update/done, preflight, startup, and git cleanliness.
- Commit tracked CodeX changes if verification passes.

Last completed step:

- Backend mirror now emits the v2 field shape and uses the live Codex backend
  paths under `/opt/codex-thread`.

Next action:

- Idle, or choose the next useful slice when Stephen says "keep rolling".

Blockers:

- None.

Files/services touched:

- `/Users/stephengodman/CodeX/CODEX-AUTOMODE-WORK-PACKET.md`
- `/Users/stephengodman/CodeX/CODEX-AUTOMODE-RUNBOOK.md`
- `/Users/stephengodman/CodeX/TICKET-CODEX-AUTOMODE-V2.md`
- `/Users/stephengodman/CodeX/CODEX-BEST-LANE.md`
- `/Users/stephengodman/bin/codex-thread`
- Pi service: `codex-thread.service`

Verification needed:

- `codex-thread --work-start`, `--work`, `--work-update`, and `--work-done`
- `/Users/stephengodman/bin/codex-thread --preflight`
- `/Users/stephengodman/CodeX/bin/codex-startup`
- `rg` for v2 field names
- `git diff --check`
- secret scan

Receipts:

- Commit for Auto-Mode v2.
- `bash -n /Users/stephengodman/bin/codex-thread`
- `/Users/stephengodman/bin/codex-thread --work-start "Mirror Auto-Mode Work Packets v2 into codex-thread backend"`
- `/Users/stephengodman/bin/codex-thread --work-update "Verified v2 field emission from backend work packet"`
- `/Users/stephengodman/bin/codex-thread --work-done "Backend mirror emits v2 fields and uses live Codex backend paths"`
- `/Users/stephengodman/bin/codex-thread --work`
- `/Users/stephengodman/bin/codex-thread --preflight`
- `/Users/stephengodman/CodeX/bin/codex-startup`
- `git diff --check`

Resume instruction:

- If Stephen says "keep rolling", "where were we", "you decide", "auto mode",
  or similar, read this packet first, then continue from `Next action` unless a
  blocker is listed.

## Packet Fields

Use these exact field names when updating this packet or mirroring it into a
backend:

```text
Current goal:
Mode:
Started:
Last update:
Active plan:
Last completed step:
Next action:
Blockers:
Files/services touched:
Verification needed:
Receipts:
Resume instruction:
```

## Rules

- Keep one active goal at a time.
- Keep blockers factual. Do not label ordinary stopping as a blocker.
- Put exact files, services, commands, receipts, and commit ids in the packet.
- Do not store secrets, private raw credentials, or long logs here.
- If work crosses a hard gate, write the gate under `Blockers` and stop.
- If the packet is stale, say so and rebuild it from git status, receipts,
  ticket files, and current runtime checks before continuing.
