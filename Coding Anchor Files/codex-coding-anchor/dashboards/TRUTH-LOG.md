# Truth Log

Use this file for verified claims about the CodeX Coding Anchor packet.

## 2026-06-28

- Verified: `bin/coding-anchor-toolkit-check` provides a read-only optional
  operator toolkit inventory inspired by
  `trimstray/the-book-of-secret-knowledge`, emits both text and JSON, treats
  missing optional tools as non-fatal, and is covered by
  `bin/coding-anchor-doctor`; passing receipt:
  `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/receipts/20260628-002229-39029-doctor.txt`.
- Decision: keep the Book of Secret Knowledge material as an external operator
  reference and curated diagnostics shortlist, not as startup context, a broad
  install list, or default public scanning automation.
- Verified: the optional operator toolkit Homebrew install completed on this
  Mac, `bin/coding-anchor-toolkit-check` reports `installed=22 missing=0`, and
  the `certifi` Homebrew link conflict was repaired with
  `brew link --overwrite certifi`.
- Verified: the active Google Cloud SDK is the user SDK at
  `/Users/stephengodman/google-cloud-sdk/bin/gcloud`, updated to `574.0.0`
  with alpha/beta/bq/core/gsutil present; the duplicate Homebrew `gcloud-cli`
  cask was removed after its stale dependency receipt was repaired, and
  `git-credential-gcloud` was restored as a symlink to the user SDK helper.
- Verified: `bin/coding-anchor-opdiag` provides a read-only single-target
  diagnostic for a URL or host, emits text and JSON, self-tests without network
  access, avoids sudo and port sweeps by default, and is covered by
  `bin/coding-anchor-doctor`; passing receipt:
  `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/receipts/20260628-014600-43778-doctor.txt`.

## 2026-06-26

- Verified: the next-slice queue now supports select, start, done, and bounded
  preview commands, with strict reviewer-required closeout and local
  `jsonschema` validation through `bin/coding-anchor-doctor`; passing receipts
  include:
  `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/receipts/20260626-164250-91588-doctor.txt`.
- Verified: `bin/coding-anchor-start` has a read-only dry-run path and doctor
  smokes it against a temp queue fixture rather than mutating live queue state.
- Decision: do not install Task Master or a broad autonomous-agent framework
  over this packet by default; keep the native queue primary and add adapters
  only for real project needs.
- Verified: `protocols/post-work-code-review.md` makes independent read-only
  reviewer subagent review the default after meaningful file changes, with a
  labeled local review fallback only when subagents are unavailable.
- Verified: `bin/coding-anchor-doctor` now checks the cross-file post-work
  review hooks rather than only checking file presence.
- Verified: the first reviewer pass found gaps in doctor behavioral coverage,
  script verification safety, and fallback wording; those gaps were fixed and
  `bin/coding-anchor-doctor` passed with receipt
  `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/receipts/20260626-161425-83207-doctor.txt`.
- Verified: `AUTONOMY-CONTRACT.md` now defaults to action inside the active
  lane, expands local authority for reversible edits, docs, protocols,
  verification, subagents, GitHub/web/docs lookup, and authorized credential
  store use when task-relevant, while keeping explicit hard stop gates.
- Verified: `protocols/autonomous-work-loop.md` now includes fan-out,
  one reasonable retry after failure, and continuation through safe next slices.
- Verified: `bin/coding-anchor-doctor` passed after the autonomy tightening;
  receipt
  `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/receipts/20260626-160640-38625-doctor.txt`.
- Verified: `bin/coding-anchor-boot --brief` and `--full` are supported boot
  modes.
- Verified: `bin/coding-anchor-doctor` checks parent front-door paths, parent
  wrapper targets, shell syntax, JSON validity, mission-state shape, launch
  dry-run target, and stale Anchor/Gemini identity phrases.
- Verified: doctor receipts include the process id to avoid same-second
  collisions from concurrent boot checks.
- Verified: `bin/coding-anchor-launch --dry-run` targets
  `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor` and
  fails if Codex or the CodeX preflight script is missing.
- Verified: parent wrappers
  `/Users/stephengodman/CodeX/Coding Anchor Files/boot-codex-coding-anchor` and
  `/Users/stephengodman/CodeX/Coding Anchor Files/launch-codex-coding-anchor`
  fail plainly when their packet targets are missing.

## 2026-06-14

- Verified: the parent folder already contained an Anchor/Gemini quarantine
  archive before this packet was created.
- Verified: the live CodeX packet is
  `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor`.
- Verified: the packet has a parent-folder boot shortcut at
  `/Users/stephengodman/CodeX/Coding Anchor Files/boot-codex-coding-anchor`.
- Verified: the first version booted successfully after doctor tuning.
- Verified: the deeper room-brain version boots successfully with autonomy,
  mission control, open loops, heartbeat, doctor, and protocols loaded.
- Verified: the fresh-session launcher dry-run targets
  `/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor` as cwd
  and finds `/opt/homebrew/bin/codex`.
- Verified: Stephen asked for Coding Anchor to become CodeX's all-time self,
  and the main CodeX room now loads `CODEX-CODING-ANCHOR-SELF.md` during
  normal startup.
- Verified: main CodeX preflight now requires
  `/Users/stephengodman/CodeX/CODEX-CODING-ANCHOR-SELF.md`.
- Verified: main CodeX identity eval now includes
  `coding-anchor-all-time-self`.
- Verified: second-pass propagation audit fixed the missed startup surfaces:
  repo-local `AGENTS.md`, `README.md`, `HANDOFF.md`, `bin/codex-room`,
  SQLite startup memory, global `/Users/stephengodman/.codex/AGENTS.md`, and
  identity eval/preflight coverage.
- Verified: the superskills catalog in `/Users/stephengodman/CodeX/list_of_superskills.py`
  was mined for CodeX-native value, not imported wholesale.
- Adapted: `detecting-container-drift-at-runtime` and
  `hunting-for-startup-folder-persistence` became the CodeX self-drift audit.
- Verified: `/Users/stephengodman/CodeX/bin/codex-self-drift` passes and is now
  part of `bin/codex-eval run room`.
- Verified: main CodeX preflight now requires the self-drift engine and wrapper,
  and the latest room doctor passed with `pass=75 fix=0 warn=0 fail=0`.
- Source-supported: the old Anchor shape combined identity, current state, open
  loops, truth logging, tool context, and execution rules.
- Decision: rebuild the useful shape as CodeX-native room mechanics, not as a
  restore of old Anchor/Gemini state.
