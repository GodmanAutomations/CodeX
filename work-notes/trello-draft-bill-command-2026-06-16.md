# Trello Draft Bill Command - 2026-06-16

## Outcome

Added a bill-draft generator that turns the Trello billing preview into actual bill artifacts.

- Local command: `/Users/stephengodman/CodeX/bin/trello-draft-bill`
- Global shortcut: `/Users/stephengodman/bin/trello-draft-bill`
- MCP tool: `draft_stephen_bill`

Default behavior:

- Reads the Memphis board list `Jobs that I need to bill for`.
- Runs the billing preview.
- Includes only confirmed `priced` lines in the payable total.
- Lists `needs_review` lines separately.
- Writes PDF, CSV, Markdown, and JSON files under:

`/Users/stephengodman/CodeX/work-artifacts/billing-drafts/`

## Current Draft

Generated current draft bill:

- PDF: `/Users/stephengodman/CodeX/work-artifacts/billing-drafts/Artesian Bill - 2026-06-16 - DRAFT - 7180.pdf`
- CSV: `/Users/stephengodman/CodeX/work-artifacts/billing-drafts/Artesian Bill - 2026-06-16 - DRAFT - 7180.csv`
- Markdown: `/Users/stephengodman/CodeX/work-artifacts/billing-drafts/Artesian Bill - 2026-06-16 - DRAFT - 7180.md`

Current totals:

- Included lines: 10
- Review lines not included: 4
- Total due: `$7,180.00`

## Safety

- Trello writes: none
- Google Drive writes: none
- Pi5 writes: none
- Secrets printed: none

Review lines can be included with `--include-review`, but the default leaves them out of the bill total.

## Verification

Verified with:

- Python compile check on `trello-draft-bill` and the Trello MCP server.
- Live command run through `/Users/stephengodman/bin/trello-draft-bill`.
- Live MCP wrapper call through `draft_stephen_bill`.
- MCP inventory confirmed `draft_stephen_bill` is exposed as read-only.
- Rendered the generated PDF with `pdftoppm` and visually inspected the first page.
