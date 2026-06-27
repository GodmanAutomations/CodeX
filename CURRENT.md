# Current

Updated: 2026-06-27

## Room State

- Room: `/Users/stephengodman/CodeX`
- Active task surface: CodeX self-drift audit adapted from the superskills catalog
- Startup boundary: stay in this folder unless Stephen explicitly points elsewhere
- Boundary repaired on 2026-06-16: `/Users/stephengodman/CodeX` is a real directory again, not a symlink to `/Users/stephengodman/Candice-Code`.
- Rook/Gemini is separate and should stay separate.
- Browser default for CodeX: `/Users/stephengodman/CodeX/bin/codex-browser`
- Default CodeX posture: Coding Anchor all the time, via `CODEX-CODING-ANCHOR-SELF.md`.
- Best Lane: `CODEX-BEST-LANE.md` layers phone-aware autonomy, concise closeout, and review-before-close onto Coding Anchor.
- Thread Profile: `CODEX-THREAD-PROFILE.md` is the compact carry-forward card
  for making new CodeX threads land in the same Codex-owned, Coding
  Anchor-backed, warm, auto-mode lane without stale transport or split-persona
  drift.
- Kira/Athena conductor port: `bin/codex-autoloop` and `bin/codex-task` create ignored reports/handholds under `receipts/`.
- Deeper Coding Anchor packet: `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor`.
- Fresh Coding Anchor launch: `/Users/stephengodman/CodeX/Coding Anchor Files/launch-codex-coding-anchor`.

## Latest Verified Boot Signals

- 2026-06-16 room-boundary repair: active CodeX docs, wrappers, MCP launchers, tests, and room modules were repointed from stale `/Users/stephengodman/Candice-Code` paths to `/Users/stephengodman/CodeX`.
- The old CodeX symlink was preserved as `/Users/stephengodman/CodeX.symlink-to-Candice-Code.20260616-054127`; `/Users/stephengodman/Candice-Code` now only contains empty receipt folders.
- The ignored Coding Anchor packet under `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor` was also repaired on disk; its doctor passes and it is intentionally not part of the tracked Git commit because `Coding Anchor Files/` is ignored.
- Fresh 2026-06-16 verification passed: `bin/codex-startup`, `bin/codex-ensure-standalone --check`, `bin/codex-doctor-room`, `bin/codex-self-drift`, `bin/codex-eval run room`, `git diff --check`, Python compile checks, and the nested cyberagent doctor from `/Users/stephengodman/CodeX/Codex's Secret Sauce`.
- Coding Anchor was promoted from optional packet to default CodeX posture on 2026-06-14.
- New all-time posture card exists: `/Users/stephengodman/CodeX/CODEX-CODING-ANCHOR-SELF.md`.
- `bin/codex-startup` now loads `CODEX-CODING-ANCHOR-SELF.md` during normal startup and prints "Coding Anchor always on."
- `bin/codex-ensure-standalone --check` now requires `CODEX-CODING-ANCHOR-SELF.md`, `/Users/stephengodman/.codex/AGENTS.md`, `/Users/stephengodman/CodeX/drift/codex_self_drift.py`, and `/Users/stephengodman/CodeX/bin/codex-self-drift`; latest final-audit receipt `/Users/stephengodman/CodeX/receipts/startup/20260614T092134Z-standalone-preflight.txt` (`pass=75 fix=0 warn=0 fail=0`).
- `bin/codex-doctor-room` passed after the superskills self-drift slice; latest final-audit receipt `/Users/stephengodman/CodeX/receipts/startup/20260614T092134Z-room-doctor.txt`.
- `bin/codex-eval run identity` now includes `coding-anchor-all-time-self` and passes.
- `bin/codex-eval run room` passes after the self-drift eval was added to the room group.
- `list_of_superskills.py` was treated as a source catalog, not executable Python; the adapted patterns were `detecting-container-drift-at-runtime` and `hunting-for-startup-folder-persistence`.
- New self-drift wrapper: `/Users/stephengodman/CodeX/bin/codex-self-drift`.
- New self-drift engine: `/Users/stephengodman/CodeX/drift/codex_self_drift.py`.
- Self-drift checks verify Coding Anchor propagation across global/local startup docs, room wrappers, evals, SQLite startup recall, and the side packet doctor.
- Adaptation note: `/Users/stephengodman/CodeX/drift/SUPERSKILL-ADAPTATION.md`.
- Second-pass audit found and fixed valuable propagation misses:
  - `/Users/stephengodman/CodeX/AGENTS.md` now includes `CODEX-CODING-ANCHOR-SELF.md` in the fresh-start order.
  - `/Users/stephengodman/CodeX/bin/codex-room brief` and `handoff` now print the Coding Anchor self card and identity lock.
  - SQLite startup memory `startup-pack` now includes `CODEX-CODING-ANCHOR-SELF.md`.
  - SQLite startup memory `coding-anchor-all-time-self` records the default posture.
  - `/Users/stephengodman/CodeX/README.md` and `/Users/stephengodman/CodeX/HANDOFF.md` now include the self card.
  - `/Users/stephengodman/.codex/AGENTS.md` now states Coding Anchor as the global default self.
  - `bin/codex-ensure-standalone --check` now requires `/Users/stephengodman/.codex/AGENTS.md`.
  - `bin/codex-eval run identity` now also checks `global-coding-anchor-default`.
- `bin/codex-startup` completed from `/Users/stephengodman/CodeX` on 2026-06-14 after dependency-stash archive move.
- Heartbeat is fresh through `bin/codex-heartbeat`.
- Continuity check is readable through `bin/codex-continuity`.
- SQLite memory is healthy at `/Users/stephengodman/CodeX/memory/codex-memory.sqlite3` with 14 memory items and 0 open loops.
- Capability registry is healthy at `/Users/stephengodman/CodeX/capabilities/capabilities.sqlite3` with 7 CodeX/source-grounding capabilities.
- `CODEX-WORKING-CARD.md` exists and `bin/codex-eval run identity` passes.
- `bin/codex-eval run room` is the room-local health signal; `run all` currently runs the same CodeX-owned cases.
- `bin/codex-room brief` is available for a compact read-only re-entry snapshot.
- `CREED.md`, `ROOM-SURFACE-MAP.md`, `WRENCH-GHOST-MODE.md`, and `BENCH-LIGHT-ON-GUARDRAILS.md` were restored after deeper cross-surface audit found startup/docs referenced them but preflight did not check them.
- Latest standalone preflight receipt: `/Users/stephengodman/CodeX/receipts/startup/20260614T092134Z-standalone-preflight.txt` (`pass=75 fix=0 warn=0 fail=0`).
- Latest room doctor receipt: `/Users/stephengodman/CodeX/receipts/startup/20260614T092134Z-room-doctor.txt`.
- Exact stale bulk artifact removed from `.playwright-mcp`: `v1-5-pruned-emaonly-fp16.safetensors`.
- `dependency-stash` was moved out of the active room to `/Users/stephengodman/CodeX-archives/dependency-stash-2026-06-14`; pointer: `DEPENDENCY-STASH-ARCHIVE.md`.
- Stale Rook collaboration surfaces were moved out of the active room to `/Users/stephengodman/CodeX-archives/stale-rook-surfaces-2026-06-14`.
- Pool reference images now live at `/Users/stephengodman/CodeX/measurement-pipeline-v2/reference-images/2026-06-04-pool-reference-images`; original root filenames are preserved as compatibility symlinks, active measurement-pipeline pointers were updated, historical file-open manifests were left as historical records, and the exact root `.DS_Store` cache file was removed.
- New CodeX-native skill installed: `/Users/stephengodman/.codex/skills/codex-adaptive-latency`; it implements "Fast start. Adaptive middle. Heavy end." from `/Users/stephengodman/CodeX/research/CodeX's Adaptive-Latency-Architecture.md` without using the confusing `stephen-*` lane prefix.
- CodeX room skills were renamed from `stephen-*` to `codex-*` because this is CodeX's room; `CODEX-SKILLS.md`, `ROUTING-CARD.md`, `AGENTS.md`, and `bin/codex-ensure-standalone` now point at the CodeX-owned names.
- Post-archive full room open/hash passed: 3,864 files opened, 0 errors, manifest `/Users/stephengodman/CodeX/work-notes/codex-room-full-file-open-manifest-2026-06-14-post-dependency-archive.jsonl`.
- Twilio phone lookup slice added repeatable report builder at `/Users/stephengodman/CodeX/output/phone-lookup/build_unknown_callers.py`; latest report `/Users/stephengodman/CodeX/output/phone-lookup/unknown-callers-20260613-225959.md`.
- Twilio live screening slice is deployed: `/Users/stephengodman/CodeX/output/twilio-functions/functions/handle-call.js` routes marketing/VoIP/invalid callers to screened voicemail when `SCREEN_SUSPECTS=1`; hard blocking remains off with `BLOCK_SUSPECTS=0`.
- Twilio deploy helper: `/Users/stephengodman/CodeX/output/twilio-functions/deploy.py`; latest deploy receipt `/Users/stephengodman/CodeX/receipts/startup/twilio-screen-suspects-20260614-001626.json`.
- Twilio live health verified after deploy: `screen_suspects=true`, `block_suspects=false`, `sms_auto_reply=false`, forwarding enabled.
- Twilio Auth Token rotation slice ran on 2026-06-14 through a nonce-guarded temporary Function; the old exposed primary token was rotated, post-rotation Lookup verification passed, and the active cleanup deployment no longer includes the maintenance route.
- Twilio rotation helper: `/Users/stephengodman/CodeX/output/twilio-functions/rotate_auth_token.py`; receipt `/Users/stephengodman/CodeX/receipts/startup/twilio-auth-token-rotation-20260614-verified.json`.
- Claude independently reviewed the Twilio slices and passed them read-only on 2026-06-14; pass note `/Users/stephengodman/CodeX/work-notes/twilio-claude-review-pass-2026-06-14.md`.
- Post-review cleanup fixed the review guide's secret scan to use `grep -rIE` with a sanity assertion, and clarified that the verified rotation receipt is hand-curated/canonical while the helper's raw receipt schema may differ.
- Twilio caller-control dashboard slice is built: `/Users/stephengodman/CodeX/output/phone-lookup/build_caller_control.py`; latest dashboard `/Users/stephengodman/CodeX/output/phone-lookup/caller-control-latest.html`.
- Latest caller-control counts: 33 unknown numbers, 23 screened now, 10 forwarded now, 0 hard-blocked now, 23 candidate-block-later review items.
- Twilio caller decision ledger slice is built: `/Users/stephengodman/CodeX/output/phone-lookup/caller-decisions.json` plus `/Users/stephengodman/CodeX/output/phone-lookup/caller_decisions.py`; dashboard now merges manual decisions without changing live Twilio policy.
- Recon MCP is live and globally configured as a read-only CodeX MCP server at `/Users/stephengodman/CodeX/mcp_servers/recon_mcp_launcher.sh`; its server, data helpers, and canonical paths are tracked in this repo so the live tool surface is reproducible.
- Recon uses `/Users/stephengodman/GodmanAutomations/data` as the canonical data root and `/Users/stephengodman/CodeX/config/stephen-billing-rates.json` as Stephen's local 2026 Artesian billing-rate authority.
- Recon exposes billing, report, job, bill-history, and photo-match lookup tools as read-only. Refresh remains dry-run preview only; stale `/Users/stephengodman/data` script paths are reportable warnings, not blockers.
- Cybersecurity skills MCP is globally configured as `cybersecurity-skills`, backed by `/Users/stephengodman/CodeX/Codex's Secret Sauce/run_mcp.py` through that repo's `.venv` Python; it exposes search, load, and domain-list tools for the 754-skill library.

## Watch Items

- Keep Coding Anchor and Best Lane as CodeX posture, not a revival of old Anchor/Gemini identity or global auto-load behavior.
- Phone/away work should check `bin/codex-phone-mode --summary` first and apply with notify only when the lane is not ready.
- Full-auto work should use `bin/codex-autoloop "<scope>" --task` when the next handhold is not already obvious.
- Venice key is not loaded in this session (`venice: key_loaded=False`); startup still passes because Venice is a sidecar lane, not core boot.
- Codex doctor reports a newer Codex version available (`0.139.0` vs current `0.136.0`); this is a workstation-level update, not a CodeX room file bug.
- Codex doctor reports active rollout files using about 3.20 GB outside this room; do not clean global rollouts from CodeX unless Stephen asks for global Codex housekeeping.
- Do not recreate `/Users/stephengodman/CodeX/dependency-stash` unless a task specifically needs the archived runtime mirror restored.
- Twilio has one inactive historical Function resource named `codex-auth-token-rotation-inactive-20260614`; Twilio refused deletion because a historical Build references its version, but the active deployment excludes it and the route returns `404`.
- The new Twilio Auth Token was not written to room files or receipts. Continue using API-key-backed CLI for API work; use the Console if the raw primary Auth Token is needed later.

## Active Rule

Coding Anchor always on, Best Lane available: find true state, pick the smallest useful move, act with initiative, use phone-aware readiness when Stephen is away, use `bin/codex-autoloop` for bounded multi-slice handholds, smoke test it when possible, and report pass, fail, or blocker plainly.
