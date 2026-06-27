# CodeX Auto-Mode Work Packet

This is the room-level live packet for longer CodeX runs.

Auto mode is not a vibe. It is a visible operating loop: one goal, one plan,
one next action, clear blockers, and receipts that make resume possible.

## Current Packet

Current goal:

- Build Executable Regression Harness v1 for Codex identity and personal voice
  startup drift.

Mode:

- Done.

Started:

- 2026-06-27 02:03 CDT

Last update:

- 2026-06-27 02:04 CDT

Active plan:

- Use `codex-build-resources` before creating the workflow.
- Add `bin/codex-identity-regression`.
- Add `CODEX-REGRESSION-HARNESS.md`.
- Wire the harness into startup, room brief/handoff, Best Lane, README,
  START-HERE, Routing Card, and Current.
- Run the harness plus startup, room, doctor, bridge preflight, diff, and
  changed-file secret checks.
- Commit, push, and open/merge a PR if verification passes.

Last completed step:

- Executable Regression Harness v1 is added, wired into startup and room
  surfaces, and verified.

Next action:

- Use `/Users/stephengodman/CodeX/bin/codex-identity-regression` after changing
  identity, personal voice, startup, routing, thread profile, room brief, or
  auto-mode surfaces.

Blockers:

- None.

Files/services touched:

- `/Users/stephengodman/CodeX/CODEX-AUTOMODE-WORK-PACKET.md`
- `/Users/stephengodman/CodeX/bin/codex-identity-regression`
- `/Users/stephengodman/CodeX/CODEX-REGRESSION-HARNESS.md`
- `/Users/stephengodman/CodeX/CODEX-BEST-LANE.md`
- `/Users/stephengodman/CodeX/ROUTING-CARD.md`
- `/Users/stephengodman/CodeX/START-HERE.md`
- `/Users/stephengodman/CodeX/README.md`
- `/Users/stephengodman/CodeX/CURRENT.md`
- `/Users/stephengodman/CodeX/bin/codex-startup`
- `/Users/stephengodman/CodeX/bin/codex-room`

Verification needed:

- `/Users/stephengodman/CodeX/bin/codex-identity-regression`
- `bash -n /Users/stephengodman/CodeX/bin/codex-identity-regression /Users/stephengodman/CodeX/bin/codex-startup /Users/stephengodman/CodeX/bin/codex-room`
- `/Users/stephengodman/CodeX/bin/codex-startup`
- `/Users/stephengodman/CodeX/bin/codex-room brief`
- `/Users/stephengodman/CodeX/bin/codex-room handoff`
- `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-doctor`
- `/Users/stephengodman/bin/codex-thread --preflight`
- `git diff --check`
- secret scan

Receipts:

- `/Users/stephengodman/CodeX/bin/codex-identity-regression` passed
  `pass=76 fail=0`; receipt:
  `/Users/stephengodman/CodeX/receipts/regression/20260627-020830-identity-regression.txt`.
- `bash -n /Users/stephengodman/CodeX/bin/codex-identity-regression /Users/stephengodman/CodeX/bin/codex-startup /Users/stephengodman/CodeX/bin/codex-room` passed.
- `/Users/stephengodman/CodeX/bin/codex-startup` surfaced owned boot,
  identity regression, regression harness docs, and the
  `bin/codex-identity-regression` command.
- `/Users/stephengodman/CodeX/bin/codex-room brief` and
  `/Users/stephengodman/CodeX/bin/codex-room handoff` surfaced the Identity
  Regression Harness section and command.
- Independent reviewer flagged false-negative risks; fixed by adding runtime
  output checks for startup, room brief, and room handoff, plus missing-file
  failures for negative checks.
- `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-doctor` passed.
- `/Users/stephengodman/bin/codex-thread --preflight` passed with auto mode ON
  and active work showing this harness goal.
- `git diff --check` passed.
- Changed-file secret scan found only guardrail words and a placeholder example,
  no raw secret values.

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
