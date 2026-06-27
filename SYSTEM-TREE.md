# CodeX System Tree Map

This is the CodeX pointer to Stephen's local filesystem map.

Use this before broad disk searches when the task is "where does X live?" or when a model/notebook output gives vague paths.

## NotebookLM Map

Notebook:

`https://notebooklm.google.com/notebook/ce7315a6-ffa7-4ce8-a316-b59cd41193d9?authuser=0`

Notebook name:

`System Tree - Local Filesystem Map`

What it is:

- 5 NotebookLM source files.
- Current local count after `refresh-systree`: 714,625 scrubbed absolute paths.
- Built from `/Users/stephengodman/system_tree/paths_scrubbed.txt`.
- Secrets are scrubbed before upload.

Use the prompt in `/Users/stephengodman/system_tree/README.md` when chatting with the notebook so NotebookLM emits real paths instead of placeholders.

## Local Files

Root:

`/Users/stephengodman/system_tree/`

Important files:

- `system_tree_part_01.md` through `system_tree_part_05.md` - upload sources for NotebookLM.
- `paths_scrubbed.txt` - source-of-truth flat manifest after secret path scrubbing.
- `_full_tree.txt` - local-only decorated tree output, about 126 MB.
- `exclusions.sh` - source it for `sgfind`, `sgfd`, and shared exclusion strings.
- `system_tree.db` - SQLite path index used by `systree`.
- `README.md` - NotebookLM prompt, excluded paths, and regeneration notes.
- `paths_all.txt` - removed to Trash by Claude after verification; no longer part of the active system tree.

## Commands

Refresh local map only:

```bash
/Users/stephengodman/bin/refresh-systree
```

Refresh local map and upload fresh sources to NotebookLM:

```bash
/Users/stephengodman/bin/refresh-systree --upload
```

NotebookLM CLI:

```bash
/Users/stephengodman/.local/bin/notebooklm
```

`refresh-systree --upload` uses this CLI and the saved NotebookLM browser auth/session.

Fast local path queries:

```bash
/Users/stephengodman/bin/systree find <term>
/Users/stephengodman/bin/systree name <term>
/Users/stephengodman/bin/systree dir <term>
/Users/stephengodman/bin/systree ext py
/Users/stephengodman/bin/systree stats
/Users/stephengodman/bin/systree sql "select path from paths where name like '%foo%' limit 20"
```

`systree` queries `/Users/stephengodman/system_tree/system_tree.db` and is the fast first move for path questions.

## Search Exclusions

Noise exclusions are installed at:

- `/Users/stephengodman/.config/fd/ignore`
- `/Users/stephengodman/.claudeignore`
- `/Users/stephengodman/system_tree/exclusions.sh`

These exclude noise such as caches, `node_modules`, virtualenvs, `~/Library`, and Pi mounts. They do not make local secret paths unsearchable; the upload scrub is separate.

Bypasses:

```bash
fd -I --no-ignore <term>
rg --no-ignore <term>
```

## Memory Pointers

Claude-side memory notes are in:

`/Users/stephengodman/.claude/projects/-Users-stephengodman-active/memory/`

Known notes:

- `search-exclusions.md` - exclusion set plus `systree` and `exclusions.sh` pointers.
- `vet-notebooklm-cheatcodes.md` - NotebookLM cheatcode outputs should be vetted first because they can be confidently wrong.

## Rule

For path-location questions:

1. Try `systree` first.
2. Use `refresh-systree` if the map is stale after folder moves.
3. Use NotebookLM when a model needs the broader path map context.
4. Do not upload raw secret paths or secret values.
