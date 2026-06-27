# CodeX Auto-Mode Work Packet

This is the room-level live packet for longer CodeX runs.

Auto mode is not a vibe. It is a visible operating loop: one goal, one plan,
one next action, clear blockers, and receipts that make resume possible.

## Current Packet

Current goal:

- Idle. Auto-Mode Work Packets v2 is installed as the standard packet shape.

Active plan:

- Use this file at the start of longer work.
- Keep the plan short enough to execute and verify.
- Update after each meaningful completed step.
- Close or reset the packet before declaring the run done.

Last completed step:

- Auto-Mode v2 packet and runbook were added to CodeX as the durable standard.

Next action:

- For the next longer run, read `CODEX-AUTOMODE-RUNBOOK.md`, set a concrete
  current goal here, then execute the first useful slice.

Blockers:

- None.

Files/services touched:

- `/Users/stephengodman/CodeX/CODEX-AUTOMODE-WORK-PACKET.md`
- `/Users/stephengodman/CodeX/CODEX-AUTOMODE-RUNBOOK.md`
- `/Users/stephengodman/CodeX/TICKET-CODEX-AUTOMODE-V2.md`

Verification needed:

- For packet-only changes, run targeted `rg`, `git diff --check`, CodeX startup,
  and Codex thread preflight.
- For code, service, or backend changes, add the narrow runtime check that proves
  the changed surface works.

Receipts:

- Commit for Auto-Mode v2.
- `git status --short`
- `/Users/stephengodman/bin/codex-thread --preflight`
- `/Users/stephengodman/CodeX/bin/codex-startup`

Resume instruction:

- If Stephen says "keep rolling", "where were we", "you decide", "auto mode",
  or similar, read this packet first, then continue from `Next action` unless a
  blocker is listed.

## Packet Fields

Use these exact field names when updating this packet or mirroring it into a
backend:

```text
Current goal:
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
