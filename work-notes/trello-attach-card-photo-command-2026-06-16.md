# Trello Attach Card Photo Command - 2026-06-16

## Result

Added a clearly named photo attachment command:

- `/Users/stephengodman/CodeX/bin/trello-attach-card-photo`

It wraps the verified Trello MCP launcher:

- `/Users/stephengodman/CodeX/mcp_servers/trello_mcp_launcher.sh`

## Why

This is the field-friendly counterpart to:

- `/Users/stephengodman/CodeX/bin/trello-read-work-order`

The name says exactly what it does: attach photo files to a Trello card.

## Supported Uses

Dry-run preview, no Trello write:

```bash
/Users/stephengodman/CodeX/bin/trello-attach-card-photo --card Byrd /path/to/photo.jpg
```

Dry-run with cover selection:

```bash
/Users/stephengodman/CodeX/bin/trello-attach-card-photo --card Byrd --cover first /path/to/photo.jpg
```

Real Trello attach:

```bash
/Users/stephengodman/CodeX/bin/trello-attach-card-photo --apply --card Byrd /path/to/photo.jpg
```

Real Trello attach and cover set:

```bash
/Users/stephengodman/CodeX/bin/trello-attach-card-photo --apply --card Byrd --cover first /path/to/photo1.jpg /path/to/photo2.jpg
```

Raw JSON:

```bash
/Users/stephengodman/CodeX/bin/trello-attach-card-photo --json --card Byrd /path/to/photo.jpg
```

## Behavior

- Dry-run is the default.
- Real Trello writes require `--apply`.
- Supports multiple photo paths.
- Supports cover selection with:
  - `none`
  - `first`
  - `last`
  - `second`
  - `third`
  - any 1-based number
- Does not write Trello comments.
- Uses the existing Trello MCP launcher for credentials and Trello writes.

## Verification

- `chmod 755 /Users/stephengodman/CodeX/bin/trello-attach-card-photo`
- `/Users/stephengodman/000_AI/bin/python3 -m py_compile /Users/stephengodman/CodeX/bin/trello-attach-card-photo` passed.
- Dry-run smoke with a local `.jpg` placeholder returned:
  - `DRY RUN: no Trello writes.`
  - card: `Byrd`
  - cover marker on photo 1
- Missing-photo smoke returned:
  - `at least one photo path is required`
- Existing wrong-extension smoke returned:
  - `not a supported photo extension`
- JSON dry-run returned:
  - `mode: dry_run`
  - `trello_writes: false`

## Safety

- No Trello writes were run.
- No Google Drive writes.
- No Pi writes.
- Secrets were not printed.
