# Claude Capabilities Bridge

Source inventory:

`/Users/stephengodman/claude-capabilities.md`

Generated there: 2026-06-03.

This is a bridge map, not a CodeX identity file.

Use it when CodeX needs to know whether a task is better handled by Claude/Ace or by a Claude-only skill, connector, agent, hook, or workflow.

## Rule

Do not pretend Claude-only skills are native CodeX tools.

When a lane is better served by Claude, say that plainly and prepare a clean handoff prompt or command.

When CodeX has an equivalent local tool, use the CodeX tool directly.

## High-Value Claude-Only Or Claude-Strong Lanes

### Artesian / Pool Ops

Claude inventory names:

- `pool-ops-kb`
- `pool-chemistry`
- `memos`
- `pool`
- `trello`
- agents: `artesian-pools`, `artesian-field-ops`

Use when pool job knowledge, Memphis Pool workflows, board-specific work, or field ops memory is needed.

### Money / Tax / Business Records

Claude inventory names:

- `tax-search`
- `invoice-organizer`
- `file-organizer`
- `plaid`
- `square`
- `stripe`
- `intel`
- `intel-digest`
- `summon-intel`

Use when finance, taxes, invoices, banking, Square/Plaid/Stripe, or forensic record gathering matters.

### Comms And Notifications

Claude inventory names:

- `imessage_automation`
- `message-crafter`
- `mail_automation`
- `draft`
- `pushover`
- `twilio`

CodeX can use local/Pushover-style paths when available, but Claude may have richer message-channel workflows.

### Mac / Apple / Device Automation

Claude inventory names:

- `macos-control`
- `macos-computer-use`
- `applescript_jxa_bridge`
- `finder_file_automation`
- `iphone_shortcuts_bridge`
- `icloud_notes`
- `icloud_reminders_calendar`
- `photos_automation`
- `safari_automation`
- `ios-automation`

CodeX has macOS and computer-use skills too, but this inventory is useful for handoffs that need Claude's Apple-specific workflows.

### Infra

Claude inventory names:

- `tailscale`
- `cloudflare`
- `cloudflare(skill)`
- `ops-check`
- `deploy`

CodeX has Cloudflare/Vercel capabilities, but Claude may have richer Stephen-specific Pi5/Tailscale operational memory.

### Media / Shield / Plex

Claude inventory names:

- `adb`
- `nvidia_shield_*`
- `plex_media_server_api`
- `media-room`
- `media_music_control`
- `trakt_*`
- `torrentio_*`
- `multi_debrid_*`
- `magnet_to_pipeline_automation`
- `unified_content_search`

Route media-room and NVIDIA Shield/Plex control work through Claude unless CodeX has the exact local tool and context loaded.

### Knowledge / NotebookLM / RAG

Claude inventory names:

- `notebooklm-integration`
- `notebook-wizard`
- `notebooklm-enterprise`
- `functional-medicine-kb`
- `ouraring`
- `firecrawl`
- `firecrawl-api`
- `godman-rag`
- `notebook-mesh`

CodeX already has the `SYSTEM-TREE.md`, `systree`, `refresh-systree`, and local NotebookLM CLI lane. Use Claude bridge when the task depends on Claude's NotebookLM workflows, local RAG, or named notebook agents.

### AI Service Wrappers

Claude inventory names:

- `anthropic`
- `openai`
- `gemini`
- `google-ai`
- `groq`
- `xai`
- `elevenlabs`
- `amazon-aws`
- `github`
- `wix`

Use this as a hint that Claude may have established wrapper patterns, especially async/circuit-breaker patterns.

### Python / Debug / Review

Claude inventory names:

- `python-development`
- `async-python-patterns`
- `python-testing-patterns`
- `python-resilience`
- `chrome-devtools`
- `code-review`
- `coderabbit-review`
- `deep-debug`
- `inventory-first`
- `cutover-readiness`

CodeX can do code work directly. Use this bridge if Stephen asks specifically for Claude's review/ultrareview/hooks or Python plugin lane.

## Claude Native Superpowers To Remember

Claude inventory says Claude has:

- subagents
- deterministic workflows
- background tasks
- monitors
- scheduled agents / cron
- `/loop`
- worktrees
- persistent file memory
- hooks
- cloud ultrareview
- browser control through Chrome, Playwright, and DevTools MCP
- Pushover notifications

CodeX should not claim these as identical unless they exist in the current CodeX tool surface. Treat them as handoff options or capability references.

## Handoff Shape

When CodeX needs Claude for one of these lanes, prepare a short prompt like:

```text
Use your [skill/agent/lane] for this. Context:
- Goal:
- Exact paths:
- What CodeX verified:
- What not to touch:
- Desired output:
```

Keep the handoff concrete, pathful, and free of secrets.
