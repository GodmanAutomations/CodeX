# Trello Phone Photo Sync Operator Guide - 2026-06-19

## What This Is

This is the CodeX/Trello MCP lane that matches Apple Photos pool-job pictures to Trello cards by GPS near the card address, stages the matching originals, uses Gemini vision to keep useful pool photos, uploads them to Trello, and sets a card cover.

The board-wide MCP tool is:

```text
sync_pool_photos_to_board
```

The friendly local wrapper is:

```text
/Users/stephengodman/CodeX/bin/trello-sync-pool-photos
```

## Normal Dry-Run

```text
/Users/stephengodman/CodeX/bin/trello-sync-pool-photos --board memphis --days-back 90 --radius-ft 250 --max-photos 1500 --max-total-photos 12 --max-photos-per-card 2 --limit-cards 100 --geocode-limit 80 --timeout-seconds 900
```

This does not write to Trello. It stages local photo candidates, classifies them, and reports:

- matched cards
- matched photos
- staged photos
- would upload
- already on card
- needs review
- rejected
- errors

## Live Apply

```text
/Users/stephengodman/CodeX/bin/trello-sync-pool-photos --apply --board memphis --days-back 90 --radius-ft 250 --max-photos 1500 --max-total-photos 12 --max-photos-per-card 2 --limit-cards 100 --geocode-limit 80 --timeout-seconds 900
```

Live writes still require the MCP apply token internally:

```text
APPLY_PHOTO_CARD_MATCH_PLAN
```

## Safety Defaults

- Dry-run is the default.
- Trello writes only happen with `--apply`.
- Existing Trello attachment names are checked before upload, so repeat runs do not duplicate already-uploaded phone photos.
- Existing `Pool photo ...` covers are preserved by default to prevent Gemini cover-choice drift from changing covers on repeat runs.
- Raw secrets are not printed.
- The launcher now falls back to the local Artesian automation `.env` for Trello and Gemini credentials when 1Password CLI is not signed in.

## 2026-06-19 Live Apply Receipt

The first board-wide live apply uploaded 9 photo attachments and set covers on 6 Memphis Pool cards.

Receipt:

```text
/Users/stephengodman/CodeX/work-artifacts/trello-mcp/photo-sync-runs/pool-photo-sync-20260619-182928.md
```

Post-apply verification confirmed all 9 expected attachment IDs are present on Trello and all 6 expected cover IDs are live.

The idempotency check against the generated plan returned:

```text
uploaded=0
would_upload=0
skipped_existing_name=9
needs_review=0
errors=0
```

