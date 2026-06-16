# CodeX Eval Bench

Practical local evals for leveling up CodeX.

This is not benchmark theater. It checks real operating behaviors Stephen cares about:

- identity separation
- memory recall
- CodeX-native routing
- dashboard generation
- Coding Anchor self-drift across startup, handoff, memory, and eval surfaces

## Commands

```bash
/Users/stephengodman/CodeX/bin/codex-eval list
/Users/stephengodman/CodeX/bin/codex-eval run room
/Users/stephengodman/CodeX/bin/codex-eval run identity
/Users/stephengodman/CodeX/bin/codex-eval run self-drift
/Users/stephengodman/CodeX/bin/codex-eval run all
/Users/stephengodman/CodeX/bin/codex-eval history
```

Groups:

- `room` checks CodeX-owned room behavior: identity, memory, failure memory, capability registry, dashboard, router, and self-drift.
- `all` currently runs the same CodeX-owned room cases.

## Results

SQLite DB:

`/Users/stephengodman/CodeX/evals/codex-evals.sqlite3`

JSON summaries:

`/Users/stephengodman/CodeX/evals/results/`

## Rule

A failed eval is useful. Patch the underlying behavior, not the scoreboard.
