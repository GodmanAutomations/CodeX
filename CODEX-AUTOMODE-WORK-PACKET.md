# CodeX Auto-Mode Work Packet

This is the room-level live packet for longer CodeX runs.

Auto mode is not a vibe. It is a visible operating loop: one goal, one plan,
one next action, clear blockers, and receipts that make resume possible.

## Current Packet

Current goal:

- Build Tool Routing v1 so CodeX chooses the right truth source before acting.

Mode:

- Done.

Started:

- 2026-06-27 01:43 CDT

Last update:

- 2026-06-27 01:44 CDT

Active plan:

- Check existing routing resources before building.
- Add `CODEX-TOOL-ROUTING.md` as the route-before-tool card.
- Add `bin/codex-tool-route` for quick route matching.
- Wire Tool Routing into startup, room brief/handoff, profile, Best Lane,
  Routing Card, README, Start Here, and Current.
- Verify helper behavior, startup output, room handoff output, backend preflight,
  diff hygiene, and secret scan.
- Commit and push through PR flow if verification passes.

Last completed step:

- Tool Routing v1 is added, wired into startup/profile/handoff surfaces, and
  verified with helper, startup, room, backend preflight, diff, and scan checks.

Next action:

- Idle, or use `bin/codex-tool-route "<prompt>"` when a prompt needs route
  selection before tool use.

Blockers:

- None.

Files/services touched:

- `/Users/stephengodman/CodeX/CODEX-AUTOMODE-WORK-PACKET.md`
- `/Users/stephengodman/CodeX/CODEX-TOOL-ROUTING.md`
- `/Users/stephengodman/CodeX/bin/codex-tool-route`
- `/Users/stephengodman/CodeX/CODEX-THREAD-PROFILE.md`
- `/Users/stephengodman/CodeX/CODEX-BEST-LANE.md`
- `/Users/stephengodman/CodeX/ROUTING-CARD.md`
- `/Users/stephengodman/CodeX/START-HERE.md`
- `/Users/stephengodman/CodeX/README.md`
- `/Users/stephengodman/CodeX/CURRENT.md`
- `/Users/stephengodman/CodeX/bin/codex-startup`
- `/Users/stephengodman/CodeX/bin/codex-room`

Verification needed:

- `bash -n bin/codex-tool-route bin/codex-startup bin/codex-room`
- `bin/codex-tool-route` with representative prompts
- `/Users/stephengodman/CodeX/bin/codex-startup`
- `/Users/stephengodman/CodeX/bin/codex-room brief`
- `/Users/stephengodman/CodeX/bin/codex-room handoff`
- `/Users/stephengodman/bin/codex-thread --preflight`
- `rg` for Tool Routing references
- `git diff --check`
- secret scan

Receipts:

- `bash -n bin/codex-tool-route bin/codex-startup bin/codex-room`
- `bin/codex-tool-route "look up latest openai api docs"`
- `bin/codex-tool-route "use the pi to check service"`
- `bin/codex-tool-route "keep rolling on this"`
- `bin/codex-tool-route "remember this"`
- `bin/codex-tool-route "commit and push"`
- `bin/codex-startup`
- `bin/codex-room brief`
- `bin/codex-room handoff`
- `/Users/stephengodman/bin/codex-thread --preflight`
- `rg` for Tool Routing references
- `git diff --check`
- Secret scan found only guardrail words, no raw secrets.

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
