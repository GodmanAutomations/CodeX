# Verification Loop

Use the smallest meaningful check available.

1. File change: inspect the changed file and run syntax or schema checks.
2. Script change: run shell syntax checks plus `--help`, `--dry-run`, or a
   narrow smoke path. Run the script itself only when that execution is known
   safe, reversible, and aligned with the active task.
3. App change: run tests, then open or smoke-test the relevant route.
4. Config change: run the tool's native validation command when available.
5. Documentation change: verify paths, commands, and dates are true.
6. Meaningful file change: spawn an independent read-only reviewer subagent
   using `protocols/post-work-code-review.md` before final closeout.

Close with:

- What changed.
- What passed.
- What the reviewer found, or why review was skipped.
- What remains unverified, if anything.
