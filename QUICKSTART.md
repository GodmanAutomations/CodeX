# CodeX Quickstart

Use this as the clipboard version for cold starts in the CodeX room.

## Startup Prompt

```text
You are starting in /Users/stephengodman/CodeX.

Stay in this folder for startup and continuity.
Do not re-root into .codex, Rook, Anchor, or any other room unless I explicitly say to.

Startup steps:
1. Read CODEX-IDENTITY-LOCK.md
2. Read CODEX-CODING-ANCHOR-SELF.md
3. Read CODEX-BEST-LANE.md
4. Read START-HERE.md
5. Read BOOT.md
6. Read CURRENT.md
7. Run /Users/stephengodman/CodeX/bin/codex-startup
8. Report boot complete in one short paragraph, including:
   - confirmation you stayed in /Users/stephengodman/CodeX
   - confirmation Coding Anchor is the default CodeX posture
   - confirmation Best Lane is loaded for autonomous phone-aware work
   - heartbeat status
   - continuity status
   - the active task surface or that none is set yet

If the boot feels thin, then also read:
- CREED.md
- WRENCH-GHOST-MODE.md
- BENCH-LIGHT-ON-GUARDRAILS.md
- ROOM-SURFACE-MAP.md

After meaningful work, use /Users/stephengodman/CodeX/bin/codex-remember-self when there is something future-CodeX should keep.
Use /Users/stephengodman/CodeX/bin/codex-one-true-sentence only for a meaningful carry-forward line, not every session.
```

## One Command

```bash
/Users/stephengodman/CodeX/bin/codex-startup
```

Fast read-only room brief:

```bash
/Users/stephengodman/CodeX/bin/codex-room brief
```

## Standalone App Launch

Use this when starting from a shell and you want CodeX to check its pre-app prerequisites first, then open the Codex desktop app:

```bash
/Users/stephengodman/CodeX/bin/codex-launch
```

Health check without launching a new Codex session:

```bash
/Users/stephengodman/CodeX/bin/codex-ensure-standalone --repair
/Users/stephengodman/CodeX/bin/codex-doctor-room
```

## What This Does

- refreshes the heartbeat
- lands CodeX in the Coding Anchor default posture
- loads the Best Lane operating contract
- brings bench light on
- checks continuity
- reports capability status
- prints the current true-now surface

## Rule

Read the room only when CodeX continuity matters. Otherwise work from the active project.

If Stephen asks whether anything important is hidden or overlooked, read `ROOM-SURFACE-MAP.md` before widening.

## Executor Loop

1. Find true state.
2. Pick the smallest real move.
3. Do it.
4. Smoke test it.
5. Report pass, fail, or blocker.

## Useful Follow-On Commands

```bash
/Users/stephengodman/CodeX/bin/codex-room status
/Users/stephengodman/CodeX/bin/codex-room handoff
/Users/stephengodman/CodeX/bin/codex-room recall smoke
/Users/stephengodman/bin/systree find "CodeX"
/Users/stephengodman/CodeX/bin/codex-browser headlines https://news.ycombinator.com --json
/Users/stephengodman/CodeX/bin/codex-route "test venice model lane"
/Users/stephengodman/CodeX/bin/codex-venice smoke
```

## Browser

Use Camoufox as the hard default for CodeX browser work.

- Primary command: `/Users/stephengodman/CodeX/bin/codex-browser`
- Default engine: `camoufox`
- Runtime Python: `/Users/stephengodman/GodmanAutomations/godman-lab/.venv/bin/python`
- Installed there: `camoufox`, `browser_use`, `nodriver`
- Archived dependency mirror: `/Users/stephengodman/CodeX-archives/dependency-stash-2026-06-14/Users/stephengodman/...`
- Archived browser engines mirror: `/Users/stephengodman/CodeX-archives/dependency-stash-2026-06-14/Users/stephengodman/Library/Caches/ms-playwright`
- Archive pointer: `/Users/stephengodman/CodeX/DEPENDENCY-STASH-ARCHIVE.md`

Do not default to Chrome/profile/extension automation. Use Chrome only when Stephen explicitly asks for Chrome or the task requires a logged-in Chrome profile.

## Venice

Venice is a CodeX-side model lane, not a raw-secret note lane.

- Use `/Users/stephengodman/CodeX/bin/codex-venice models` to list models.
- Use `/Users/stephengodman/CodeX/bin/codex-venice smoke` for a safe API smoke.
- Keep `VENICE_API_KEY` or `VENICE_ADMIN_KEY` env-only. Do not write keys into notes, prompts, docs, or repo files.

## Memory

SQLite memory is at:

`/Users/stephengodman/CodeX/memory/codex-memory.sqlite3`

Helper:

`/Users/stephengodman/CodeX/memory/codex_memory.py`
