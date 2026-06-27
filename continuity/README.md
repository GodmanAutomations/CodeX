# CodeX Startup Continuity

This folder is the small startup pulse.

It is not the MCP vault and not the practical memory database.

## Owns

- `one-true-sentence.txt` - one sparse carry-forward line.
- `one-true-sentence.timestamp` - timestamp for that line.
- `codex_continuity.py` - status check used by `bin/codex-continuity`.

## Does Not Own

- MCP tools or vault records. Those live in `codex_continuity/`.
- Practical durable facts. Those live in `memory/codex-memory.sqlite3`.
- Private journal entries. Those live in `private/JOURNAL.md`.

## Rule

Keep this folder tiny. If a note would become a record, open loop, tomorrow note, or searchable memory item, put it in the right lane instead of adding files here.
