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

Compact phone check:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --summary
```

`--summary` requires AC power by default. If the Mac is on battery, it reports
`ready: no (power)` and exits non-zero instead of pretending the phone lane is
safe. Only bypass this intentionally:

```bash
CODEX_PHONE_ALLOW_BATTERY=1 /Users/stephengodman/CodeX/bin/codex-phone-mode --summary
```

Refresh the local phone credential cache while the Mac has access:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --refresh-cache
```

Apply and send a phone notification:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --apply --notify
```

Pushover alerts are silent by default for phone mode and watchdog:

```bash
CODEX_PUSHOVER_PRIORITY=-1
CODEX_PUSHOVER_SOUND=none
```

Set those env vars only when an audible alert is intentional. The phone lane
accepts priority `-2`, `-1`, `0`, or `1`; emergency priority `2` is not used
because Pushover requires extra retry/expire fields for that mode.

Full auto watchdog:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode-watchdog --install
/Users/stephengodman/CodeX/bin/codex-phone-mode-watchdog --status
```

The watchdog runs every five minutes. It checks the compact phone summary,
Codex app presence, the managed phone-mode `caffeinate` LaunchAgent,
lid-closed sleep state, the phone credential cache, and battery state. It
repairs safe drift with bounded `codex-phone-mode --apply --no-sleep-display`
and sends Pushover only when state changes, repairs happen, failures happen, or
battery protection matters.

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
- keep Coding Anchor boot/doctor/agentic-check healthy
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

Phone mode treats AC power as a required readiness signal. Normal summary and
apply flows fail when the Mac is drawing from battery, unless
`CODEX_PHONE_ALLOW_BATTERY=1` is set for that command. This keeps the phone lane
honest when Stephen has told CodeX not to spend battery.

For closet / remote operation, phone mode requests lid-closed survival by default:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --apply
```

That uses macOS `pmset disablesleep=1` when sudo permission is available. Restore normal sleep later with:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode --restore-sleep
```

If `disablesleep` cannot be enabled, lid-close operation remains best-effort and can stop Codex until the Mac wakes.

The GitHub pattern for lid-closed agents is consistent: `caffeinate` handles
idle sleep, but lid-close survival needs `pmset disablesleep`. CodeX phone mode
therefore treats `--lid-closed` as the stronger closet/remote path, still gated
by the AC-power readiness rule unless `CODEX_PHONE_ALLOW_BATTERY=1` is set.

The apply-time AC gate and the watchdog thresholds are separate protections.
The gate blocks new phone-mode apply attempts while on battery. The watchdog
still protects already-running phone mode automatically: if the Mac is on
battery and drops to 30% or lower, it sends a warning; if it drops to 20% or
lower, it restores sleep and sleeps the Mac unless the battery override file is
present. Use:

```bash
/Users/stephengodman/CodeX/bin/codex-phone-mode-watchdog --battery-override-on
/Users/stephengodman/CodeX/bin/codex-phone-mode-watchdog --battery-override-off
```

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
Use `--refresh-cache` while local credential sources are available to turn
`op://` references into cached runtime values for phone-only work.

CodeX may use these sources autonomously when the task requires credentials, but must not print, write, or commit raw secret values.

If 1Password or macOS asks for physical biometric or hardware approval and automation cannot complete it, CodeX should switch paths first. Only block on Stephen after the available non-physical credential paths fail.

## Coding Anchor Readiness

Phone mode must keep the Coding Anchor execution packet usable without Stephen
opening the Mac:

- ensure the Codex app is running or request launch
- run `Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-agentic-check`
- run `Coding Anchor Files/codex-coding-anchor/bin/coding-anchor-doctor`
- report `coding-anchor-next` state so Stephen knows whether an autonomous
  slice is ready

This readiness check is part of `/Users/stephengodman/CodeX/bin/codex-phone-mode --apply`
and `/Users/stephengodman/CodeX/bin/codex-phone-mode --status`.

## Away-Mode Decision Rules

When in phone mode:

- prefer API-first paths over browser UI
- prefer read/status checks before state-changing work
- use dry-run or preview modes when a tool supports them
- do not start local heavyweight model stacks unless the active task requires them
- do not rely on desktop notifications for Stephen
- use Pushover only for time-sensitive alerts
- use `--summary` or `--notify` when Stephen is reading from the phone
- leave a clear report of what was stopped, what stayed up, and what remains blocked

## Safety Line

Phone mode is not permission to be careless with secrets, money, messages, or destructive filesystem/git operations.

It is permission to assume Stephen is remote and to choose remote-friendly, low-friction execution paths.
