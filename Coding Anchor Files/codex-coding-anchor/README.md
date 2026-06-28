# CodeX Coding Anchor

This is a bootable, CodeX-native coding posture that lives inside Stephen's
`Coding Anchor Files` folder without reviving the old Anchor/Gemini setup.

Boot it with:

```bash
"/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-boot" --brief
```

Use the full orientation boot when you need the packet printed back out:

```bash
"/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-boot" --full
```

Start a fresh Codex session rooted here with:

```bash
"/Users/stephengodman/CodeX/Coding Anchor Files/launch-codex-coding-anchor"
```

Or from the parent folder:

```bash
./boot-codex-coding-anchor
./launch-codex-coding-anchor
```

## What It Is

- A clean CodeX room packet for deep coding work.
- A translation of the Phase 1 "coding genius" ideas into CodeX behavior.
- A local set of protocols, schemas, and checks that can be run on demand.
- A small room brain: mission control, open loops, truth log, capability map,
  and autonomy contract.

## What It Is Not

- It is not Anchor.
- It is not a Gemini settings restore.
- It is not a live hook installer.
- It does not modify global agent configuration.

## Main Files

- `START-HERE.md` - first read when entering this packet.
- `BOOT.md` - boot sequence.
- `CURRENT.md` - current state and next safe moves.
- `CODING-ANCHOR-IDENTITY.md` - identity and posture.
- `AUTONOMY-CONTRACT.md` - what CodeX can do without waiting.
- `MISSION-CONTROL.md` - current mission and next moves.
- `OPEN-LOOPS.md` - active, watch, and parked loops.
- `dashboards/TRUTH-LOG.md` - verified claims and decisions.
- `CAPABILITY-MAP.md` - native lanes and routing.
- `bin/coding-anchor-boot` - boot front door.
- `bin/coding-anchor-launch` - fresh Codex session launcher.
- `bin/coding-anchor-doctor` - health, structure, parent-doorway, launch, JSON,
  and shell-syntax check.
- `bin/coding-anchor-next` - select the active or next safe queue slice.
- `bin/coding-anchor-start` - mark a selected pending queue slice in progress.
- `bin/coding-anchor-done` - close an eligible queue slice with evidence.
- `bin/coding-anchor-loop` - preview bounded safe queue continuation.
- `bin/coding-anchor-agentic-check` - verify concise autonomy anchors.
- `bin/coding-anchor-toolkit-check` - read-only optional operator toolkit
  inventory inspired by The Book of Secret Knowledge.
- `bin/coding-anchor-opdiag` - compact read-only diagnostic for one URL or
  host, with text and JSON output.
- `bin/coding-anchor-tick` - heartbeat writer.
- `bin/coding-anchor-mission` - mission-note starter.
- `protocols/` - CodeX-native before/after work protocols.
- `schemas/` - JSON schemas for reusable receipts.

## Local Python Dependency

`bin/coding-anchor-doctor` prefers `.venv/bin/python` when present and uses
`jsonschema` to validate live state files against their schemas.

Install the local validation dependency with:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```
