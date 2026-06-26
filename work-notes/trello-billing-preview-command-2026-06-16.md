# Trello Billing Preview Command - 2026-06-16

## Outcome

Added a read-only billing preview command for Stephen's Memphis Pool Trello workflow:

- Local command: `/Users/stephengodman/CodeX/bin/trello-preview-bill`
- Global shortcut: `/Users/stephengodman/bin/trello-preview-bill`
- MCP tool: `preview_stephen_bill`

The command reads the Memphis board list named `Jobs that I need to bill for`, loads current pricing from the Pi5 runtime source at `/opt/artesian-pools/config.yaml`, and writes local draft billing reports under:

`/Users/stephengodman/CodeX/work-artifacts/billing-drafts/`

## Safety

- Trello writes: none
- Google Drive writes: none
- Pi5 writes: none
- Secrets printed: none

The command separates confident line totals from review-line totals so draft bills do not silently include questionable work.

## Verification

Verified with:

- Python compile check on the command and Trello MCP server.
- Live Trello read against the Memphis board billing list.
- Live Pi5 read-only pricing check against `/opt/artesian-pools/config.yaml`.
- MCP inventory confirmed `preview_stephen_bill` is exposed as read-only.

Latest preview result:

- Cards scanned: 14
- Confirmed priced total: `$7,180.00`
- Review-line possible total: `$2,450.00`
- Draft total including review lines: `$9,630.00`
- Needs review: 4
- Report: `/Users/stephengodman/CodeX/work-artifacts/billing-drafts/stephen-billing-preview-20260616-040914.md`

## Known Review Lines

- Barbara Walker inlay steps: verify whether this is add-on-only or a full liner install line.
- Shelia Miles rope anchors: current live pricing only has generic repair, no dedicated anchor rule.
- Jay & Cynthia Snider inlay steps and bench: verify whether this is add-on-only or a full liner install line.
- Dana Morrison warranty snap-in: confirm whether warranty work should be billed.
