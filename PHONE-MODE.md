# CodeX Phone / Away Mode

This is the operating contract for Stephen saying things like:

- "I'm away from the computer"
- "phone mode"
- "away mode"
- "I'm running you from my phone today"

## Command

Preview:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode
```

Apply:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --apply
```

`--apply` enables the stronger lid-closed path by default.

Status:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --status
```

## What Phone Mode Means

CodeX should assume Stephen is not physically at the Mac.

Do not expect Stephen to:

- touch the fingerprint scanner
- approve a local prompt immediately
- read a Mac screen
- recover a modal dialog
- hear notifications

Do keep the Mac useful for remote operation:

- keep Codex running
- keep iTerm available
- keep Tailscale and network access up
- keep Cloudflare tunnel and remote-control helpers up
- keep CodeX MCP helpers up
- keep the Trello photo bridge up unless Stephen asks for a deeper shutdown

## What Gets Shut Down

Phone mode stops or unloads nonessential heavyweight/local stacks:

- SillyTavern
- Rook Telegram
- LM Studio and LM Studio headless
- ComfyUI / Venice
- Ollama
- Redis
- Postgres

It also quits low-risk visible apps when possible and hides document-style apps instead of force-quitting them. This avoids losing unsaved work.

## Privacy And Power

Phone mode applies the quiet/private Mac posture:

- start or preserve `caffeinate` so the Mac stays awake
- mute output
- set alert volume to zero
- require password immediately on wake
- hide non-Codex windows
- lock the screen
- sleep the display

For closet / portable-battery operation, phone mode requests lid-closed survival by default:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --apply
```

That uses macOS `pmset disablesleep=1` when sudo permission is available. Restore normal sleep later with:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --restore-sleep
```

If `disablesleep` cannot be enabled, lid-close operation remains best-effort and can stop Codex until the Mac wakes.

The GitHub pattern for lid-closed agents is consistent: `caffeinate` handles idle sleep, but lid-close survival needs `pmset disablesleep`. CodeX phone mode therefore treats `--lid-closed` as the stronger closet/portable-battery path.

## Credential Book Rule

There is no plaintext password book in the CodeX repo.

The "credential book" for phone mode is a map of allowed sources:

- environment variables already loaded into the Codex app or macOS user environment
- native MCP servers that can use scoped credentials without exposing plaintext values
- 1Password CLI or 1Password MCP when available
- Stephen's local credential profile when a tool already supports it

In phone mode, CodeX should preload runtime credentials where possible:

1. Load `/Users/stephengodman/.codex-phone-mode.env` into the macOS user environment when present.
2. If that cache is missing, try the existing one-unlock 1Password loader with `/opt/homebrew/bin` on `PATH`.
3. If the 1Password CLI blocks on app/Touch ID approval, fall back to the local profile for known API environment variables.
4. Report only variable names loaded or missing. Do not print values into chat, notes, logs, or git.

The phone-mode env cache lives outside the repo at `/Users/stephengodman/.codex-phone-mode.env` and must stay `0600`.

CodeX may use these sources autonomously when the task requires credentials, but must not print, write, or commit raw secret values.

If 1Password or macOS asks for physical biometric or hardware approval and automation cannot complete it, CodeX should switch paths first. Only block on Stephen after the available non-physical credential paths fail.

## Away-Mode Decision Rules

When in phone mode:

- prefer API-first paths over browser UI
- prefer read/status checks before state-changing work
- use dry-run or preview modes when a tool supports them
- do not start local heavyweight model stacks unless the active task requires them
- do not rely on desktop notifications for Stephen
- use Pushover only for time-sensitive alerts
- leave a clear report of what was stopped, what stayed up, and what remains blocked

## Safety Line

Phone mode is not permission to be careless with secrets, money, messages, or destructive filesystem/git operations.

It is permission to assume Stephen is remote and to choose remote-friendly, low-friction execution paths.
