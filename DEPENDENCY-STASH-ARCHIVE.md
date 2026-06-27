# Dependency Stash Archive

The old in-room dependency/runtime mirror was moved out of the active CodeX room on 2026-06-14.

## Current Location

```text
/Users/stephengodman/CodeX-archives/dependency-stash-2026-06-14
```

## Former Location

```text
/Users/stephengodman/CodeX/dependency-stash
```

## Why It Moved

The stash was a 3.9 GB copied cache/runtime mirror with about 30,946 files. It included Playwright browser engines, Codex plugin cache pieces, NotebookLM skill environments, and copied browser/dependency runtime material.

It was not needed inside the active room for startup, Twilio, continuity, or ordinary CodeX work. Keeping it in-room made audits noisy and heavy.

## Restore

If a future task genuinely needs the archive back in the active room:

```bash
mv /Users/stephengodman/CodeX-archives/dependency-stash-2026-06-14 /Users/stephengodman/CodeX/dependency-stash
```

Then rerun:

```bash
/Users/stephengodman/CodeX/bin/codex-startup
/Users/stephengodman/CodeX/bin/codex-ensure-standalone
```

## Receipts

- `/Users/stephengodman/CodeX/work-notes/codex-room-dependency-stash-slice-2026-06-14.md`
- `/Users/stephengodman/CodeX/work-notes/codex-room-dependency-stash-archive-2026-06-14.md`
