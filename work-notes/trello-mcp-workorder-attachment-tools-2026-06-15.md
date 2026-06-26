# Trello MCP Work-Order + Attachment Tools - 2026-06-15

## Result

Extended the always-on Trello MCP server:

- `attach_file_to_card`
- `set_card_cover`
- `read_card_work_order`

Server file:

- `/Users/stephengodman/CodeX/mcp_servers/trello_mcp_server.py`
- `/Users/stephengodman/CodeX/mcp_servers/trello_mcp_launcher.sh`

Backup made before edits:

- `/Users/stephengodman/CodeX/mcp_servers/trello_mcp_server.py.before-codex-workorder-tools-20260615-231701`

## Behavior

`attach_file_to_card`

- Attaches a local file to a card by `card_id` or exact/unique `card_query`.
- Does not infer Trello comments from Stephen's spoken prompt.
- Optional comments are explicit only.
- Returns the Trello attachment id.

`set_card_cover`

- Sets `idAttachmentCover` for an existing attachment id.

CLI fallback:

- `trello_mcp_launcher.sh --attach-file --file-path <path> --card-id <id>`
- `trello_mcp_launcher.sh --attach-file --file-path <path> --card-query <unique card name>`
- `trello_mcp_launcher.sh --set-cover --card-id <id> --attachment-id <attachment id>`

`read_card_work_order`

- Read-only Trello operation.
- Resolves a card by `card_id` or exact/unique `card_query`.
- Picks the best work-order-like attachment, preferring XLS/XLSX/CSV/PDF work-order, install, measure, liner, and drawing names over photos.
- Downloads the selected attachment to:
  - `/Users/stephengodman/CodeX/work-artifacts/trello-mcp/work-orders/`
- Extracts text from:
  - `.xls` via `strings -a` and `strings -el`
  - `.xlsx` via workbook XML/shared strings
  - `.pdf` via `pdftotext`, fallback `pypdf`
  - text-like files via normal text read
- Returns haul-off hints and important work-order lines.

## Verification

File-level verification:

- `/Users/stephengodman/000_AI/bin/python3 -m py_compile /Users/stephengodman/CodeX/mcp_servers/trello_mcp_server.py` passed.
- `bash -n /Users/stephengodman/CodeX/mcp_servers/trello_mcp_launcher.sh` passed.
- Direct FastMCP manager inspection returned 47 tools and confirmed:
  - `attach_file_to_card`
  - `set_card_cover`
  - `read_card_work_order`
- CLI fallback validation passed:
  - `trello_mcp_launcher.sh --attach-file` returns a clean `--file-path is required with --attach-file` error and performs no Trello write.

Launcher/runtime verification:

- `/Users/stephengodman/CodeX/mcp_servers/trello_mcp_launcher.sh --status` passed.
- Credentials loaded from the existing 1Password env path.
- Secret values were not printed.
- Local Trello board config exists and contains board ids only, not credentials.
- Raised the launcher's default `op run` timeout from 12 seconds to 35 seconds after a reload flapped on a one-time 1Password timeout.
- Verified normal status now reports `op_timeout_seconds: 35`.

Live read-only Trello verification:

- `/Users/stephengodman/CodeX/mcp_servers/trello_mcp_launcher.sh --doctor-live` passed.
- `/Users/stephengodman/CodeX/mcp_servers/trello_mcp_launcher.sh --read-work-order --card-query 'Corson' --question 'hauloff?' --max-text-chars 2000` passed.
- Selected card on the new Memphis board:
  - `Chris Corson - Collierville - Inlay Steps - Going Out of Town June 4-11`
- Selected attachment:
  - `Corson Chris 1111 Tuscumbia Road Install Liner with Inlay Steps.xls`
- Extracted haul-off result:
  - `NO HAUL OFF`

## Safety

- No Trello write smoke was run.
- No Google Drive writes.
- No Pi writes.
- `read_card_work_order` writes only a local downloaded artifact copy for parsing.

## Reload Note

Stopped stale Trello MCP server processes so the next MCP connection starts from the updated source. The local launcher and CLI smoke tests pass after reload. In the current Codex app thread, the old tool transport closed during restart; if direct MCP tool calls still show only partial Trello tools, refresh the Codex MCP connection or start a fresh thread.

Direct server inspection proves the MCP server exports all three new tools. If Codex `tool_search` does not find those exact names, that is deferred tool-search metadata lag, not a server/export failure. Use the launcher CLI fallback for the affected operation until the app refreshes its tool index.
