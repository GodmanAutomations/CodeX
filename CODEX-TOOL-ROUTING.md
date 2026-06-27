# CodeX Tool Routing v1

Use this before choosing tools when Stephen says "check", "look into", "find",
"use the Pi", "remember this", "keep rolling", or "make it real".

The rule is simple: route by truth source first, then act.

## Routes

| Need | Route | First move | Verification |
| --- | --- | --- | --- |
| Current outside facts | Web/search | Browse or search current sources; prefer official/primary sources for technical, policy, account, or high-stakes facts. | Cite sources or state what remains unverified. |
| Local repo truth | Filesystem/shell | Stay in the current folder, read local rules, run `rg`/targeted commands. | Run tests, lint, startup, or the smallest runtime smoke available. |
| Pi/backend truth | `codex-thread` + SSH | Run `/Users/stephengodman/bin/codex-thread --preflight`, then SSH only as needed. | Check service state, health endpoint, logs, or targeted backend command. |
| CodeX continuity | Room memory | Use `bin/codex-room brief`, `bin/codex-room recall`, `CONTINUITY.md`, and the active packet. | Confirm against current files/runtime before treating memory as current truth. |
| API/library behavior | Official docs | Use local docs/examples first, then official docs for drift-prone APIs. | Link or name the exact doc/source and run a small code/runtime check when possible. |
| Long auto-mode work | v2 packet | Read/update `CODEX-AUTOMODE-WORK-PACKET.md`; mirror with `codex-thread --work*` when backend-visible. | Packet has current goal, next action, blockers, touched files, receipts, and verification. |
| Private/person-sensitive work | Bounded/safety lane | Keep private material out of logs/chat/git; use minimal necessary reads. | Confirm no raw secrets/private payloads were written to tracked files or receipts. |
| Creative/media work | Media/image/audio tools | Use the domain tool directly; save outputs in an appropriate local path. | Open/render/play the output or provide the exact file path and known limits. |
| Git/release work | Git/PR route | Inspect status, stage only intentional files, use conventional commits, PR when protected. | `git status`, commit hash, PR URL, and push/merge state. |

## Selection Rules

- If the user asks for "latest", "current", "today", prices, docs, policies,
  schedules, or account status, use current-source lookup.
- If the answer depends on this machine, this repo, or a service, inspect the
  real local or remote state before answering.
- If the task crosses more than one bounded step, create or update the v2 packet.
- If a tool fails, try one safe alternate route before escalating.
- If a route is unclear, choose the smallest safe first read and say which lane
  was chosen.

## Hard Gates

Stop before destructive deletes, force-pushes, spending money, external contact,
legal/tax/government/medical/financial submissions, biometric/live 2FA gates, or
unrelated-room widening without a clear task reason.

## Compact Form

Current facts: web. Local truth: files/shell. Pi truth: `codex-thread` + SSH.
Memory: recall then verify. API behavior: official docs. Long work: v2 packet.
Private work: bounded lane. Creative work: media tools. Git work: status,
commit, PR, verify.
