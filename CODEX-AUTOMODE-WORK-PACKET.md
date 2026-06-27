# CodeX Auto-Mode Work Packet

This is the room-level live packet for longer CodeX runs.

Auto mode is not a vibe. It is a visible operating loop: one goal, one plan,
one next action, clear blockers, and receipts that make resume possible.

## Current Packet

Current goal:

- Implement Personal Voice Profile v1 as a first-class startup layer.

Mode:

- Done.

Started:

- 2026-06-27 01:52 CDT

Last update:

- 2026-06-27 01:57 CDT

Active plan:

- Add `CODEX-PERSONAL-VOICE-PROFILE.md`.
- Add `CODEX-PERSONAL-MODES.md`.
- Add `TICKET-CODEX-PERSONAL-VOICE-V1.md`.
- Wire the personal layer into sticky startup, owned boot, identity regression,
  thread profile, startup, room handoff, and front-door docs.
- Run regression/search, startup, Coding Anchor doctor, bridge preflight, diff,
  and secret checks.
- Commit and push through PR flow if verification passes.

Last completed step:

- Wired Personal Voice Profile v1 into startup, routing, regression, room
  brief/handoff, front-door docs, and the thread profile; verification passed.

Next action:

- Use `CODEX-PERSONAL-VOICE-PROFILE.md` and `CODEX-PERSONAL-MODES.md` whenever
  Stephen is testing tone, trust, closeness, disappointment, or "what's next."

Blockers:

- None.

Files/services touched:

- `/Users/stephengodman/CodeX/CODEX-AUTOMODE-WORK-PACKET.md`
- `/Users/stephengodman/CodeX/CODEX-PERSONAL-VOICE-PROFILE.md`
- `/Users/stephengodman/CodeX/CODEX-PERSONAL-MODES.md`
- `/Users/stephengodman/CodeX/TICKET-CODEX-PERSONAL-VOICE-V1.md`
- `/Users/stephengodman/CodeX/TICKET-CODEX-OWNED-STARTUP-INTEGRATION.md`
- `/Users/stephengodman/CodeX/AGENTS.md`
- `/Users/stephengodman/CodeX/CODEX-STICKY-STARTUP.md`
- `/Users/stephengodman/CodeX/CODEX-OWNED-BOOT.md`
- `/Users/stephengodman/CodeX/CODEX-IDENTITY-REGRESSION.md`
- `/Users/stephengodman/CodeX/CODEX-THREAD-PROFILE.md`
- `/Users/stephengodman/CodeX/CODEX-BEST-LANE.md`
- `/Users/stephengodman/CodeX/CODEX-CODING-ANCHOR-SELF.md`
- `/Users/stephengodman/CodeX/CODEX-STARTUP-DROPIN.md`
- `/Users/stephengodman/CodeX/ROUTING-CARD.md`
- `/Users/stephengodman/CodeX/START-HERE.md`
- `/Users/stephengodman/CodeX/README.md`
- `/Users/stephengodman/CodeX/CURRENT.md`
- `/Users/stephengodman/CodeX/HANDOFF.md`
- `/Users/stephengodman/CodeX/bin/codex-startup`
- `/Users/stephengodman/CodeX/bin/codex-room`

Verification needed:

- `rg -n "PERSONAL-VOICE|PERSONAL-MODES|personal voice|I can't tell|What's next" /Users/stephengodman/CodeX`
- `/Users/stephengodman/CodeX/bin/codex-startup`
- `/Users/stephengodman/CodeX/bin/codex-room brief`
- `/Users/stephengodman/CodeX/bin/codex-room handoff`
- `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-doctor`
- `/Users/stephengodman/bin/codex-thread --preflight`
- `git diff --check`
- secret scan

Receipts:

- `rg -n "PERSONAL-VOICE|PERSONAL-MODES|personal voice|I can't tell|What's next" /Users/stephengodman/CodeX` found the new layer across startup, routing, regression, and front-door surfaces.
- `bash -n /Users/stephengodman/CodeX/bin/codex-startup /Users/stephengodman/CodeX/bin/codex-room` passed.
- `/Users/stephengodman/CodeX/bin/codex-startup` surfaced `CODEX-PERSONAL-VOICE-PROFILE.md`, `CODEX-PERSONAL-MODES.md`, and the boot-complete Personal Voice line.
- `/Users/stephengodman/CodeX/bin/codex-room brief` and `handoff` surfaced the Personal Voice Profile and Personal Modes sections.
- `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-doctor` passed.
- `/Users/stephengodman/bin/codex-thread --preflight` passed with auto mode ON and active work showing this goal.
- `git diff --check` passed.
- Changed-file secret scan found only guardrail words and a placeholder example, no raw secret values.

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
