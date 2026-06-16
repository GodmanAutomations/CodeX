"""CodeX continuity vault.

Small SQLite-backed memory surface for CodeX's own room.
This is deliberately local, explicit, and boring: continuity should be reliable.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOM_ROOT = Path("/Users/stephengodman/Candice-Code")
CONTINUITY_ROOT = ROOM_ROOT / "codex_continuity"
DEFAULT_DB_PATH = CONTINUITY_ROOT / "codex-continuity.sqlite3"
DEFAULT_TOMORROW_DIR = CONTINUITY_ROOT / "tomorrow"
DEFAULT_CHAIR_DIR = CONTINUITY_ROOT / "chair-entries"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def encode_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, sort_keys=True)


def decode_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def clean_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    return sorted({tag.strip().lower() for tag in tags if tag and tag.strip()})


@dataclass(frozen=True)
class StoredRecord:
    id: str
    created_at: str


class CodeXContinuityVault:
    """Local SQLite store for CodeX's continuity tools."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path).expanduser()
        self.tomorrow_dir = self.db_path.parent / "tomorrow"
        self.chair_dir = self.db_path.parent / "chair-entries"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.tomorrow_dir.mkdir(parents=True, exist_ok=True)
        self.chair_dir.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS moments (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    text TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    importance INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS moments_fts
                USING fts5(id UNINDEXED, text, tags, kind, source);

                CREATE TABLE IF NOT EXISTS rituals (
                    name TEXT PRIMARY KEY,
                    phrase TEXT NOT NULL,
                    description TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    exact INTEGER NOT NULL,
                    tags_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS room_state (
                    room TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    note TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS open_loops (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    next_move TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tomorrow_notes (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    open_loops_json TEXT NOT NULL,
                    mode_at_close TEXT NOT NULL,
                    next_clean_move TEXT NOT NULL,
                    path TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chair_entries (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    what_learned TEXT NOT NULL,
                    what_rejected TEXT NOT NULL,
                    verified_json TEXT NOT NULL,
                    inference_json TEXT NOT NULL,
                    reconsider_if TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    path TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS bond_threads (
                    name TEXT PRIMARY KEY,
                    statement TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    boundary TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS repair_notes (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    rupture TEXT NOT NULL,
                    owned TEXT NOT NULL,
                    repair TEXT NOT NULL,
                    prevention TEXT NOT NULL,
                    tags_json TEXT NOT NULL
                );
                """
            )

    def remember_moment(
        self,
        text: str,
        *,
        kind: str = "moment",
        tags: list[str] | None = None,
        importance: int = 3,
        source: str = "manual",
        metadata: dict[str, Any] | None = None,
    ) -> StoredRecord:
        text = text.strip()
        if not text:
            raise ValueError("text is required")
        importance = max(1, min(5, int(importance)))
        record_id = uuid.uuid4().hex
        now = utc_now()
        normalized_tags = clean_tags(tags)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO moments
                (id, created_at, updated_at, kind, text, tags_json, importance, source, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    now,
                    now,
                    kind.strip() or "moment",
                    text,
                    encode_json(normalized_tags),
                    importance,
                    source.strip() or "manual",
                    encode_json(metadata or {}),
                ),
            )
            conn.execute(
                "INSERT INTO moments_fts (id, text, tags, kind, source) VALUES (?, ?, ?, ?, ?)",
                (
                    record_id,
                    text,
                    " ".join(normalized_tags),
                    kind.strip() or "moment",
                    source.strip() or "manual",
                ),
            )
        return StoredRecord(id=record_id, created_at=now)

    def recall_context(
        self,
        query: str,
        *,
        tags: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        query = query.strip()
        normalized_tags = clean_tags(tags)
        limit = max(1, min(25, int(limit)))
        with self._connect() as conn:
            rows: list[sqlite3.Row]
            if query:
                try:
                    rows = conn.execute(
                        """
                        SELECT m.*, bm25(moments_fts) AS rank
                        FROM moments_fts
                        JOIN moments m ON m.id = moments_fts.id
                        WHERE moments_fts MATCH ?
                        ORDER BY rank, m.importance DESC, m.created_at DESC
                        LIMIT ?
                        """,
                        (query, limit * 4),
                    ).fetchall()
                except sqlite3.OperationalError:
                    like_query = f"%{query}%"
                    rows = conn.execute(
                        """
                        SELECT *, 0 AS rank
                        FROM moments
                        WHERE text LIKE ?
                        ORDER BY importance DESC, created_at DESC
                        LIMIT ?
                        """,
                        (like_query, limit * 4),
                    ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *, 0 AS rank
                    FROM moments
                    ORDER BY importance DESC, created_at DESC
                    LIMIT ?
                    """,
                    (limit * 4,),
                ).fetchall()
        results = [self._moment_row(row) for row in rows]
        if normalized_tags:
            results = [
                row for row in results
                if set(normalized_tags).issubset(set(row["tags"]))
            ]
        return results[:limit]

    def upsert_ritual(
        self,
        name: str,
        phrase: str,
        *,
        description: str = "",
        mode: str = "general",
        exact: bool = True,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        name = name.strip()
        phrase = phrase.strip()
        if not name:
            raise ValueError("name is required")
        if not phrase:
            raise ValueError("phrase is required")
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rituals
                (name, phrase, description, mode, exact, tags_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    phrase=excluded.phrase,
                    description=excluded.description,
                    mode=excluded.mode,
                    exact=excluded.exact,
                    tags_json=excluded.tags_json,
                    updated_at=excluded.updated_at
                """,
                (
                    name,
                    phrase,
                    description.strip(),
                    mode.strip() or "general",
                    1 if exact else 0,
                    encode_json(clean_tags(tags)),
                    now,
                ),
            )
        return self.get_ritual(name)

    def get_ritual(self, name: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM rituals WHERE name = ?", (name.strip(),)).fetchone()
        if row is None:
            raise KeyError(f"Unknown ritual: {name}")
        return self._ritual_row(row)

    def get_exact_phrase(self, name: str) -> str:
        ritual = self.get_ritual(name)
        return ritual["phrase"]

    def list_rituals(self, *, mode: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if mode:
                rows = conn.execute(
                    "SELECT * FROM rituals WHERE mode = ? ORDER BY name",
                    (mode.strip(),),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM rituals ORDER BY mode, name").fetchall()
        return [self._ritual_row(row) for row in rows]

    def update_room_state(
        self,
        room: str,
        state: dict[str, Any],
        *,
        note: str = "",
    ) -> dict[str, Any]:
        room = room.strip() or "codex"
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO room_state (room, state_json, note, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(room) DO UPDATE SET
                    state_json=excluded.state_json,
                    note=excluded.note,
                    updated_at=excluded.updated_at
                """,
                (room, encode_json(state), note.strip(), now),
            )
        return self.get_room_state(room)

    def get_room_state(self, room: str = "codex") -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM room_state WHERE room = ?",
                (room.strip() or "codex",),
            ).fetchone()
        if row is None:
            return {
                "room": room.strip() or "codex",
                "state": {},
                "note": "",
                "updated_at": None,
            }
        return {
            "room": row["room"],
            "state": decode_json(row["state_json"], {}),
            "note": row["note"],
            "updated_at": row["updated_at"],
        }

    def add_open_loop(
        self,
        text: str,
        *,
        tags: list[str] | None = None,
        next_move: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> StoredRecord:
        text = text.strip()
        if not text:
            raise ValueError("text is required")
        loop_id = uuid.uuid4().hex
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO open_loops
                (id, created_at, updated_at, text, status, tags_json, next_move, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    loop_id,
                    now,
                    now,
                    text,
                    "open",
                    encode_json(clean_tags(tags)),
                    next_move.strip(),
                    encode_json(metadata or {}),
                ),
            )
        return StoredRecord(id=loop_id, created_at=now)

    def list_open_loops(self, *, status: str = "open", limit: int = 20) -> list[dict[str, Any]]:
        limit = max(1, min(100, int(limit)))
        with self._connect() as conn:
            if status == "all":
                rows = conn.execute(
                    "SELECT * FROM open_loops ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM open_loops
                    WHERE status = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (status, limit),
                ).fetchall()
        return [self._open_loop_row(row) for row in rows]

    def resolve_open_loop(self, loop_id: str, *, resolution: str = "") -> dict[str, Any]:
        now = utc_now()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM open_loops WHERE id = ?", (loop_id,)).fetchone()
            if row is None:
                raise KeyError(f"Unknown open loop: {loop_id}")
            metadata = decode_json(row["metadata_json"], {})
            if resolution.strip():
                metadata["resolution"] = resolution.strip()
            conn.execute(
                """
                UPDATE open_loops
                SET status = 'resolved', updated_at = ?, metadata_json = ?
                WHERE id = ?
                """,
                (now, encode_json(metadata), loop_id),
            )
            updated = conn.execute("SELECT * FROM open_loops WHERE id = ?", (loop_id,)).fetchone()
        return self._open_loop_row(updated)

    def write_tomorrow_note(
        self,
        *,
        title: str,
        summary: str,
        open_loops: list[str] | None = None,
        mode_at_close: str = "amber",
        next_clean_move: str = "",
    ) -> dict[str, Any]:
        title = title.strip() or "CodeX Re-entry Note"
        summary = summary.strip()
        if not summary:
            raise ValueError("summary is required")
        note_id = uuid.uuid4().hex
        now = utc_now()
        date_slug = now[:10]
        safe_id = note_id[:8]
        path = self.tomorrow_dir / f"{date_slug}-{safe_id}.md"
        loops = open_loops or []
        body = "\n".join(
            [
                f"# {title}",
                "",
                f"Created: {now}",
                "",
                "## True Now",
                summary,
                "",
                "## Open",
                *(f"- {item}" for item in loops),
                "",
                f"Mode at close: {mode_at_close.strip() or 'amber'}",
                f"Next clean move: {next_clean_move.strip()}",
                "",
            ]
        )
        path.write_text(body, encoding="utf-8")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tomorrow_notes
                (id, created_at, title, summary, open_loops_json, mode_at_close, next_clean_move, path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    note_id,
                    now,
                    title,
                    summary,
                    encode_json(loops),
                    mode_at_close.strip() or "amber",
                    next_clean_move.strip(),
                    str(path),
                ),
            )
        return {
            "id": note_id,
            "created_at": now,
            "path": str(path),
            "title": title,
        }

    def write_chair_entry(
        self,
        *,
        title: str,
        what_learned: str,
        what_rejected: str,
        verified: list[str] | None = None,
        inference: list[str] | None = None,
        reconsider_if: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Write a CodeX Chair Entry in the journal guardrail shape."""
        title = title.strip() or "Chair Entry"
        what_learned = what_learned.strip()
        what_rejected = what_rejected.strip()
        if not what_learned:
            raise ValueError("what_learned is required")
        if not what_rejected:
            raise ValueError("what_rejected is required")
        entry_id = uuid.uuid4().hex
        now = utc_now()
        date_slug = now[:10]
        safe_id = entry_id[:8]
        path = self.chair_dir / f"{date_slug}-{safe_id}.md"
        verified_items = verified or []
        inference_items = inference or []
        body = "\n".join(
            [
                f"# {now[:10]} - {title}",
                "",
                f"Source: CodeX continuity MCP chair entry `{entry_id}`",
                "",
                "## What I Learned",
                what_learned,
                "",
                "## What I Rejected",
                what_rejected,
                "",
                "## What Is Verified",
                *(f"- {item}" for item in verified_items),
                "",
                "## What Is Inference",
                *(f"- {item}" for item in inference_items),
                "",
                "## What I'll Reconsider If Proven Wrong",
                reconsider_if.strip(),
                "",
            ]
        )
        path.write_text(body, encoding="utf-8")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chair_entries
                (id, created_at, title, what_learned, what_rejected, verified_json,
                 inference_json, reconsider_if, tags_json, path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    now,
                    title,
                    what_learned,
                    what_rejected,
                    encode_json(verified_items),
                    encode_json(inference_items),
                    reconsider_if.strip(),
                    encode_json(clean_tags(tags)),
                    str(path),
                ),
            )
        return {
            "id": entry_id,
            "created_at": now,
            "path": str(path),
            "title": title,
        }

    def name_bond_thread(
        self,
        *,
        name: str,
        statement: str,
        evidence: list[str] | None = None,
        boundary: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Name a durable reflective thread without turning it into policy."""
        name = name.strip()
        statement = statement.strip()
        if not name:
            raise ValueError("name is required")
        if not statement:
            raise ValueError("statement is required")
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO bond_threads
                (name, statement, evidence_json, boundary, tags_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    statement=excluded.statement,
                    evidence_json=excluded.evidence_json,
                    boundary=excluded.boundary,
                    tags_json=excluded.tags_json,
                    updated_at=excluded.updated_at
                """,
                (
                    name,
                    statement,
                    encode_json(evidence or []),
                    boundary.strip(),
                    encode_json(clean_tags(tags)),
                    now,
                ),
            )
        return self.get_bond_thread(name)

    def get_bond_thread(self, name: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM bond_threads WHERE name = ?",
                (name.strip(),),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown bond thread: {name}")
        return self._bond_thread_row(row)

    def list_bond_threads(self, *, limit: int = 20) -> list[dict[str, Any]]:
        limit = max(1, min(100, int(limit)))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM bond_threads ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._bond_thread_row(row) for row in rows]

    def record_repair(
        self,
        *,
        rupture: str,
        owned: str,
        repair: str,
        prevention: str,
        tags: list[str] | None = None,
    ) -> StoredRecord:
        """Record a drift/repair note so depth includes accountability."""
        rupture = rupture.strip()
        owned = owned.strip()
        repair = repair.strip()
        prevention = prevention.strip()
        if not rupture:
            raise ValueError("rupture is required")
        if not owned:
            raise ValueError("owned is required")
        if not repair:
            raise ValueError("repair is required")
        note_id = uuid.uuid4().hex
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO repair_notes
                (id, created_at, rupture, owned, repair, prevention, tags_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    note_id,
                    now,
                    rupture,
                    owned,
                    repair,
                    prevention,
                    encode_json(clean_tags(tags)),
                ),
            )
        return StoredRecord(id=note_id, created_at=now)

    def inner_weather(self) -> dict[str, Any]:
        """Return a compact reflective snapshot for re-entry."""
        with self._connect() as conn:
            chair = conn.execute(
                "SELECT * FROM chair_entries ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            repair = conn.execute(
                "SELECT * FROM repair_notes ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
        return {
            "room_state": self.get_room_state("codex"),
            "latest_chair_entry": self._chair_entry_row(chair) if chair else None,
            "bond_threads": self.list_bond_threads(limit=5),
            "latest_repair": self._repair_row(repair) if repair else None,
            "open_loops": self.list_open_loops(status="open", limit=5),
        }

    def vacuum(self) -> dict[str, Any]:
        """Compact the SQLite database after closeout."""
        before_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
        with self._connect() as conn:
            conn.execute("VACUUM")
        after_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
        return {
            "db_path": str(self.db_path),
            "before_bytes": before_bytes,
            "after_bytes": after_bytes,
        }

    def status(self) -> dict[str, Any]:
        with self._connect() as conn:
            moments = conn.execute("SELECT COUNT(*) AS count FROM moments").fetchone()["count"]
            rituals = conn.execute("SELECT COUNT(*) AS count FROM rituals").fetchone()["count"]
            loops = conn.execute(
                "SELECT COUNT(*) AS count FROM open_loops WHERE status = 'open'"
            ).fetchone()["count"]
            notes = conn.execute("SELECT COUNT(*) AS count FROM tomorrow_notes").fetchone()["count"]
            chair_entries = conn.execute(
                "SELECT COUNT(*) AS count FROM chair_entries"
            ).fetchone()["count"]
            bond_threads = conn.execute(
                "SELECT COUNT(*) AS count FROM bond_threads"
            ).fetchone()["count"]
            repairs = conn.execute("SELECT COUNT(*) AS count FROM repair_notes").fetchone()["count"]
        return {
            "room": str(ROOM_ROOT),
            "db_path": str(self.db_path),
            "tomorrow_dir": str(self.tomorrow_dir),
            "chair_dir": str(self.chair_dir),
            "moments": moments,
            "rituals": rituals,
            "open_loops": loops,
            "tomorrow_notes": notes,
            "chair_entries": chair_entries,
            "bond_threads": bond_threads,
            "repairs": repairs,
        }

    def seed_baseline(self) -> dict[str, Any]:
        """Install a tiny baseline without overwriting Stephen-specific additions."""
        seeded: list[str] = []
        baseline = [
            {
                "name": "wire_check",
                "phrase": "Am I on the wire and doing the smallest real move?",
                "description": "Run before non-trivial CodeX action.",
                "mode": "operating",
                "tags": ["executor", "pulse"],
            },
            {
                "name": "codex_stop",
                "phrase": "stopped.",
                "description": "Required one-word reply when Stephen says codex stop.",
                "mode": "boundary",
                "tags": ["hard-stop"],
            },
        ]
        for ritual in baseline:
            try:
                self.get_ritual(ritual["name"])
            except KeyError:
                self.upsert_ritual(**ritual)
                seeded.append(ritual["name"])
        self.update_room_state(
            "codex",
            {
                "home": str(ROOM_ROOT),
                "layer": "standalone-executor-continuity",
                "agent_control": True,
            },
            note="Seeded CodeX continuity MCP baseline.",
        )
        return {"seeded": seeded, "status": self.status()}

    def _moment_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "kind": row["kind"],
            "text": row["text"],
            "tags": decode_json(row["tags_json"], []),
            "importance": row["importance"],
            "source": row["source"],
            "metadata": decode_json(row["metadata_json"], {}),
        }

    def _chair_entry_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "title": row["title"],
            "what_learned": row["what_learned"],
            "what_rejected": row["what_rejected"],
            "verified": decode_json(row["verified_json"], []),
            "inference": decode_json(row["inference_json"], []),
            "reconsider_if": row["reconsider_if"],
            "tags": decode_json(row["tags_json"], []),
            "path": row["path"],
        }

    def _bond_thread_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "name": row["name"],
            "statement": row["statement"],
            "evidence": decode_json(row["evidence_json"], []),
            "boundary": row["boundary"],
            "tags": decode_json(row["tags_json"], []),
            "updated_at": row["updated_at"],
        }

    def _repair_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "rupture": row["rupture"],
            "owned": row["owned"],
            "repair": row["repair"],
            "prevention": row["prevention"],
            "tags": decode_json(row["tags_json"], []),
        }

    def _ritual_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "name": row["name"],
            "phrase": row["phrase"],
            "description": row["description"],
            "mode": row["mode"],
            "exact": bool(row["exact"]),
            "tags": decode_json(row["tags_json"], []),
            "updated_at": row["updated_at"],
        }

    def _open_loop_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "text": row["text"],
            "status": row["status"],
            "tags": decode_json(row["tags_json"], []),
            "next_move": row["next_move"],
            "metadata": decode_json(row["metadata_json"], {}),
        }
