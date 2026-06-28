# Adapter Recommendation: Taskmaster / Agentic Workflow Tools

Date: 2026-06-26

## Verdict

Do not install Task Master, Taskqueue MCP, Agent Task Queue, or a broad
autonomous-agent framework over this packet right now.

Keep the native CodeX queue as the primary local handhold:

- `state/work-queue.json`
- `bin/coding-anchor-next`
- `bin/coding-anchor-start`
- `bin/coding-anchor-done`
- `bin/coding-anchor-loop`
- `bin/coding-anchor-doctor`

Add adapters only when a real project needs them.

## Why

Task Master is closest to the requested shape: it has PRD parsing, task listing,
next-task selection, research, dependency-aware movement, CLI commands, and an
MCP server. It is useful to learn from, but too much to make this packet depend
on by default.

`taskqueue-mcp` overlaps with this packet's local queue: structured multi-step
task planning, progress tracking, task status management, and optional user
approval checkpoints. That makes it a possible MCP adapter later, not a reason
to replace the native queue now.

`block/agent-task-queue` solves a different problem: local FIFO queuing so
multiple agents do not run expensive operations concurrently. That is useful if
this Mac starts running several agents against shared build/test resources, but
it is not the same as Coding Anchor's next-slice continuity queue.

GitHub Agentic Workflows is the strongest official GitHub-side candidate. It
supports agentic repository automation in GitHub Actions, including Codex, but
it is public preview and repo/CI oriented. It belongs behind an explicit project
adapter, not inside the local boot packet.

Generic autonomous-agent repos found through GitHub topics are less relevant
than the packet's current need. Most add runtimes, daemons, or new agent
identities; this packet needs bounded local continuity, verification, and review
discipline.

## Adapter Path

Use this order when a real project needs more:

1. Native queue first.
2. Add import/export from Task Master or Taskqueue MCP task files if a project
   already uses one of them.
3. Add Agent Task Queue only when local multi-agent build/test contention
   becomes a real problem.
4. Add a GitHub Agentic Workflows recipe only for repository-level scheduled or
   event-triggered maintenance.
5. Do not install a daemon or broad agent framework unless Stephen explicitly
   wants that tradeoff.

## Sources Checked

- Task Master repository: https://github.com/eyaltoledano/claude-task-master
- Task Master npm package: https://www.npmjs.com/package/task-master-ai
- Taskqueue MCP repository: https://github.com/chriscarrollsmith/taskqueue-mcp
- Taskqueue MCP registry page: https://mcpmarket.com/es/server/taskqueue
- Agent Task Queue repository: https://github.com/block/agent-task-queue
- GitHub Agentic Workflows docs: https://github.github.com/gh-aw/
- GitHub Agentic Workflows repository: https://github.com/github/gh-aw
- GitHub autonomous-agent topic scan:
  https://github.com/topics/autonomous-agent?l=typescript
