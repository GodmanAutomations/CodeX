# CodeX Claude Reviewer

Claude Code is the preferred outside reviewer for meaningful CodeX code,
startup, harness, routing, and room-surface changes.

Codex remains the executor. Claude is the reviewer lane.

Current identity/routing correction:

- Claude is Claude Code, not Ace.
- There is no active Ace persona layer.
- Claude's CodeX-local settings/config surface lives under
  `/Users/stephengodman/CodeX/.claude/`.
- Use `CLAUDE-OPUS-4.8-CODING-BEAST-RESEARCH.md` as the current rebuild note
  for Claude Code's clean coding/review operator profile.
- Do not route reviewer work through old global persona names, missing output
  styles, or retired identity layers.

## Command

```bash
/Users/stephengodman/CodeX/bin/codex-claude-review
```

## Contract

- Codex prepares the exact diff and context.
- Claude Code reviews the diff with edit tools disabled.
- The default reviewer command uses Claude Code's logged-in subscription/OAuth
  path by clearing Anthropic API auth and provider-routing environment variables
  for the subprocess, including common Bedrock, Vertex, proxy selectors, and
  AWS credential variables that could make Claude route outside subscription
  auth.
- Claude returns findings first, severity ordered, with file/line references.
- Codex fixes concrete findings, verifies, then commits.
- If Claude Code is unavailable, the Codex operator should use the built-in
  reviewer/subagent path and record that fallback.

## Use When

Run this after meaningful changes to:

- shell scripts
- startup or identity surfaces
- personal voice/profile/mode files
- regression harnesses
- routing or handoff docs
- repo automation

For tiny typo-only changes, a normal self-review is acceptable, but Claude Code
is still preferred when the change affects copy/paste commands or boot paths.

## Safety

The wrapper sends tracked diffs and safe untracked text files. It skips untracked
files that look like env files, credentials, secrets, tokens, passwords, private
keys, SSH key filenames, certificates, JSON/YAML config exports, or files over
the configured size cap.

For non-git workpapers or advisory packets, use `CODEX-CLAUDE-TEAMING.md` and
`/Users/stephengodman/CodeX/bin/codex-claude-team` instead of forcing the work
through a diff reviewer.

Claude Code CLI flags used here:

- `--tools ""` disables tools for the review subprocess.
- `--no-session-persistence` keeps the review one-shot.
- `--model sonnet` uses Claude Code's installed model alias.
- `--effort low` keeps routine review responsive; raise it only for deep review.

Environment overrides:

- `CODEX_CLAUDE_REVIEW_MODEL`
- `CODEX_CLAUDE_REVIEW_EFFORT`
- `CODEX_CLAUDE_REVIEW_MAX_BUDGET_USD`
- `CODEX_CLAUDE_REVIEW_MAX_UNTRACKED_BYTES`
- `CODEX_CLAUDE_REVIEW_MAX_UNTRACKED_LINES`

## API Auth Override

Only use API auth when explicitly needed:

```bash
CODEX_CLAUDE_REVIEW_USE_API_AUTH=1 /Users/stephengodman/CodeX/bin/codex-claude-review
```
