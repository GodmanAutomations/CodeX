# Mission Control

Last updated: 2026-06-26

## Active Mission

Reinvent the best parts of the old Anchor feel as a CodeX-native coding agent
packet:

- crisp identity
- current-state landing
- open-loop tracking
- verified truth log
- autonomous work loop
- true launch entrypoint
- no contaminated identity restore

## Current Status

- Base CodeX Coding Anchor packet exists.
- Room-brain surfaces now exist.
- Doctor and boot path pass with the room-brain layer loaded.
- Fresh-session launcher dry-run passes and targets this packet as cwd.
- Autonomy contract now defaults to action inside the active lane: make the
  reversible move, verify it, retry once when appropriate, and continue through
  safe next slices without permission theater.
- Post-work code review is now mandatory after meaningful file changes: attempt
  an independent read-only reviewer subagent before final closeout, and use a
  labeled local review fallback only if subagents are unavailable.
- Next-slice queue commands now exist so Coding Anchor can choose safe
  unblocked work without waiting for Stephen to say "next slice."
- Dogfooding exposed and filled the missing queue transition command:
  `bin/coding-anchor-start` now marks safe pending work in progress.
- Concise agentic output and decision rules now exist so Coding Anchor can act
  with less narration while preserving verification and stop gates.

## Next Moves

1. Use `bin/coding-anchor-next` after boot or slice closeout when the next
   safe action is not already explicit, then `bin/coding-anchor-start <task-id>`
   before executing a selected pending queue task.
2. Use `bin/coding-anchor-agentic-check` when tuning autonomy or communication
   discipline.
3. Use this packet on the next serious coding mission.
4. Create a mission note with `bin/coding-anchor-mission` when a project is
   booted here.
5. Adapt the useful pieces of `shinpr/codex-workflows` into local protocols
   only after inspection, not by blind install.
6. Use the truth log for verified claims.
7. Keep old Anchor archive material read-only unless Stephen explicitly asks.

## Definition Of Good

When booted, CodeX should know:

- who it is in this packet
- what it is allowed to do
- what is currently true
- what loops are open
- what the next useful action is
- how to verify before declaring success
- when to keep moving without asking
- when a hard gate actually requires Stephen
- when to use an independent reviewer before trusting the result
- how to select the next safe queued slice
- how to communicate concisely while still showing verification and blockers
