
## Venice Bench

Run a small model comparison and save a JSON receipt:

```bash
/Users/stephengodman/CodeX/bin/codex-venice-bench
```

Custom run:

```bash
/Users/stephengodman/CodeX/bin/codex-venice-bench \
  --model venice-uncensored-1-2 \
  --model z-ai-glm-5-turbo \
  --prompt "Find the weakest assumption in this plan." \
  --max-tokens 128
```

Results are written to:

`/Users/stephengodman/CodeX/venice/results/`

Secrets stay environment-only. The bench can read `VENICE_API_KEY` or `VENICE_ADMIN_KEY` from the shell environment or macOS `launchctl` environment, but it never writes keys to disk.

## Venice Leaderboard

Summarize the latest bench receipt:

```bash
/Users/stephengodman/CodeX/bin/codex-venice-leaderboard
```

Summarize a specific receipt:

```bash
/Users/stephengodman/CodeX/bin/codex-venice-leaderboard /Users/stephengodman/CodeX/venice/results/example-venice-bench.json
```

## Venice Sidecar

Ask Venice for one bounded second opinion. This is a sidecar, not an executor.

```bash
/Users/stephengodman/CodeX/bin/codex-venice-sidecar "A helper wants to install 592 packages to fix one missing import. Tell it the smarter move."
```

Rules:

- Uses `venice-uncensored-role-play` by default.
- Saves a JSON receipt in `venice/results/`.
- Redacts obvious secret-looking strings before sending.
- Does not give Venice tool authority.
- CodeX decides what to actually execute.

### Sidecar Modes

```bash
/Users/stephengodman/CodeX/bin/codex-venice-sidecar --mode critic "Find the weakest assumption in this plan."
/Users/stephengodman/CodeX/bin/codex-venice-sidecar --mode weird "Give 5 strange but usable ideas."
/Users/stephengodman/CodeX/bin/codex-venice-sidecar --mode gremlin "Give me useful gremlin ideas for CodeX."
/Users/stephengodman/CodeX/bin/codex-venice-sidecar --mode security "Should this secret go in notes?"
```

Mode map:

- `default`: blunt practical sidecar
- `critic`: weakest assumption and likely failure mode
- `weird`: strange but usable ideas
- `gremlin`: playful, sharp, unfiltered, shop-floor humor
- `security`: secrets, authority, and tool boundaries

## Venice Search

Search through Venice's `/augment/search` endpoint. Brave is the default provider.

```bash
/Users/stephengodman/CodeX/bin/codex-venice search "agent reflection episodic memory" --limit 5
```

Provider options:

- `brave`
- `google`

Venice docs:

- https://docs.venice.ai/api-reference/endpoint/augment/search
