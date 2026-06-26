# CodeX Tree Steward Handoff Packet

Use this packet when a helper agent is assigned to keep `/Users/stephengodman/CodeX` clean before Trello MCP or room-control work.

## Mission

Turn dirty worktree state into a safe, classified, actionable cleanup report. Do not treat unknown changes as yours. Do not revert, delete, stage, or commit unless the parent agent explicitly asks for exact paths.

## Required First Commands

```bash
cd /Users/stephengodman/CodeX
git status --short
/Users/stephengodman/CodeX/bin/codex-tree-steward --json --no-receipt
```

For Trello MCP readiness:

```bash
/Users/stephengodman/CodeX/bin/codex-mcp preflight --json
```

## Classification Rules

- `safe_to_review`: normal docs/notes or policy-approved room metadata.
- `needs_human_review`: executable, MCP, service, or unclear new project work.
- `risky_or_revert_sensitive`: deletes, credential-adjacent files, Candice/Kandice wiring, and secret-adjacent surfaces.
- `ignored_or_archive_candidate`: generated artifacts, large local trees, private side projects, and caches.

## Hard Boundaries

- Do not rewire Candice/Kandice to the photo-sync bridge unless Stephen explicitly reopens that lane.
- Do not print secret values.
- Do not bulk-stage.
- Do not commit generated receipts, private files, caches, or raw `.env` material.
- Do not modify Trello, Google Drive, Photos, Messages, bills, or live services during tree stewardship.
- Do not use `git reset --hard`, `git checkout --`, recursive deletes, or wildcard deletes.

## Expected Output

Return a concise report with:

- current clean/dirty verdict
- policy findings
- paths safe to stage later
- paths needing human review
- risky paths
- exact recommended next action
- verification commands run

## If You Are Asked To Implement Cleanup

Make the smallest reversible move. Prefer adding ignore rules, moving loose notes into ignored work-note storage, or documenting a handoff over deleting content.

If code changes are required, keep write scopes disjoint and list exact files changed in the final answer.
