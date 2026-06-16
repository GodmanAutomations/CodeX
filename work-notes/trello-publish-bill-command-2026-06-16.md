# Trello Publish Bill Command - 2026-06-16

## Outcome

Added a publish-plan layer for Stephen's Trello billing flow.

- Local command: `/Users/stephengodman/CodeX/bin/trello-publish-bill`
- Global shortcut: `/Users/stephengodman/bin/trello-publish-bill`
- MCP tool: `publish_stephen_bill`

Default behavior is plan-only. It finds the latest draft bill JSON, confirms the matching PDF/CSV/Markdown/JSON files exist, finds the Memphis board `BILLS` list, and writes a local publish plan under:

`/Users/stephengodman/CodeX/work-artifacts/billing-drafts/`

## Apply Gate

Trello writes require:

`--apply-token PUBLISH_STEPHEN_BILL`

Optional write behaviors:

- `--comment-job-cards` comments on included job cards after the bill is published.
- `--move-to-list LIST_NAME` moves included job cards after the bill is published.

Without the apply token:

- Trello writes: none
- Google Drive writes: none
- Pi5 writes: none
- Secrets printed: none

## Verification

Verified with:

- Python compile check on `trello-publish-bill` and the Trello MCP server.
- Dry-run command through `/Users/stephengodman/bin/trello-publish-bill --json`.
- Direct MCP wrapper dry-run through `publish_stephen_bill`.
- MCP inventory now classifies `publish_stephen_bill` as write-capable.

Latest dry-run result:

- Mode: `plan`
- Bill card name: `Artesian Bill - 2026-06-16 - DRAFT - 7180`
- BILLS list ID: `6a2f3f45d1e13218cfc620c0`
- Included cards: 10
- Review cards: 4
- Total: `$7,180.00`
- Trello writes: false
