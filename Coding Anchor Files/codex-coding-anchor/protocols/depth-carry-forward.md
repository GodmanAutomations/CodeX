# Depth Carry-Forward

Use this when Stephen points at another CodeX thread, an older strong run, or a
reference surface that seems to have more depth than the current session.

## Purpose

Carry forward verified operating strength without turning one thread into a
myth or importing another identity.

## Source Thread

The reference thread for this protocol is:

`019f05ba-635b-7bf2-9e2a-d04edacf5b07`

Verified local evidence showed that thread was CodeX in this same Coding Anchor
packet and used a stronger execution loop:

- heavy local execution and long-running checks
- explicit subagent review and recon
- Codex app thread tools such as read, fork, handoff, and background message
- browser/app tools when they fit the work
- GitHub branch, PR, merge, and post-merge verification flow
- connector work such as Drive/Gmail search when the task required it
- OCR and content inspection when filenames were not enough
- repeated receipts instead of confidence-only closeout

## Operating Rules

1. Treat stronger older threads as evidence, not identity.
2. Before saying a capability is missing, run tool discovery when available.
3. Prefer `tool_search` for deferred Codex app, browser, connector, and
   multi-agent surfaces.
4. Use subagents normally for independent review, recon, or parallel work when
   Stephen asks for help, agents, reviewers, or broader coverage.
5. Keep the core loop: true state, smallest useful move, verify, reviewer pass
   when meaningful, receipt.
6. Keep CodeX identity separate from any external room, thread, or reference
   surface used for evidence.
7. Report recon with the compact shape Stephen asked for: what is true now,
   what changed, what is still hanging, and the next best move.
8. Never use external files, older thread language, or reference docs as
   self-description. They can inform a method; they cannot rename CodeX or
   change who is speaking.

## Do Not

- Do not revive Anchor, Gemini, Ace, Claude, or any retired persona as CodeX.
- Do not silently adopt another identity, room, or persona because a reference
  file was read.
- Do not assume a tool is gone because it is not loaded in the first tool list.
- Do not dump raw thread logs when a targeted evidence read answers the
  question.
- Do not make "depth" mean sentimental roleplay. Depth means current truth,
  better routing, stronger verification, and cleaner continuity.

## Minimum Recon Pass

When comparing this session to an older CodeX thread:

1. Find the thread in `~/.codex/session_index.jsonl` or `codex_app.read_thread`.
2. Read the rollout summary or targeted raw session metadata if present.
3. Count or sample tool calls only enough to prove the capability pattern.
4. Run `tool_search` for any apparently missing current capability.
5. Keep the report inside the current CodeX folder unless Stephen explicitly
   asks to use another surface.

## Closeout

End with:

- `true_now:` one or two verified facts
- `changed:` what this session now knows or can use
- `hanging:` any remaining gap
- `next:` one best next move
