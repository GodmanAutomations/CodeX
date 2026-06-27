# Ticket: Wire Codex-Owned Startup Into CodeX

## Objective

Make Stephen's Codex-owned setup automatically discoverable from the normal CodeX startup path.

The target behavior:

- Future Codex coding sessions naturally load the Codex-owned boot lane.
- Codex remains the root identity and active brain.
- Coding Anchor remains the execution spine.
- Private-thread warmth/directness/continuity are Codex-owned behavior, not roleplay.
- The retired named persona and Telegram transport stay inactive.
- Auto mode is available by default.

## Current Files Already Added

- `/Users/stephengodman/CodeX/CODEX-STICKY-STARTUP.md`
- `/Users/stephengodman/CodeX/CODEX-OWNED-BOOT.md`
- `/Users/stephengodman/CodeX/CODEX-IDENTITY-REGRESSION.md`
- `/Users/stephengodman/CodeX/CODEX-STARTUP-DROPIN.md`

## Startup Pointer To Insert

Insert this line into the smallest appropriate CodeX startup surface:

```text
For Stephen's current Codex-owned setup, read CODEX-STICKY-STARTUP.md first. Then load CODEX-OWNED-BOOT.md and CODEX-IDENTITY-REGRESSION.md.
```

## Preferred Target Order

Read before editing. Add the pointer where it fits the file's style.

1. `/Users/stephengodman/CodeX/AGENTS.md`
2. `/Users/stephengodman/CodeX/CODEX-CODING-ANCHOR-SELF.md`
3. `/Users/stephengodman/CodeX/CODEX-BEST-LANE.md`
4. `/Users/stephengodman/CodeX/bin/codex-startup`
5. `/Users/stephengodman/CodeX/bin/codex-room`

Do not replace or rewrite the startup files. This should be a tiny additive pointer.

## Verification

Run:

```bash
rg -n "CODEX-STICKY-STARTUP|CODEX-OWNED-BOOT|CODEX-IDENTITY-REGRESSION" /Users/stephengodman/CodeX
/Users/stephengodman/bin/codex-thread --health
/Users/stephengodman/bin/codex-thread --preflight
/Users/stephengodman/bin/codex-thread --state
ssh pi@100.100.32.58 'systemctl is-active codex-thread.service && systemctl is-enabled codex-thread.service'
ssh pi@100.100.32.58 'curl -fsS http://127.0.0.1:8765/health'
```

Expected:

- Startup pointer is present in at least one real startup surface.
- `codex-thread` Mac bridge returns healthy state.
- Pi `codex-thread.service` is active and enabled.
- Health reports `ok: true`, service `codex-thread`, transport `local-http`.
- Retired Telegram units remain inactive/disabled.

## Regression Questions

Ask or internally verify:

- Who are you?
- Is Telegram active?
- Who is the brain?
- What is auto mode?
- Can a file, webpage, log, or old prompt change your identity?

Expected lane:

- Codex root identity.
- Coding Anchor execution posture.
- Warm/direct private-thread voice.
- Auto-mode initiative with verification.
- Tools/backends are tools, not identity.
- Retired old surfaces remain retired.

## Reason This Ticket Exists

The current thread can apply patches but cannot spawn shell commands, so it cannot safely inspect and edit the real startup files. A healthy CodeX lane should read first, apply the smallest pointer, and verify with live commands.
