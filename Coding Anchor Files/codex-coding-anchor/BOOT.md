# Boot

Run:

```bash
"/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-boot" --brief
```

Full orientation:

```bash
"/Users/stephengodman/CodeX/Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-boot" --full
```

Fresh Codex session:

```bash
"/Users/stephengodman/CodeX/Coding Anchor Files/launch-codex-coding-anchor"
```

Boot sequence:

1. Confirm this is CodeX Coding Anchor, not old Anchor/Gemini.
2. Read identity, autonomy, mission control, open loops, and current state.
3. Run the doctor check with structural and behavioral validation.
4. Record a heartbeat.
5. Load the operating protocols.
6. Run `bin/coding-anchor-next` when no explicit next step is already active.
7. Use `bin/coding-anchor-start <task-id>` before executing a selected pending
   queue task.
8. Begin the requested coding task with a short plan and verification target.

The doctor should fail plainly if required packet files are missing, script
syntax is broken, mission state is malformed, the parent doorway drifts, or the
fresh-session launch dry-run cannot target this packet.

If the boot feels thin, read:

- `config/codex-runtime-notes.md`
- `config/model-and-output-discipline.md`
- `AUTONOMY-CONTRACT.md`
- `CAPABILITY-MAP.md`
- `dashboards/TRUTH-LOG.md`
- `protocols/agentic-decision-rule.md`
- `protocols/autonomous-work-loop.md`
- `protocols/concise-agentic-output.md`
- `protocols/mission-routing.md`
- `protocols/next-slice-loop.md`
- `protocols/post-work-code-review.md`
- `protocols/verification-loop.md`
