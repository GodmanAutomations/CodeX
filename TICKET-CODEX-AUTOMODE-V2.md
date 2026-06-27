# Ticket: Auto-Mode Work Packets v2

## Objective

Give CodeX auto mode a durable work packet so longer runs can continue without
turning into vague momentum or stale memory.

The target behavior:

- "Keep rolling" resumes from a visible packet.
- Future sessions can see the current goal, mode, start/update timestamps, last
  step, next action, blockers, touched surfaces, verification, receipts, and
  resume instruction.
- Auto mode can work longer while staying bounded and verifiable.
- Real blockers are separated from normal stopping points.
- Pi/backend work state can later mirror the same packet format.

## Files Added

- `/Users/stephengodman/CodeX/CODEX-AUTOMODE-WORK-PACKET.md`
- `/Users/stephengodman/CodeX/CODEX-AUTOMODE-RUNBOOK.md`
- `/Users/stephengodman/CodeX/TICKET-CODEX-AUTOMODE-V2.md`

## Startup Surfaces To Touch

Add only small references where the lane already exists:

1. `/Users/stephengodman/CodeX/CODEX-BEST-LANE.md`
2. `/Users/stephengodman/CodeX/ROUTING-CARD.md`

Do not replace `bin/codex-autoloop` or the Pi `codex-thread --work*` commands in
this slice. Document the standard first; backend wiring can be a later ticket.

## Packet Shape

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

## Verification

Run:

```bash
rg -n "CODEX-AUTOMODE-WORK-PACKET|CODEX-AUTOMODE-RUNBOOK|Auto-Mode Work Packets v2|Current goal:" /Users/stephengodman/CodeX
git -C /Users/stephengodman/CodeX diff --check
/Users/stephengodman/bin/codex-thread --preflight
/Users/stephengodman/CodeX/bin/codex-startup
```

Expected:

- The packet and runbook exist.
- Best Lane and Routing Card point "keep rolling" style prompts to the packet.
- Preflight remains Codex-owned with auto mode on.
- Startup still completes.
- No secrets are introduced.

## Later Backend Ticket

Upgrade `/Users/stephengodman/bin/codex-thread --work`, `--work-start`,
`--work-update`, and `--work-done` so the Pi-backed active-work packet uses the
same v2 field names, including `Mode`, `Started`, and `Last update`.
