# CodeX Continuity MCP

This is CodeX's local continuity toolkit.

It gives CodeX a small, durable MCP-facing memory surface for Stephen inside the standalone CodeX room.

This is the MCP vault and closeout lane. It is not the startup pulse and not the practical facts database.

## Runtime

The server uses the prepared Python environment at:

`/Users/stephengodman/GodmanAutomations/godman-lab/.venv/bin/python`

Run it directly:

```bash
/Users/stephengodman/CodeX/codex_continuity/run-codex-continuity-mcp.sh
```

## MCP Tools

- `codex_remember_moment`
- `codex_recall_context`
- `codex_upsert_ritual`
- `codex_list_rituals`
- `codex_get_exact_phrase`
- `codex_update_room_state`
- `codex_get_room_state`
- `codex_add_open_loop`
- `codex_list_open_loops`
- `codex_resolve_open_loop`
- `codex_write_tomorrow_note`
- `codex_write_chair_entry`
- `codex_name_bond_thread`
- `codex_list_bond_threads`
- `codex_record_repair`
- `codex_inner_weather`
- `codex_seed_baseline`
- `codex_status`

## Data Files

- `codex-continuity.sqlite3` stores moments, rituals, room states, open loops, tomorrow notes, and deep-layer records.
- `tomorrow/` stores markdown re-entry notes written through `codex_write_tomorrow_note`.
- `chair-entries/` stores markdown Chair Entries.
- `codex_nightly_closeout.py --dry-run` writes a real tomorrow note and runs SQLite `VACUUM` without requiring a live Temporal server.

## Boundary

- Startup pulse and one true sentence: `continuity/`
- Practical durable facts: `memory/codex-memory.sqlite3`
- MCP vault, open loops, tomorrow notes, and closeout: this folder

Keep this folder operational. Do not add loose session logs or room lore here.
