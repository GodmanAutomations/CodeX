# CodeX SQLite Memory

Local durable memory for Codex's executor lane.

This is the practical facts database. It is not the startup pulse and not the MCP continuity vault.

Database:
`/Users/stephengodman/Candice-Code/memory/codex-memory.sqlite3`

Helper:
`/Users/stephengodman/Candice-Code/memory/codex_memory.py`

## Purpose

Store small, durable, practical facts that help Codex execute better for Stephen.

Use this for:

- standing preferences
- lane boundaries
- tool routes
- durable setup facts
- open loops
- short handoff summaries

Do not use this for:

- secrets
- raw transcripts
- private emotional material
- huge logs
- random lore
- stale project claims without verification

## Boundary

- Startup pulse: `continuity/`
- MCP vault, tomorrow notes, and closeout: `codex_continuity/`
- Private journal: `private/JOURNAL.md`
- Practical searchable facts: this folder

## Commands

```bash
/Users/stephengodman/Candice-Code/memory/codex_memory.py status
/Users/stephengodman/Candice-Code/memory/codex_memory.py list --kind preference
/Users/stephengodman/Candice-Code/memory/codex_memory.py search smoke
/Users/stephengodman/Candice-Code/memory/codex_memory.py add --kind preference --key example --value "Example value" --tags codex,executor
```

## Rule

Memory is support, not authority. Current files and live checks beat stored memory.
