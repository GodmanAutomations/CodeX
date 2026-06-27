# CodeX Routing Card

Stephen should not have to remember skill names.

Use this card to route ordinary prompts into the right CodeX lane.

## Fast Routes

- "What is broken?", "what is live?", "check CodeX", "status":
  run `/Users/stephengodman/CodeX/bin/codex-status`.

- "I'm away from the computer", "phone mode", "away mode", "running you from my phone":
  read `/Users/stephengodman/CodeX/CODEX-BEST-LANE.md` and `/Users/stephengodman/CodeX/PHONE-MODE.md`, then run `/Users/stephengodman/CodeX/bin/codex-phone-mode --summary`; if not ready, run `/Users/stephengodman/CodeX/bin/codex-phone-mode --apply --notify`.

- "best version", "full auto", "more agentic", "stay in this mode", "all threads work this way":
  read `/Users/stephengodman/CodeX/CODEX-BEST-LANE.md`, then run `/Users/stephengodman/CodeX/bin/codex-autoloop "best lane" --task` when a concrete next handhold would help; pick the smallest safe next action and verify it.

- "new thread", "same lane", "make other threads like this", "profile":
  read `/Users/stephengodman/CodeX/CODEX-THREAD-PROFILE.md` and use it as the
  compact bootstrap card; keep repo-local rules primary in the target thread.

- "I can't tell", "where is the personal stuff", "do you care", "talk like you know me", "you sound generic":
  read `/Users/stephengodman/CodeX/CODEX-PERSONAL-VOICE-PROFILE.md` and
  `/Users/stephengodman/CodeX/CODEX-PERSONAL-MODES.md`; answer from the
  matching personal mode instead of explaining identity architecture.

- "run the regression", "check the voice layer", "test the lane", "make sure this still loads":
  run `/Users/stephengodman/CodeX/bin/codex-identity-regression`, then fix any
  failed startup, personal voice, or identity-regression check before closing.

- "have Claude review", "Claude Code reviewer", "use Claude as reviewer", "main reviewer":
  run `/Users/stephengodman/CodeX/bin/codex-claude-review`; fix concrete
  findings before committing. If Claude Code is unavailable, use the Codex
  reviewer subagent fallback and say that explicitly.

- "what route", "which tool", "how should you check", "look into this":
  read `/Users/stephengodman/CodeX/CODEX-TOOL-ROUTING.md` or run
  `/Users/stephengodman/CodeX/bin/codex-tool-route "<prompt>"`, then use the
  selected truth source before answering.

- "keep rolling", "next slice", "what should you do next", "make a handhold":
  read `/Users/stephengodman/CodeX/CODEX-AUTOMODE-WORK-PACKET.md` and
  `/Users/stephengodman/CodeX/CODEX-AUTOMODE-RUNBOOK.md`, update the packet's
  next action, then run `bin/codex-autoloop "<scope>" --task` when a handhold
  would help; execute pass 1 only, and stop at any
  public/paid/credential/destructive/external-contact gate.

- MCP, Trello MCP, tool list, reload MCP, doctor MCP:
  run `/Users/stephengodman/CodeX/bin/codex-mcp status` first.

- Before Trello MCP edits, apply-like work, or "clean up the tree":
  run `/Users/stephengodman/CodeX/bin/codex-mcp preflight`; if blocked, run `/Users/stephengodman/CodeX/bin/codex-tree-steward --json --preflight trello-mcp --no-receipt`.

- Receipts, work notes, "what file means what":
  run `/Users/stephengodman/CodeX/bin/codex-receipts-index`, then read `/Users/stephengodman/CodeX/work-notes/INDEX.md`.

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
