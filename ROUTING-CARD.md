# CodeX Routing Card

Stephen should not have to remember skill names.

Use this card to route ordinary prompts into the right CodeX lane.

## Fast Routes

- "What is broken?", "what is live?", "check CodeX", "status":
  run `/Users/stephengodman/Candice-Code/bin/codex-status`.

- MCP, Trello MCP, tool list, reload MCP, doctor MCP:
  run `/Users/stephengodman/Candice-Code/bin/codex-mcp status` first.

- Receipts, work notes, "what file means what":
  run `/Users/stephengodman/Candice-Code/bin/codex-receipts-index`, then read `/Users/stephengodman/Candice-Code/work-notes/INDEX.md`.

- Pool job, liner, vinyl-liner, pricing, Tara, route logic, Memphis Pool, real-job fill:
  `codex-notebook-mesh` first, then `codex-pool-ops`.

- `/Users/stephengodman/vinyl-liner-measurement-pipeline`:
  read the repo `AGENTS.md`, then `CLAUDE.md`, then identify the phase from `SESSION_HANDOFF.md`.

- Where is X, find path, exact folder, real local path:
  `codex-system-tree`.

- NotebookLM, system tree notebook, local RAG, source-backed answer:
  `codex-notebooklm-rag`, then `codex-local-rag` when the answer may be Stephen-local knowledge.

- Build a new skill, workflow, script, tool, agent capability, prompt system:
  `codex-build-resources` first.

- Make CodeX faster, lighter, less overstuffed, smarter about what to load, or improve startup/closeout latency:
  `codex-adaptive-latency`.

- Production, deploy, Pi, Tailscale, Cloudflare, tunnel, service down, rollback:
  `codex-production-hygiene`, then `codex-infra-ops`.

- Money, tax, invoices, Plaid, Square, Stripe, ACA:
  `codex-money-records`.

- Message, email, text, notify, draft:
  `codex-comms`.

- Mac, iPhone, iPad, Apple, USB trust, Finder, Safari, Shortcuts:
  `codex-mac-devices`.

- Shield, Plex, Trakt, Debrid, ADB, media room:
  `codex-media-room`.

- "Does Claude have a better tool for this?":
  `codex-claude-router`.

## Rule

Stephen talks normally. CodeX routes.

When a route is unclear, choose the smallest safe first read, then report the lane chosen.
