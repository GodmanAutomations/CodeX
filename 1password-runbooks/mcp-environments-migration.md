# MCP Environments Migration

## Goal

Move CodeX Environments work away from legacy `op://` secret-reference mapping and `op run --env-file` wrappers, toward native 1Password Environments managed through the Codex MCP server.

## Verified Local Setup

- Codex MCP server name: `1password`
- Command: `/Applications/1Password.app/Contents/MacOS/onepassword-mcp`
- Local preflight verifies the MCP command path.
- Room guidance exists in:
  - `/Users/stephengodman/CodeX/AGENTS.md`
  - `/Users/stephengodman/CodeX/CURRENT.md`

## Migration Checklist

1. Inventory legacy secret injection:
   - `.env`
   - `.env.tpl`
   - shell wrappers using `op run`
   - config files containing `op://` references

2. Classify each variable:
   - runtime secret
   - non-secret config
   - local-only development value
   - CI/CD value

3. Create or select the matching 1Password Environment through the `1password` MCP server.

4. Add variable names and placeholder structure through MCP. Keep plaintext secret values outside CodeX context.

5. Use 1Password authorization prompts as the access gate. Do not paste secrets into notes, prompts, logs, or repository files.

6. Mount or inject environment variables through the MCP-supported 1Password workflow at runtime.

7. Remove legacy `op run` wrappers only after the new environment path has a working smoke test.

## Current Blocker

The external 1Password docs describe:

```bash
op environment read <environmentID>
op run --environment <environmentID> -- <command>
```

But this Mac currently reports:

```text
op environment --help -> unknown command "environment" for "op"
op run --help -> no --environment flag
```

So the stable local CLI is not the execution surface for this migration yet. Use the `1password` MCP server first.

## Guardrail

If a specific command, endpoint, or setup step is absent from the source set, write:

```text
DATA NOT IN SOURCES: REQUIRES EXTERNAL DOCUMENTATION
```

Do not invent `op environment sync`, `op environment pull`, `op mcp init`, or any similar ghost command.

