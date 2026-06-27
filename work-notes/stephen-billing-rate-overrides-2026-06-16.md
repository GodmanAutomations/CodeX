# Stephen Billing Rate Overrides - 2026-06-16

## Outcome

Added Stephen-confirmed billing rates as a local CodeX override file:

`/Users/stephengodman/CodeX/config/stephen-billing-rates.json`

Confirmed rates:

- Regular liner install: `$1,150`
- Inlay / liner-over-step install: `$1,500`
- Non A/B measure: `$150`
- A/B measure: `$250`
- Snap-in: `$100`

The bill preview still reads the Pi5 runtime pricing block first, then applies these local Stephen billing overrides for Stephen's Memphis Pool bill.

## Billing Logic Changes

- Inlay-step cards are now priced as `liner_install_inlet` at `$1,500`, not held for review.
- Regular liner installs now use `$1,150`.
- Snap-ins are priced at `$100`, including warranty snap-in wording when Stephen says they were completed and should be added.
- Extra bill cards can be added by search query or exact card ID with `--extra-card-query`.
- `draft_stephen_bill` MCP now accepts `extra_card_queries`.

## Current Corrected Draft

Generated current corrected draft with Santiago and Cave snap-ins added:

- PDF: `/Users/stephengodman/CodeX/work-artifacts/billing-drafts/Artesian Bill - 2026-06-16 - DRAFT - 11430.pdf`
- CSV: `/Users/stephengodman/CodeX/work-artifacts/billing-drafts/Artesian Bill - 2026-06-16 - DRAFT - 11430.csv`
- Markdown: `/Users/stephengodman/CodeX/work-artifacts/billing-drafts/Artesian Bill - 2026-06-16 - DRAFT - 11430.md`

Current totals:

- Included lines: 15
- Review lines not included: 1
- Total due: `$11,430.00`

## Verification

Verified with:

- Python compile check on `trello-preview-bill`, `trello-draft-bill`, and the Trello MCP server.
- Live preview run with `--extra-card-query Santiago --extra-card-query 6a2f3f45d1e13218cfc62623`.
- Live draft bill generation.
- Direct MCP call through `draft_stephen_bill(extra_card_queries=[...])`.
- PDF rendered to PNG and visually inspected.
- Publish-plan dry-run now points to `Artesian Bill - 2026-06-16 - DRAFT - 11430`.

No Trello writes were made.
