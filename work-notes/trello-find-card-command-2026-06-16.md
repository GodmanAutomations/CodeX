# Trello Find Card Command - 2026-06-16

## Result

Added a clearly named read-only card lookup command:

- `/Users/stephengodman/Candice-Code/bin/trello-find-card`

Added launcher support in:

- `/Users/stephengodman/Candice-Code/mcp_servers/trello_mcp_server.py`

New launcher mode:

```bash
/Users/stephengodman/Candice-Code/mcp_servers/trello_mcp_launcher.sh --search-cards --query Byrd --limit-cards 5
```

## Why

This gives a plain operator command for resolving card names before using:

- `/Users/stephengodman/Candice-Code/bin/trello-read-work-order`
- `/Users/stephengodman/Candice-Code/bin/trello-attach-card-photo`

## Supported Uses

Find cards:

```bash
/Users/stephengodman/Candice-Code/bin/trello-find-card Byrd
```

Find on another configured board:

```bash
/Users/stephengodman/Candice-Code/bin/trello-find-card --board artesian Byrd
```

Raw JSON:

```bash
/Users/stephengodman/Candice-Code/bin/trello-find-card --json Byrd
```

## Verification

Local/file verification passed:

- `chmod 755 /Users/stephengodman/Candice-Code/bin/trello-find-card`
- `/Users/stephengodman/000_AI/bin/python3 -m py_compile /Users/stephengodman/Candice-Code/bin/trello-find-card /Users/stephengodman/Candice-Code/mcp_servers/trello_mcp_server.py`
- `bash -n /Users/stephengodman/Candice-Code/mcp_servers/trello_mcp_launcher.sh`
- Missing-query usage check returns the expected argparse error.
- No hanging `trello-find-card`, `trello_mcp_launcher`, or `op run` processes remained after checks.

Live Trello verification is blocked right now:

- `op run --env-file /Users/stephengodman/.env.1password ...` timed out with status `124`.
- 1Password MCP authenticate failed with an IPC error after opening the 1Password desktop app.
- The app-side Trello MCP transport was also closed during this check.

## Safety

- Command is read-only.
- No Trello writes.
- No Google Drive writes.
- No Pi writes.
- Secrets were not printed.

## Next Fix Needed

The command code is installed, but live use needs the 1Password CLI/env path healthy again. Once 1Password is unlocked and `op run --env-file /Users/stephengodman/.env.1password ...` resolves, verify:

```bash
/Users/stephengodman/Candice-Code/bin/trello-find-card Byrd
```
