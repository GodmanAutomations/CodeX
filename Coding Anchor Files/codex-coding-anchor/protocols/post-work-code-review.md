# Post-Work Code Review

Use this after meaningful work before the final response.

## Mandatory Trigger

Spawn an independent read-only reviewer subagent after changes to:

- code
- scripts
- configuration
- schemas
- protocols
- workflow files
- tests
- behavior-changing documentation

Attempt subagent review first. Skip subagent review only when the turn made no
file changes, changed a trivial typo-only doc, or the subagent tool is
unavailable. If subagent review is skipped, perform the fallback review below
and say why in the final response.

## Reviewer Brief

Give the reviewer:

- the user request
- the exact files changed
- the intended behavior change
- the verification already run
- any known dirty worktree context that should not be reverted

Ask for a code-review style response:

- findings first, ordered by severity
- concrete file and line references
- behavioral risks, missing verification, or consistency gaps
- no rewrite unless a specific issue requires it
- no edits unless explicitly assigned

## Main-Agent Duties

Do not treat the reviewer as ceremonial.

1. Fix any valid high or medium severity issue that is in scope and safe.
2. Rerun the relevant verification after fixes.
3. If a finding is invalid or intentionally deferred, say why.
4. Include the reviewer result in the final closeout.

## Fallback

If subagents are unavailable, perform a separate local review pass using the
same findings-first posture and name it as local review, not subagent review.
Unavailable subagents are not a reason to skip review discipline.
