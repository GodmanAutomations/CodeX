# Next-Slice Loop

Use this when Stephen gives a broad direction and expects CodeX to keep moving
without repeated "next slice" prompts.

## Purpose

The queue is a local handhold, not a background daemon. It lets CodeX select the
next safe unblocked slice, record proof, and continue until completion or a
real blocker.

## Commands

- `bin/coding-anchor-next`: show the current in-progress task or next unblocked
  pending task.
- `bin/coding-anchor-start <task-id>`: mark a safe unblocked pending task
  `in_progress`. Use `--dry-run` for a read-only smoke check.
- `bin/coding-anchor-done <task-id> --details "..."`
  marks an eligible in-progress task done with evidence. Add `--reviewed` when
  the task requires reviewer closeout.
- `bin/coding-anchor-loop --dry-run --max-slices N`
  previews the next slices that can be taken.

## Selection Rule

Prefer, in order:

1. an existing `in_progress` task, if it has no stop gates and is still safe
2. an unblocked `pending` task with all dependencies done
3. highest priority
4. earliest task order in `state/work-queue.json`

Skip tasks that are unsafe to auto-run, blocked by dependencies, or carrying
stop gates.

## Stop Rule

Stop when:

- no eligible task exists
- a task has `safe_to_auto: false`
- a task has stop gates
- verification fails
- reviewer blocks the change
- the next action would cross `AUTONOMY-CONTRACT.md`

## Closeout Rule

Every completed slice needs:

- concrete completion details
- verification evidence
- `--reviewed` plus reviewer result in the details when `reviewer_required` is
  true or meaningful files changed
- updated queue state
