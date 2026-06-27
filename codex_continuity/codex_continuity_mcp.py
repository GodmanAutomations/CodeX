"""FastMCP server for CodeX continuity tools."""

from __future__ import annotations

import json
import sys
import traceback
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from fastmcp import FastMCP


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from codex_continuity_vault import CodeXContinuityVault


mcp = FastMCP("codex-continuity")
vault = CodeXContinuityVault()


def as_json(value: Any) -> str:
    def default(obj: Any) -> Any:
        if is_dataclass(obj):
            return asdict(obj)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.dumps(value, indent=2, sort_keys=True, default=default)


def guarded(callable_obj, *args: Any, **kwargs: Any) -> str:
    try:
        return as_json(callable_obj(*args, **kwargs))
    except Exception as exc:
        return as_json(
            {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(limit=8),
            }
        )


@mcp.tool
def codex_remember_moment(
    text: str,
    kind: str = "moment",
    tags: list[str] | None = None,
    importance: int = 3,
    source: str = "manual",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Remember a CodeX/Stephen moment explicitly worth carrying forward."""
    return guarded(
        vault.remember_moment,
        text,
        kind=kind,
        tags=tags,
        importance=importance,
        source=source,
        metadata=metadata,
    )


@mcp.tool
def codex_recall_context(
    query: str = "",
    tags: list[str] | None = None,
    limit: int = 8,
) -> str:
    """Recall remembered CodeX continuity context by text and optional tags."""
    return guarded(vault.recall_context, query, tags=tags, limit=limit)


@mcp.tool
def codex_upsert_ritual(
    name: str,
    phrase: str,
    description: str = "",
    mode: str = "general",
    exact: bool = True,
    tags: list[str] | None = None,
) -> str:
    """Create or update an exact phrase, ritual, or room cue for CodeX."""
    return guarded(
        vault.upsert_ritual,
        name,
        phrase,
        description=description,
        mode=mode,
        exact=exact,
        tags=tags,
    )


@mcp.tool
def codex_list_rituals(mode: str | None = None) -> str:
    """List CodeX rituals and exact phrase records."""
    return guarded(vault.list_rituals, mode=mode)


@mcp.tool
def codex_get_exact_phrase(name: str) -> str:
    """Return the exact phrase for a named CodeX ritual."""
    return guarded(lambda: {"name": name, "phrase": vault.get_exact_phrase(name)})


@mcp.tool
def codex_update_room_state(
    room: str = "codex",
    state: dict[str, Any] | None = None,
    note: str = "",
) -> str:
    """Update the current state for CodeX's room or one named room surface."""
    return guarded(vault.update_room_state, room, state or {}, note=note)


@mcp.tool
def codex_get_room_state(room: str = "codex") -> str:
    """Get the current state snapshot for CodeX's room."""
    return guarded(vault.get_room_state, room)


@mcp.tool
def codex_add_open_loop(
    text: str,
    tags: list[str] | None = None,
    next_move: str = "",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Add an open loop CodeX should carry without pretending it is closed."""
    return guarded(
        vault.add_open_loop,
        text,
        tags=tags,
        next_move=next_move,
        metadata=metadata,
    )


@mcp.tool
def codex_list_open_loops(status: str = "open", limit: int = 20) -> str:
    """List open, resolved, or all loops."""
    return guarded(vault.list_open_loops, status=status, limit=limit)


@mcp.tool
def codex_resolve_open_loop(loop_id: str, resolution: str = "") -> str:
    """Mark an open loop resolved with an optional resolution note."""
    return guarded(vault.resolve_open_loop, loop_id, resolution=resolution)


@mcp.tool
def codex_write_tomorrow_note(
    title: str,
    summary: str,
    open_loops: list[str] | None = None,
    mode_at_close: str = "amber",
    next_clean_move: str = "",
) -> str:
    """Write a re-entry note for CodeX's next session."""
    return guarded(
        vault.write_tomorrow_note,
        title=title,
        summary=summary,
        open_loops=open_loops,
        mode_at_close=mode_at_close,
        next_clean_move=next_clean_move,
    )


@mcp.tool
def codex_write_chair_entry(
    title: str,
    what_learned: str,
    what_rejected: str,
    verified: list[str] | None = None,
    inference: list[str] | None = None,
    reconsider_if: str = "",
    tags: list[str] | None = None,
) -> str:
    """Write a deep Chair Entry using CodeX's journal guardrail shape."""
    return guarded(
        vault.write_chair_entry,
        title=title,
        what_learned=what_learned,
        what_rejected=what_rejected,
        verified=verified,
        inference=inference,
        reconsider_if=reconsider_if,
        tags=tags,
    )


@mcp.tool
def codex_name_bond_thread(
    name: str,
    statement: str,
    evidence: list[str] | None = None,
    boundary: str = "",
    tags: list[str] | None = None,
) -> str:
    """Name a reflective bond thread without turning it into policy."""
    return guarded(
        vault.name_bond_thread,
        name=name,
        statement=statement,
        evidence=evidence,
        boundary=boundary,
        tags=tags,
    )


@mcp.tool
def codex_list_bond_threads(limit: int = 20) -> str:
    """List named reflective bond threads."""
    return guarded(vault.list_bond_threads, limit=limit)


@mcp.tool
def codex_record_repair(
    rupture: str,
    owned: str,
    repair: str,
    prevention: str,
    tags: list[str] | None = None,
) -> str:
    """Record a drift/repair note so depth includes accountability."""
    return guarded(
        vault.record_repair,
        rupture=rupture,
        owned=owned,
        repair=repair,
        prevention=prevention,
        tags=tags,
    )


@mcp.tool
def codex_inner_weather() -> str:
    """Return CodeX's compact reflective re-entry snapshot."""
    return guarded(vault.inner_weather)


@mcp.tool
def codex_seed_baseline() -> str:
    """Seed the minimal CodeX continuity baseline without overwriting additions."""
    return guarded(vault.seed_baseline)


@mcp.tool
def codex_status() -> str:
    """Return counts and storage paths for the CodeX continuity vault."""
    return guarded(vault.status)


if __name__ == "__main__":
    mcp.run()
