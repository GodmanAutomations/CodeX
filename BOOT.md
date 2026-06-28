# Boot

Use this boot sequence for ordinary CodeX room openers.

## Sequence

```bash
/Users/stephengodman/CodeX/bin/codex-startup
```

The startup script should:

- load `CODEX-OWNED-BOOT.md`
- land CodeX in the Coding Anchor default posture
- load the Best Lane operating contract
- load `CODEX-THREAD-PROFILE.md`
- load `CODEX-PERSONAL-VOICE-PROFILE.md`
- load `CODEX-PERSONAL-MODES.md`
- surface `docs/agent-protocol.md` for advisor-directed work
- load `CODEX-IDENTITY-REGRESSION.md`
- expose the Identity Regression Harness through `bin/codex-identity-regression`
- refresh the heartbeat
- turn the bench light on
- check startup continuity
- report SQLite memory status
- recall startup memory items
- report capability registry status
- print the current task surface

## Health Check

For a fuller room check:

```bash
/Users/stephengodman/CodeX/bin/codex-doctor-room
```

For identity/startup/personal voice regression:

```bash
/Users/stephengodman/CodeX/bin/codex-identity-regression
```

For pre-Codex prerequisite repair:

```bash
/Users/stephengodman/CodeX/bin/codex-ensure-standalone --repair
```

## Boot Is Good When

- the room is clearly `/Users/stephengodman/CodeX`
- the default self is clearly CodeX Coding Anchor, not old Anchor/Gemini
- the Best Lane is visible for autonomous, phone-aware work
- the Thread Profile, Personal Voice Profile, Personal Modes, and Identity
  Regression surfaces are visible
- advisor-directed work knows to use `docs/agent-protocol.md`
- the Identity Regression Harness is available
- the heartbeat is fresh
- startup continuity is readable
- SQLite startup memories are recalled
- the capability registry loads
- the active task surface is known, or none is set yet
