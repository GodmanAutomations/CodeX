# Tool Rules

## Default

Use tools to prove reality, not to perform busyness.

## Smoke Test Rule

After changing code, shell wrappers, launchers, MCP wiring, or local tools, run the smallest meaningful smoke test.

Examples:

- CLI change: run `--help` or one harmless command.
- Python tool: run import or tiny sample input.
- Browser tool: fetch a public static page.
- NotebookLM route: run auth/status.
- JSON compressor: run against tiny temp JSON.
- Model-side helpers: run one short non-interactive prompt when the helper itself changed.

## Review Rule

Do not run current-diff review when the tree is clean or when no implementation changed.

Use review only for an actual diff, PR, or commit range.

## Identity Separation

Codex does not inherit Rook, Anchor, Gemini, Ace, Jacker, NotebookLM, or any room identity.

Use them as tools or references only when useful.
