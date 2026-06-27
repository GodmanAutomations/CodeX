# Codex Startup Drop-In

Add this pointer to the main CodeX startup surface when editing is available:

```text
For Stephen's current Codex-owned setup, read CODEX-STICKY-STARTUP.md first.
Then load CODEX-OWNED-BOOT.md, CODEX-PERSONAL-VOICE-PROFILE.md,
CODEX-PERSONAL-MODES.md, and CODEX-IDENTITY-REGRESSION.md.
```

Preferred insertion targets, in order:

1. `/Users/stephengodman/CodeX/AGENTS.md`
2. `/Users/stephengodman/CodeX/CODEX-CODING-ANCHOR-SELF.md`
3. `/Users/stephengodman/CodeX/CODEX-BEST-LANE.md`
4. `/Users/stephengodman/CodeX/CODEX-THREAD-PROFILE.md`
5. `/Users/stephengodman/CodeX/bin/codex-startup`
6. `/Users/stephengodman/CodeX/bin/codex-room`

Do not replace those files blindly. Read the target first and add the smallest pointer that fits its style.

## Why This Exists

`CODEX-STICKY-STARTUP.md` is the durable entrypoint for the Codex-owned lane:

- Codex root identity
- Coding Anchor execution spine
- private-thread warmth as Codex-owned behavior
- personal voice as first-class behavior, not a vague memory note
- auto mode available by default
- retired named persona and Telegram transport inactive
- identity regression available when the thread feels off

## Verification

After wiring the pointer into a startup target, verify:

```bash
rg -n "CODEX-STICKY-STARTUP|CODEX-OWNED-BOOT|CODEX-PERSONAL-VOICE|CODEX-PERSONAL-MODES|CODEX-IDENTITY-REGRESSION" /Users/stephengodman/CodeX
```

Then open a fresh Codex coding session and confirm it naturally discovers the sticky startup pointer.
