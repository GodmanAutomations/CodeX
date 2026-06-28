# Current

Date: 2026-06-26

This packet was created as a fresh CodeX-native rebuild inside:

`/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor`

The parent folder is an Anchor/Gemini quarantine and recovery archive. This
packet does not depend on those archived files as live instructions.

The packet has now been extended beyond a boot checklist into a small room
brain:

- `MISSION-CONTROL.md`
- `OPEN-LOOPS.md`
- `AUTONOMY-CONTRACT.md`
- `CAPABILITY-MAP.md`
- `dashboards/TRUTH-LOG.md`
- `state/current-mission.json`
- `state/work-queue.json`

## Current Safe Move

Use `bin/coding-anchor-boot --brief` for normal daily landing.

Use `bin/coding-anchor-boot --full` when Stephen wants full orientation printed
back out.

Use `bin/coding-anchor-launch` or the parent `launch-codex-coding-anchor` when
Stephen wants a fresh Codex session rooted directly in this packet.

Use `bin/coding-anchor-doctor` after edits to this packet. The doctor now
checks required files, required directories, executable bits, parent front-door
paths, parent wrapper targets, JSON validity, mission-state shape, shell syntax,
launch dry-run target, and stale Anchor/Gemini identity phrases.

Use `bin/coding-anchor-next` after boot or slice closeout when the next safe
action is not already explicit.

Use `bin/coding-anchor-start <task-id>` to turn a selected safe pending queue
task into the active in-progress slice before doing it.

Use `bin/coding-anchor-loop --dry-run --max-slices 3` to preview the next safe
unblocked slices without starting an uncontrolled background run.

Use `protocols/concise-agentic-output.md` and
`protocols/agentic-decision-rule.md` when Stephen asks for sharper, faster, or
more autonomous execution.

Use `bin/coding-anchor-agentic-check` to verify the concise autonomy anchors are
present before trusting the packet's agentic posture.

Use `bin/coding-anchor-toolkit-check` to inventory optional operator tools for
HTTP/API, TLS, DNS/network, logs/performance, and container/security
diagnostics. It is read-only and should not install packages by itself.

Use `bin/coding-anchor-opdiag <url-or-host>` for a compact single-target
read-only diagnostic. It runs DNS checks for hosts, adds HTTP and TLS checks
for URLs, emits text or `--json`, and leaves deeper tools such as `mtr`,
`sslscan`, `testssl`, and `ssh-audit` as manual follow-ups.

## Latest Hardening

On 2026-06-26, the boot path was hardened:

- `bin/coding-anchor-boot` supports `--brief`, `--full`, and `--help`.
- Boot fails with clearer errors when required files are missing.
- `bin/coding-anchor-doctor` validates behavior beyond file presence.
- Doctor receipts include the process id so concurrent boots do not overwrite
  receipts created in the same second.
- `bin/coding-anchor-launch --dry-run` fails if Codex or preflight is missing.
- Parent wrappers fail plainly if their packet targets are missing.

On 2026-06-26, the autonomy posture was tightened:

- `AUTONOMY-CONTRACT.md` now says the default is action, not
  permission-seeking, when the lane is clear.
- The packet may use parallel reads, background verification, subagents, web,
  GitHub, official docs, local skills, and narrow reference repos when they
  directly improve the active task.
- The work loop now includes fan-out, one reasonable retry after failure, and
  continuation through safe next slices.
- Hard gates remain explicit for destructive deletes, force pushes, spending,
  human contact, credential changes, official submissions, unrelated-room
  widening, and physical approval or 2FA.

On 2026-06-26, post-work review was added:

- `protocols/post-work-code-review.md` defines the reviewer trigger, reviewer
  brief, main-agent duties, and fallback.
- Meaningful file changes now require attempting an independent read-only
  reviewer subagent before final closeout, with a labeled local review fallback
  only if subagents are unavailable.
- `bin/coding-anchor-doctor` requires the review protocol so it cannot drift
  out of the packet unnoticed, and checks the cross-file review hooks.

On 2026-06-26, the next-slice queue was added:

- `state/work-queue.json` stores queued work with dependencies, priority,
  safe-to-auto flags, stop gates, verification, and reviewer requirements.
- `bin/coding-anchor-next` selects the current in-progress task or next safe
  unblocked pending task.
- `bin/coding-anchor-start` marks a safe unblocked pending task in progress.
- `bin/coding-anchor-done` marks a task done only with completion evidence.
- `bin/coding-anchor-loop` previews or guides bounded next-slice continuation;
  it is not a background daemon.
- `bin/coding-anchor-doctor` validates the queue files, executable commands,
  protocol hooks, and work queue shape.

On 2026-06-26, the concise agentic layer was added:

- `protocols/concise-agentic-output.md` trims work updates and final reports to
  action, result, verification, reviewer outcome, and next handhold.
- `protocols/agentic-decision-rule.md` turns safe ambiguity into action and
  keeps hard stop gates explicit.
- `bin/coding-anchor-agentic-check` verifies those anchors are present.

On 2026-06-28, an operator toolkit inventory was added:

- `notes/operator-toolkit-shortlist-2026-06-28.md` records the curated takeaways
  from `trimstray/the-book-of-secret-knowledge`.
- `bin/coding-anchor-toolkit-check` reports installed and missing optional
  diagnostics tools without mutating the workstation.

On 2026-06-28, a narrow operator diagnostic wrapper was added:

- `bin/coding-anchor-opdiag` accepts one URL or host, performs read-only DNS,
  HTTP, and TLS checks where applicable, and supports `--json`.
- The command intentionally avoids sudo, port sweeps, packet capture, and broad
  public recon expansion by default.

## Known Source Gift

The design was informed by:

`/Users/stephengodman/CodeX/private/phase1_coding_genius_plan.md`

That document's Gemini-specific settings and hook ideas were translated into
CodeX-native protocols and local receipts.
