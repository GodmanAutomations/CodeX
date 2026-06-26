# Trello Read Work Order Command - 2026-06-16

## Result

Added a thin field-friendly Trello command:

- `/Users/stephengodman/CodeX/bin/trello-read-work-order`

Naming note:

- This was first created as `pool-trello`, but that name was too vague.
- It was renamed to `trello-read-work-order` so the filename says what it does.

This wraps the verified Trello MCP launcher:

- `/Users/stephengodman/CodeX/mcp_servers/trello_mcp_launcher.sh`

## Why

The Trello MCP server exports the new work-order tools, but Codex `tool_search`
can lag on newly added tool metadata. This wrapper gives CodeX and Stephen a
stable local operator path for the field workflow while the MCP index catches up.

## Supported Uses

Status:

```bash
/Users/stephengodman/CodeX/bin/trello-read-work-order status
```

Short field command:

```bash
/Users/stephengodman/CodeX/bin/trello-read-work-order hauloff Corson
```

Natural phrase:

```bash
/Users/stephengodman/CodeX/bin/trello-read-work-order "can you read the workorder on Corson card and tell me if its a hauloff"
```

Raw JSON:

```bash
/Users/stephengodman/CodeX/bin/trello-read-work-order --json hauloff Corson
```

## Verification

- `chmod 755 /Users/stephengodman/CodeX/bin/trello-read-work-order`
- `/Users/stephengodman/000_AI/bin/python3 -m py_compile /Users/stephengodman/CodeX/bin/trello-read-work-order` passed.
- `/Users/stephengodman/CodeX/bin/trello-read-work-order status` returned `OK`.
- `/Users/stephengodman/CodeX/bin/trello-read-work-order hauloff Corson` returned:
  - `NO HAUL OFF`
  - source line: `24 X 44 - FREEFORM - INLAY STEPS - NO HAUL OFF`
- Natural phrase smoke returned the same result.
- Negative lookup smoke:
  - `/Users/stephengodman/CodeX/bin/trello-read-work-order hauloff DefinitelyNoSuchPoolCard`
  - returned a clean no-card-match error.

## Safety

- Read-only Trello smoke tests only.
- No Trello writes.
- No Google Drive writes.
- No Pi writes.
- Secrets were not printed.
