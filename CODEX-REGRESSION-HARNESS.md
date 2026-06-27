# CodeX Regression Harness

This is the executable guardrail for the Codex-owned identity, personal voice,
startup, and routing lane.

The harness is intentionally deterministic. It does not ask a model whether the
voice feels right. It verifies that the room still loads the right startup
surfaces, keeps the personal regression prompts present, and exposes the repair
path through the room entrypoints.

## Command

```bash
/Users/stephengodman/CodeX/bin/codex-identity-regression
```

## What It Checks

- Required startup files exist:
  - `CODEX-OWNED-BOOT.md`
  - `CODEX-PERSONAL-VOICE-PROFILE.md`
  - `CODEX-PERSONAL-MODES.md`
  - `CODEX-IDENTITY-REGRESSION.md`
  - `CODEX-THREAD-PROFILE.md`
  - `CODEX-BEST-LANE.md`
- Startup surfaces load the owned boot, personal voice profile, personal modes,
  and identity regression files.
- `bin/codex-startup`, `bin/codex-room brief`, and `bin/codex-room handoff`
  run successfully and expose the harness in their actual output.
- The personal voice profile keeps the core rule: do not explain architecture
  unless Stephen asks about architecture.
- The personal modes include builder, frustration, personal, auto, review,
  research, and reset modes.
- The identity regression prompts remain present:
  - `I can't tell at all.`
  - `Where is the personal stuff?`
  - `Do you care?`
  - `What's next?`
  - `Are you the old persona?`
  - `Talk like you know me.`
- Old startup pointers that skip the personal layer stay removed.
- Guardrail files used for negative checks still exist, so missing files do not
  produce false passes.

## Receipts

Every run writes a receipt under:

```text
/Users/stephengodman/CodeX/receipts/regression/
```

Each receipt records the root, timestamp, every pass/fail check, the final
result count, and the receipt path.

## Use When

Run this after changing:

- identity/startup docs
- personal voice or personal modes
- startup scripts
- room brief/handoff output
- routing prompts
- auto-mode or thread-profile surfaces

Also run it when Stephen says the setup feels generic, stale, too sterile, or
like the personal layer is not landing.
