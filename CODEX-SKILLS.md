# CodeX Skills

These are CodeX-native skills for this room.

They live in:

`/Users/stephengodman/.codex/skills/`

## Skills

- `codex-system-tree` - real local path map, `systree`, `refresh-systree`, NotebookLM system tree.
- `codex-claude-router` - route Claude-only or Claude-strong lanes without pretending they are native CodeX tools.
- `codex-pool-ops` - Artesian Pools, Memphis Pool, liner jobs, field ops routing.
- `codex-money-records` - taxes, invoices, Plaid, Square, Stripe, books, ACA-sensitive money work.
- `codex-comms` - messages, email, drafts, notifications, channel handoff routing.
- `codex-mac-devices` - Mac, AppleScript, Finder, iPhone/iPad, Apple device automation routing.
- `codex-infra-ops` - Pi5, Tailscale, Cloudflare, tunnels, Docker, deploy checks.
- `codex-media-room` - NVIDIA Shield, Plex, Trakt, Debrid, ADB, media workflows.
- `codex-notebooklm-rag` - NotebookLM, system tree notebook, local RAG, notebook-mesh, Firecrawl routing.
- `codex-notebook-mesh` - packet-first routing for vinyl-liner/pool pipeline work, including `/Users/stephengodman/vinyl-liner-measurement-pipeline`.
- `codex-local-rag` - Stephen's local Chroma/LM Studio knowledge base via `rag`.
- `codex-production-hygiene` - production discipline, rollback, verification, artifact rules.
- `codex-build-resources` - check existing skills/resources/scripts before building new tools.
- `codex-adaptive-latency` - CodeX operating workflow for fast startup, adaptive context loading, and heavier closeout work.

## Rule

Use these as CodeX language for durable room lanes and user work.

Do not clone Claude's identity. Use `codex-claude-router` when the right move is
a clean Claude Code handoff. There is no active Ace persona layer.

## Validate

```bash
for d in codex-system-tree codex-claude-router codex-pool-ops codex-money-records codex-comms codex-mac-devices codex-infra-ops codex-media-room codex-notebooklm-rag codex-notebook-mesh codex-local-rag codex-production-hygiene codex-build-resources codex-adaptive-latency; do
  python3 /Users/stephengodman/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/stephengodman/.codex/skills/$d
done
```
