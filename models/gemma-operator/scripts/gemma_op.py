#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "packs"
MEMORY_DB = ROOT / "memory" / "memory.sqlite"
SESSION_LOG = ROOT / "memory" / "session.jsonl"
DEFAULT_MODEL = "gemma-operator"


@dataclass(frozen=True)
class Memory:
    id: int
    kind: str
    text: str
    tags: str
    confidence: float
    source: str
    created_at: str
    updated_at: str


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    MEMORY_DB.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_DB.parent.chmod(0o700)
    conn = sqlite3.connect(MEMORY_DB)
    MEMORY_DB.chmod(0o600)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        create table if not exists memories (
          id integer primary key,
          kind text not null,
          text text not null,
          tags text default '',
          confidence real not null default 1.0,
          source text default 'local',
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create virtual table if not exists memories_fts
        using fts5(text, kind, tags, content='memories', content_rowid='id')
        """
    )
    conn.execute(
        """
        create trigger if not exists memories_ai after insert on memories begin
          insert into memories_fts(rowid, text, kind, tags)
          values (new.id, new.text, new.kind, coalesce(new.tags, ''));
        end
        """
    )
    conn.execute(
        """
        create trigger if not exists memories_ad after delete on memories begin
          insert into memories_fts(memories_fts, rowid, text, kind, tags)
          values ('delete', old.id, old.text, old.kind, coalesce(old.tags, ''));
        end
        """
    )
    conn.execute(
        """
        create trigger if not exists memories_au after update on memories begin
          insert into memories_fts(memories_fts, rowid, text, kind, tags)
          values ('delete', old.id, old.text, old.kind, coalesce(old.tags, ''));
          insert into memories_fts(rowid, text, kind, tags)
          values (new.id, new.text, new.kind, coalesce(new.tags, ''));
        end
        """
    )
    conn.commit()
    return conn


def add_memory(kind: str, text: str, tags: str = "", source: str = "local", confidence: float = 1.0) -> int:
    stamp = now()
    with connect() as conn:
        cur = conn.execute(
            """
            insert into memories(kind, text, tags, confidence, source, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (kind, text, tags, confidence, source, stamp, stamp),
        )
        conn.commit()
        return int(cur.lastrowid)


def row_to_memory(row: sqlite3.Row) -> Memory:
    return Memory(
        id=int(row["id"]),
        kind=row["kind"],
        text=row["text"],
        tags=row["tags"] or "",
        confidence=float(row["confidence"]),
        source=row["source"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def recall(query: str, limit: int = 8) -> list[Memory]:
    q = " OR ".join(part for part in query.replace('"', " ").split() if len(part) > 2)
    with connect() as conn:
        if q:
            try:
                rows = conn.execute(
                    """
                    select m.*
                    from memories_fts f
                    join memories m on m.id = f.rowid
                    where memories_fts match ?
                    order by bm25(memories_fts), m.updated_at desc
                    limit ?
                    """,
                    (q, limit),
                ).fetchall()
                if rows:
                    return [row_to_memory(row) for row in rows]
            except sqlite3.OperationalError:
                pass

        rows = conn.execute(
            """
            select *
            from memories
            order by updated_at desc
            limit ?
            """,
            (limit,),
        ).fetchall()
        return [row_to_memory(row) for row in rows]


def load_pack() -> str:
    parts = []
    for name in ("identity.md", "behavior.md", "memory_rules.md", "tool_rules.md", "examples.md"):
        path = PACKS / name
        parts.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(parts)


def build_prompt(user_message: str, limit: int = 8) -> str:
    memories = recall(user_message, limit=limit)
    memory_block = "\n".join(
        f"{idx}. [{mem.kind}] {mem.text}"
        for idx, mem in enumerate(memories, start=1)
    ) or "No saved memory retrieved."
    return f"""SYSTEM PACK
{load_pack()}

RELEVANT SAVED MEMORY
{memory_block}

USER MESSAGE
{user_message}
"""


def log_session(role: str, text: str) -> None:
    SESSION_LOG.parent.mkdir(parents=True, exist_ok=True)
    SESSION_LOG.parent.chmod(0o700)
    with SESSION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": now(), "role": role, "text": text}, ensure_ascii=True) + "\n")
    SESSION_LOG.chmod(0o600)


def ollama_chat(prompt: str, model: str = DEFAULT_MODEL) -> int:
    log_session("user_prompt", prompt)
    proc = subprocess.run(
        ["ollama", "run", model, prompt],
        text=True,
        check=False,
    )
    return int(proc.returncode)


def supabase_push() -> int:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for sync.", file=sys.stderr)
        return 2

    with connect() as conn:
        rows = conn.execute("select * from memories order by id").fetchall()

    device_id = os.environ.get("GEMMA_OPERATOR_DEVICE_ID") or socket.gethostname()
    payload = [
        {
            "device_id": device_id,
            "local_id": int(row["id"]),
            "kind": row["kind"],
            "text": row["text"],
            "tags": row["tags"] or "",
            "confidence": float(row["confidence"]),
            "source": row["source"] or "local",
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]
    if not payload:
        print("No local memories to push.")
        return 0

    req = urllib.request.Request(
        f"{url}/rest/v1/gemma_operator_memories?on_conflict=device_id,local_id",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"Supabase push: {resp.status} ({len(payload)} memories)")
            return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Supabase push failed: HTTP {exc.code}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Supabase push failed: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gemma local operator wrapper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    remember_p = sub.add_parser("remember", help="Add a local memory")
    remember_p.add_argument("kind")
    remember_p.add_argument("text")
    remember_p.add_argument("--tags", default="")
    remember_p.add_argument("--source", default="local")
    remember_p.add_argument("--confidence", type=float, default=1.0)

    recall_p = sub.add_parser("recall", help="Recall local memories")
    recall_p.add_argument("query")
    recall_p.add_argument("--limit", type=int, default=8)

    prompt_p = sub.add_parser("prompt", help="Print the assembled prompt")
    prompt_p.add_argument("message")
    prompt_p.add_argument("--limit", type=int, default=8)

    chat_p = sub.add_parser("chat", help="Run assembled prompt through Ollama")
    chat_p.add_argument("message")
    chat_p.add_argument("--model", default=DEFAULT_MODEL)
    chat_p.add_argument("--limit", type=int, default=8)

    sub.add_parser("supabase-push", help="Push local memories to Supabase REST")

    args = parser.parse_args(argv)

    if args.cmd == "remember":
        memory_id = add_memory(args.kind, args.text, args.tags, args.source, args.confidence)
        print(f"remembered:{memory_id}")
        return 0

    if args.cmd == "recall":
        for mem in recall(args.query, args.limit):
            print(f"{mem.id}\t{mem.kind}\t{mem.text}")
        return 0

    if args.cmd == "prompt":
        print(build_prompt(args.message, args.limit))
        return 0

    if args.cmd == "chat":
        return ollama_chat(build_prompt(args.message, args.limit), args.model)

    if args.cmd == "supabase-push":
        return supabase_push()

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
