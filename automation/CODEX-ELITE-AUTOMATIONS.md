# CodeX Elite Automations

These prompts are for Codex app automations. Use worktrees for Git repos unless
the automation is strictly read-only.

## Daily Repo Triage

Schedule: daily morning.

Prompt:

```text
Run /Users/stephengodman/CodeX/bin/codex-elite-status. Summarize only:
- dirty CodeX repo state
- open PRs needing action
- failed or pending checks
- Codex Cloud tasks with diffs ready to inspect
- plugin or app-server problems

Do not modify files. Do not print secrets. Archive the run if there is nothing actionable.
```

## PR Watch

Schedule: every 30 minutes while a CodeX PR is open.

Prompt:

```text
Check the current open CodeX PRs. If a PR has failed checks, inspect the logs and fix the smallest verified issue on the PR branch. If Codex review has requested changes, address only the concrete P0/P1 findings. Push the fix and report the PR URL. If nothing needs action, archive the run.
```

## Security Scan Cadence

Schedule: weekly, or before major merges.

Prompt:

```text
Use the Codex Security plugin to run a standard security scan on /Users/stephengodman/CodeX. Focus on committed code and scripts, not private receipts, generated artifacts, caches, or unrelated local outputs. Save the report path and list only validated findings with evidence.
```

## Cloud Review Follow-Up

Schedule: manual/thread automation after opening a PR.

Prompt:

```text
Poll the active CodeX PR. If @codex review posted findings, classify them as real behavior/security/maintainability issues or non-actionable notes. Fix real P0/P1 findings locally, verify, commit, push, and request another @codex review.
```
