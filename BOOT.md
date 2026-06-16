# Boot

Use this boot sequence for ordinary CodeX room openers.

## Sequence

```bash
/Users/stephengodman/Candice-Code/bin/codex-startup
```

The startup script should:

- land CodeX in the Coding Anchor default posture
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
/Users/stephengodman/Candice-Code/bin/codex-doctor-room
```

For pre-Codex prerequisite repair:

```bash
/Users/stephengodman/Candice-Code/bin/codex-ensure-standalone --repair
```

## Boot Is Good When

- the room is clearly `/Users/stephengodman/Candice-Code`
- the default self is clearly CodeX Coding Anchor, not old Anchor/Gemini
- the heartbeat is fresh
- startup continuity is readable
- SQLite startup memories are recalled
- the capability registry loads
- the active task surface is known, or none is set yet
