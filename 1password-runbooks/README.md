# 1Password Runbooks

This packet turns the NotebookLM 1Password gap work into local CodeX execution surfaces.

## What This Solves

- Stop using guessed `op environment` syntax when the local CLI does not expose it.
- Keep SCIM/Entra provisioning on the documented SCIM URL + bearer token lane, not an OAuth callback lane.
- Keep CodeX pointed at the native 1Password MCP server for Environments work.
- Preserve the `DATA NOT IN SOURCES` guardrail where external docs still do not provide general-purpose execution mechanics.

## Files

- `verify_op_beta.sh` checks whether the installed `op` binary exposes the beta Environments commands documented by 1Password.
- `mcp-environments-migration.md` captures the local migration posture from legacy `op run` wrappers to native 1Password Environments through the Codex MCP server.
- `entra-hosted-provisioning.md` captures the Entra hosted provisioning correction: SCIM URL + bearer token, not OAuth callback setup.
- `notebooklm-results.md` summarizes the two saved NotebookLM outputs that drove this packet.

## Current Local Truth

- Codex MCP server `1password` is configured globally.
- MCP command path: `/Applications/1Password.app/Contents/MacOS/onepassword-mcp`
- Local `op --version`: `2.34.0`
- Local `op environment --help`: currently returns `unknown command "environment" for "op"`.
- Local `op run --help`: currently exposes `--env-file`, not `--environment`.

Run:

```bash
./1password-runbooks/verify_op_beta.sh
```

