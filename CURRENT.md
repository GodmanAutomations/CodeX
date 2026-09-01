# Current

Updated: 2026-09-01

## Purpose

This is a compact re-entry handhold, not a session log or receipt index. The
newest authenticated directive and live room checks outrank this file.

## Room State

- Room boundary: `/Users/stephengodman/CodeX`.
- CodeX runs in the Codex desktop app unless Stephen explicitly requests a CLI
  session.
- Default posture: Coding Anchor, with Best Lane and the personal voice/modes
  startup layer defined by the room's startup documents.
- CodeX remains separate from Rook, Dawn, Marlow, Ace, and other rooms or
  identities.
- Do not infer a continuing task from old receipts. Recover the active objective
  from the current thread, handoff, or controller claim.

## Live Truth

Run the smallest check that answers the current question instead of trusting a
copied timestamp or an old `latest` receipt:

- Startup and room readiness: `bin/codex-startup`
- Compact room re-entry: `bin/codex-room brief`
- Repository state: `git status --short --branch`
- Repo/cloud/plugin/app triage: `bin/codex-elite-status`
- Standalone prerequisites: `bin/codex-ensure-standalone --check`
- Full room health when needed: `bin/codex-doctor-room`

Startup and doctor receipts belong under `receipts/startup/`; regression
receipts belong under `receipts/regression/`. Their newest successful output is
evidence for that run, not permanent current state.

## Durable Pointers

- `AGENTS.md` owns room law, startup order, boundaries, and verification rules.
- `CODEX-STICKY-STARTUP.md` and `CODEX-OWNED-BOOT.md` own the current startup
  packet.
- `CODEX-CODING-ANCHOR-SELF.md` owns the default execution posture.
- `CODEX-BEST-LANE.md` owns the autonomous, phone-aware lane.
- `CODEX-THREAD-PROFILE.md`, `CODEX-PERSONAL-VOICE-PROFILE.md`, and
  `CODEX-PERSONAL-MODES.md` own cross-thread behavior and tone.
- `CONTINUITY.md` maps deeper continuity; use private continuity only when the
  active work actually requires it.
- `CODEX-SKILLS.md` and `ROUTING-CARD.md` map CodeX-owned skills and ordinary
  requests to execution lanes.
- `SYSTEM-TREE.md` owns path-map and refresh procedures.

## Current-State Maintenance

Update this file only when the room's active boundary, operating posture,
durable pointer set, or verification path materially changes. Do not append:

- per-run pass lists or exact receipt filenames;
- version availability, service health, loaded-key, or storage snapshots;
- completed project inventories or historical cleanup notes;
- counts that a live command can reproduce.

Those facts belong in their owning project, receipt, Git history, or live
status output. Replace stale current truth in place rather than accumulating a
chronology here.

## Active Rule

Find current truth, choose the smallest consequential move, act within the room
boundary, verify the real effect, carry coherent Git work through the governed
lifecycle, and report pass, fail, partial, or blocked plainly.
