# CodeX Auto-Mode Runbook

Use this when Stephen says "keep rolling", "full auto", "you decide",
"where were we", "next slice", or when a task will span more than one bounded
step.

## Purpose

Auto mode should create durable forward motion without losing the thread.

The work packet answers:

- what CodeX is trying to finish
- what already happened
- what should happen next
- what is actually blocked
- what files, services, and receipts prove the work

## Start A Run

1. Read `CODEX-AUTOMODE-WORK-PACKET.md`.
2. If the packet has an active goal, decide whether the current request resumes
   it or starts a new goal.
3. Set `Current goal` to one concrete outcome.
4. Set `Active plan` to 3-7 short steps.
5. Set `Next action` to the first executable step.
6. Set `Verification needed` before editing.
7. If the Pi thread bridge is relevant, run:

```bash
/Users/stephengodman/bin/codex-thread --work-start "goal"
```

## During Work

Update the packet when any of these changes:

- a plan step completes
- the next action changes
- a file or service is touched
- verification passes or fails
- a real blocker appears

Use concise entries. The packet is a control surface, not a transcript.

When the Pi thread bridge is relevant, mirror the current step with:

```bash
/Users/stephengodman/bin/codex-thread --work-update "current step"
```

## Resume A Run

When resuming:

1. Read `CODEX-AUTOMODE-WORK-PACKET.md`.
2. Run `git status --short` in the active repo.
3. Read any ticket, plan, or receipt named in the packet.
4. Verify live service/runtime state if the packet names services.
5. Continue from `Next action`.

If the packet conflicts with current files or runtime state, trust current
state and update the packet before continuing.

## Close A Run

Before closeout:

1. Run the verification listed in `Verification needed`.
2. Put the pass/fail result under `Receipts`.
3. Set `Last completed step` to the final verified step.
4. Set `Next action` to the next real handhold, or `Idle` if done.
5. Clear `Blockers` if no blocker remains.
6. If a commit was made, record the short commit id.
7. If the Pi thread bridge is relevant, run:

```bash
/Users/stephengodman/bin/codex-thread --work-done "summary"
```

## Standard Packet

Copy this shape exactly:

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

## Hard Gates

Stop and write the blocker when the next move would:

- delete unclear user work
- rewrite git history
- push or publish without an explicit request
- spend money
- contact a person externally
- submit legal, tax, government, medical, or financial changes
- require Stephen's biometric, hardware key, live 2FA tap, or wet signature
- widen into an unrelated room without a clear task reason

## Relationship To Existing Tools

- `CODEX-BEST-LANE.md` defines the autonomy posture.
- `ROUTING-CARD.md` maps Stephen's ordinary wording into this lane.
- `bin/codex-autoloop` creates ignored planning handholds under `receipts/`.
- `codex-thread --work*` is the Pi-backed runtime mirror and should use this
  packet shape when upgraded.

The tracked packet is the room standard. Ignored receipts are evidence. Backend
state is a mirror, not a replacement for the room control surface.
