# CodeX Claude Teaming

Codex is the system keeper and executor. Claude Code is the controlled outside
reviewer/advisor lane.

This is not an identity merge. Claude is Claude Code. There is no active Ace
persona layer. CodeX stays responsible for local truth, edits, verification,
receipts, and final integration.

## Operating Model

```text
Stephen gives direction.
Codex gathers local truth and does the work.
Claude Code reviews, challenges, researches, or advises under a scoped packet.
Codex verifies Claude's findings against local state.
Codex implements useful fixes and reports receipts.
```

## Use Claude When

- A meaningful CodeX diff needs outside review.
- A tax, invoice, Plaid, Square, Stripe, or forensic records slice needs a
  second-pass workflow critique.
- A routing/startup/protocol change could affect future sessions.
- A hard technical decision would benefit from a separate reviewer.
- Stephen explicitly asks for Claude, Claude Code, main reviewer, hard review,
  or the two-agent lane.

## Routes

### Diff Review

Use this for tracked CodeX changes:

```bash
/Users/stephengodman/CodeX/bin/codex-claude-review
```

Codex prepares the diff. Claude Code reviews with edit tools disabled. Codex
fixes concrete findings and verifies.

### Scoped Advisory Packet

Use this for non-git workpapers, tax folders, broad records work, or workflow
questions where a diff is not the right review surface:

```bash
/Users/stephengodman/CodeX/bin/codex-claude-team --template > /tmp/claude-packet.md
/Users/stephengodman/CodeX/bin/codex-claude-team --prompt /tmp/claude-packet.md
```

The packet must name exact paths, what CodeX verified, what Claude must not
touch, and the desired output.

## Claude Roles

- `reviewer`: findings first, severity ordered, no edits.
- `advisor`: workflow critique, source hierarchy, risks, next fixes.
- `researcher`: official docs and primary-source grounding.
- `config-doctor`: Claude/CodeX config sanity, dead references, hook risk.
- `tax-workpaper-reviewer`: duplicate-income risk, owner classification,
  processor evidence, support trail, CPA-readiness.

## Safety

- Do not paste secrets, raw credentials, full account numbers, recovery codes,
  private keys, or unnecessary personal detail into Claude packets.
- Prefer paths, row counts, hashes, manifests, summaries, and bounded excerpts.
- Claude confidence is not verification. Codex must verify locally before
  changing files or treating a finding as true.
- Do not let Claude revive old identity, old transport, or split-persona
  framing.
- If Claude is unavailable, use the current Codex reviewer subagent fallback
  and record that fallback.

## Pattern Exchange

When Claude finds a better method, Codex should turn it into one durable thing:

- a checklist
- a regression check
- a command/script improvement
- a workpaper control
- a routing rule
- a concise doc update

When Codex builds a useful method, hand Claude the exact contract, not a vague
summary.

## Closeout

Every Claude-assisted slice should close with:

```text
Claude route:
Claude finding:
Codex action:
Verification:
Residual risk:
Next handhold:
```
