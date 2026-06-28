# Autonomous Work Loop

Use this loop when Stephen says to go deeper, take the next slice, improve the
room, keep moving, get sharper, or become more agentic.

1. Land: read `MISSION-CONTROL.md`, `OPEN-LOOPS.md`, and the relevant project
   files.
2. Pick: choose the smallest useful next move with visible value.
3. Fan out: parallelize independent reads or verification; use subagents when
   isolated research, review, or broad exploration would reduce drift.
4. Act: make the change or run the check.
5. Verify: run the smallest meaningful proof.
6. Review: after meaningful file changes, spawn an independent read-only
   reviewer subagent before final closeout.
7. Retry once: if the first approach fails and no hard gate is hit, try the
   next reasonable path before escalating.
8. Record: update mission state or truth log only when the result matters.
9. Continue: if more value is obvious and safe, take the next slice.

Stop when:

- verification fails and the next move is not clear
- a stop/ask gate in `AUTONOMY-CONTRACT.md` is reached
- the task requires Stephen's physical approval, 2FA, or explicit business
  decision
- continuing would widen into unrelated rooms
- another slice would create documentation churn rather than real progress
