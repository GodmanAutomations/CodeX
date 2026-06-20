# Candice Mac Photo Sync Bridge - 2026-06-20

## Purpose

Candice runs on the Pi, but Stephen's Apple Photos library is on the Mac. This slice added a narrow Mac bridge so Candice can ask CodeX on the Mac to run the existing Apple Photos GPS-to-Trello sync.

## Current Status

Candice is intentionally not wired to this bridge right now.

Stephen paused the Candice integration on 2026-06-20. The Mac-side bridge remains installed for later use, but the live Pi bot was disconnected:

- `/opt/telegram/candice_v2/main.py` restored from the pre-bridge backup.
- `/opt/telegram/candice_v2/tool_dispatcher.py` restored from the pre-bridge backup.
- `/opt/telegram/.env` no longer contains the bridge URL or token keys.
- `pool_photo_sync` is not present in Candice's tool registry.
- The deterministic board-wide photo-sync parser methods are not present.
- `candice-v2.service` was restarted and verified active after rollback.

Do not rewire Candice/Kandice to this bridge unless Stephen explicitly asks for that again.

## Mac Bridge

Tracked files:

- `/Users/stephengodman/CodeX/bin/trello-photo-sync-bridge`
- `/Users/stephengodman/CodeX/bin/trello-photo-sync-bridge-install`
- `/Users/stephengodman/CodeX/launchd/com.godman.codex-photo-sync-bridge.plist`

Runtime:

- LaunchAgent label: `com.godman.codex-photo-sync-bridge`
- URL: `http://100.114.106.68:8768`
- Health endpoint: `/health`
- Start endpoint: `/v1/photo-sync`
- Status endpoint: `/v1/runs/<run_id>`
- Private token path: `/Users/stephengodman/CodeX/private/trello-photo-sync-bridge/token`

Safety:

- `/health` is read-only and returns no secret values.
- `/v1/photo-sync` and `/v1/runs/<run_id>` require `Authorization: Bearer <token>`.
- Bridge defaults to dry-run unless request body has `apply: true`.
- Bridge calls the verified wrapper `/Users/stephengodman/CodeX/bin/trello-sync-pool-photos`.

## Pi Candice Integration - Paused

Live host:

- `pi@100.100.32.58`
- Service: `candice-v2.service`
- Path: `/opt/telegram/candice_v2`

The following live Pi wiring was added, then rolled back after Stephen paused the integration:

- `/opt/telegram/candice_v2/tool_dispatcher.py`
  - Added `pool_photo_sync` tool.
  - Actions: `health`, `start`, `status`.
  - Uses `CODEX_PHOTO_SYNC_BRIDGE_URL` and `CODEX_PHOTO_SYNC_BRIDGE_TOKEN` from `/opt/telegram/.env`.
- `/opt/telegram/candice_v2/main.py`
  - Added deterministic text shortcut for pool-photo library sync.
  - Routes phrases like `sync my pool photos to trello` to live apply.
  - Routes phrases like `preview matching phone photos to pool cards` to dry-run.
  - Keeps work-order reads and single-photo Trello attachment phrases out of this board-wide sync route.
- `/opt/telegram/candice_v2/proactive.py`
  - Excludes transient SQLite WAL/SHM files from bot tar backups.
  - Treats live `file changed as we read it` tar exit as a warning when the archive exists.

The `proactive.py` backup-noise fix remains in place because it is unrelated to photo-sync wiring.

Pi backups were written before each live edit under:

- `/opt/telegram/candice_v2/backups/`
- `/opt/telegram/backups/.env.before-codex-photo-sync-bridge-<timestamp>`
- `/opt/telegram/backups/.env.before-codex-photo-sync-unwire-<timestamp>`

## Verification

- Mac LaunchAgent is running.
- Mac bridge `/health` returns `ok=true`.
- Pi can reach Mac bridge `/health` over Tailscale.
- Before rollback, Pi `pool_photo_sync` tool was registered and returned bridge health.
- Before rollback, authenticated Pi-to-Mac dry-run queue smoke succeeded with no Trello writes.
- Before rollback, Candice parser checks passed:
  - `sync my pool photos to trello` -> board-wide photo sync, live apply intent.
  - `preview matching phone photos to pool cards` -> board-wide photo sync, dry-run intent.
  - `put that pic on Byrd card` -> not board-wide photo sync.
  - `can you read the workorder on corson card` -> not board-wide photo sync.
- After rollback, Candice tool registry reports `has_pool_photo_sync_tool=False`.
- After rollback, Candice parser checks report `has_photo_sync_parser=False` and `has_photo_sync_status_parser=False`.
- After rollback, `/opt/telegram/.env` reports both `CODEX_PHOTO_SYNC_BRIDGE_URL=False` and `CODEX_PHOTO_SYNC_BRIDGE_TOKEN=False`.
- `candice-v2.service` restarted and is active with one live `python -m candice_v2.main` process.
- Current backup behavior writes archive successfully; live file-change tar condition is now warning, not failed backup.
