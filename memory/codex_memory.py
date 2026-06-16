#!/usr/bin/env python3
"""Small SQLite memory helper for CodeX."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path('/Users/stephengodman/Candice-Code/memory/codex-memory.sqlite3')


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def tags_to_json(tags: str | list[str] | None) -> str:
    if tags is None:
        values: list[str] = []
    elif isinstance(tags, str):
        values = [item.strip().lower() for item in tags.split(',') if item.strip()]
    else:
        values = [item.strip().lower() for item in tags if item.strip()]
    return json.dumps(sorted(set(values)))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                tags_json TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL DEFAULT 'manual',
                confidence TEXT NOT NULL DEFAULT 'verified',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            DROP TABLE IF EXISTS memory_items_fts;

            CREATE VIRTUAL TABLE memory_items_fts
            USING fts5(key, value, tags);

            CREATE TABLE IF NOT EXISTS open_loops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                next_move TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'open',
                tags_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS handoff_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        rows = conn.execute('SELECT key, value, tags_json FROM memory_items').fetchall()
        for row in rows:
            conn.execute(
                'INSERT INTO memory_items_fts (key, value, tags) VALUES (?, ?, ?)',
                (row['key'], row['value'], ' '.join(json.loads(row['tags_json']))),
            )


def upsert_item(kind: str, key: str, value: str, tags: str = '', source: str = 'manual', confidence: str = 'verified') -> None:
    now = utc_now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO memory_items (kind, key, value, tags_json, source, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                kind=excluded.kind,
                value=excluded.value,
                tags_json=excluded.tags_json,
                source=excluded.source,
                confidence=excluded.confidence,
                updated_at=excluded.updated_at
            """,
            (kind, key, value, tags_to_json(tags), source, confidence, now, now),
        )
        conn.execute('DELETE FROM memory_items_fts WHERE key = ?', (key,))
        conn.execute(
            'INSERT INTO memory_items_fts (key, value, tags) VALUES (?, ?, ?)',
            (key, value, ' '.join(json.loads(tags_to_json(tags)))),
        )


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    if 'tags_json' in data:
        data['tags'] = json.loads(data.pop('tags_json'))
    return data


def cmd_init(_: argparse.Namespace) -> None:
    init_db()
    print(DB_PATH)


def cmd_seed(_: argparse.Namespace) -> None:
    init_db()
    seeds = [
        ('identity', 'codex-role', 'Codex is Stephen Godman\'s main executor.', 'codex,identity,executor'),
        ('preference', 'smoke-tests-default', 'After code or tooling changes, run the smallest meaningful smoke test by default.', 'testing,tools,preference'),
        ('preference', 'no-review-loop-clean-tree', 'Do not run current-diff review when there are no current changes.', 'review,git,preference'),
        ('boundary', 'identity-separation', 'Codex does not inherit Rook, Anchor, Gemini, Ace, Jacker, NotebookLM, or room identity.', 'identity,boundary'),
        ('tool-route', 'codex-context-handling', 'Use CodeX-native search, structured parsing, focused reads, and smoke tests before feeding large output back into the model.', 'codex,context,tools'),
        ('tool-route', 'notebooklm-jacker', 'Use NotebookLM/Jacker for source-grounded audit pressure, not as final authority over local code reality.', 'notebooklm,jacker,audit'),
    ]
    for kind, key, value, tags in seeds:
        upsert_item(kind, key, value, tags, source='seed')
    print(f'seeded {len(seeds)} memory item(s)')


def cmd_status(_: argparse.Namespace) -> None:
    init_db()
    with connect() as conn:
        items = conn.execute('SELECT COUNT(*) AS count FROM memory_items').fetchone()['count']
        loops = conn.execute("SELECT COUNT(*) AS count FROM open_loops WHERE status = 'open'").fetchone()['count']
        handoffs = conn.execute('SELECT COUNT(*) AS count FROM handoff_summaries').fetchone()['count']
    print(json.dumps({'db': str(DB_PATH), 'memory_items': items, 'open_loops': loops, 'handoff_summaries': handoffs}, indent=2))


def cmd_add(args: argparse.Namespace) -> None:
    init_db()
    upsert_item(args.kind, args.key, args.value, args.tags, args.source, args.confidence)
    print(f'upserted {args.key}')


def cmd_list(args: argparse.Namespace) -> None:
    init_db()
    with connect() as conn:
        if args.kind:
            rows = conn.execute('SELECT * FROM memory_items WHERE kind = ? ORDER BY key', (args.kind,)).fetchall()
        else:
            rows = conn.execute('SELECT * FROM memory_items ORDER BY kind, key').fetchall()
    print(json.dumps([row_to_dict(row) for row in rows], indent=2))


def cmd_search(args: argparse.Namespace) -> None:
    init_db()
    query = args.query.strip()
    with connect() as conn:
        try:
            rows = conn.execute(
                """
                SELECT m.*
                FROM memory_items_fts f
                JOIN memory_items m ON m.key = f.key
                WHERE memory_items_fts MATCH ?
                ORDER BY bm25(memory_items_fts)
                LIMIT ?
                """,
                (query, args.limit),
            ).fetchall()
        except sqlite3.OperationalError:
            like = f'%{query}%'
            rows = conn.execute(
                'SELECT * FROM memory_items WHERE key LIKE ? OR value LIKE ? ORDER BY kind, key LIMIT ?',
                (like, like, args.limit),
            ).fetchall()
    print(json.dumps([row_to_dict(row) for row in rows], indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='CodeX SQLite memory helper')
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser('init')
    p.set_defaults(func=cmd_init)

    p = sub.add_parser('seed')
    p.set_defaults(func=cmd_seed)

    p = sub.add_parser('status')
    p.set_defaults(func=cmd_status)

    p = sub.add_parser('add')
    p.add_argument('--kind', required=True)
    p.add_argument('--key', required=True)
    p.add_argument('--value', required=True)
    p.add_argument('--tags', default='')
    p.add_argument('--source', default='manual')
    p.add_argument('--confidence', default='verified')
    p.set_defaults(func=cmd_add)

    p = sub.add_parser('list')
    p.add_argument('--kind')
    p.set_defaults(func=cmd_list)

    p = sub.add_parser('search')
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=10)
    p.set_defaults(func=cmd_search)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
