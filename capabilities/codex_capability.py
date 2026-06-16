#!/usr/bin/env python3
"""Capability registry for CodeX-native lanes."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path('/Users/stephengodman/CodeX/capabilities/capabilities.sqlite3')


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def encode_tags(tags: str | None) -> str:
    return json.dumps(sorted({x.strip().lower() for x in (tags or '').split(',') if x.strip()}))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    return con


def init_db() -> None:
    with connect() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor TEXT NOT NULL,
                capability TEXT NOT NULL,
                command TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'verified',
                confidence TEXT NOT NULL DEFAULT 'verified',
                when_to_use TEXT NOT NULL,
                when_not_to_use TEXT NOT NULL DEFAULT '',
                eval_case TEXT NOT NULL DEFAULT '',
                failure_keys TEXT NOT NULL DEFAULT '',
                tags_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(actor, capability)
            );

            DROP TABLE IF EXISTS capabilities_fts;
            CREATE VIRTUAL TABLE capabilities_fts USING fts5(actor, capability, command, when_to_use, when_not_to_use, tags);
            """
        )
        rows = con.execute('SELECT * FROM capabilities').fetchall()
        for row in rows:
            con.execute(
                'INSERT INTO capabilities_fts (actor, capability, command, when_to_use, when_not_to_use, tags) VALUES (?, ?, ?, ?, ?, ?)',
                (row['actor'], row['capability'], row['command'], row['when_to_use'], row['when_not_to_use'], ' '.join(json.loads(row['tags_json']))),
            )


def upsert(**item: str) -> None:
    init_db()
    stamp = now()
    tags = encode_tags(item.get('tags', ''))
    with connect() as con:
        con.execute(
            """
            INSERT INTO capabilities (actor, capability, command, status, confidence, when_to_use, when_not_to_use, eval_case, failure_keys, tags_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(actor, capability) DO UPDATE SET
                command=excluded.command,
                status=excluded.status,
                confidence=excluded.confidence,
                when_to_use=excluded.when_to_use,
                when_not_to_use=excluded.when_not_to_use,
                eval_case=excluded.eval_case,
                failure_keys=excluded.failure_keys,
                tags_json=excluded.tags_json,
                updated_at=excluded.updated_at
            """,
            (
                item['actor'], item['capability'], item.get('command', ''), item.get('status', 'verified'),
                item.get('confidence', 'verified'), item['when_to_use'], item.get('when_not_to_use', ''),
                item.get('eval_case', ''), item.get('failure_keys', ''), tags, stamp, stamp,
            ),
        )
        con.execute('DELETE FROM capabilities_fts WHERE actor = ? AND capability = ?', (item['actor'], item['capability']))
        con.execute(
            'INSERT INTO capabilities_fts (actor, capability, command, when_to_use, when_not_to_use, tags) VALUES (?, ?, ?, ?, ?, ?)',
            (item['actor'], item['capability'], item.get('command', ''), item['when_to_use'], item.get('when_not_to_use', ''), ' '.join(json.loads(tags))),
        )


def row_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data['tags'] = json.loads(data.pop('tags_json'))
    return data


def seed() -> None:
    items = [
        {
            'actor': 'CodeX', 'capability': 'main execution', 'command': '', 'eval_case': 'identity',
            'when_to_use': 'Use CodeX for repo changes, shell wiring, tool creation, smoke tests, evals, and concrete implementation.',
            'when_not_to_use': 'Do not use CodeX as NotebookLM source authority or as a substitute for live verification.',
            'tags': 'codex,executor,repo,tools',
        },
        {
            'actor': 'CodeX', 'capability': 'memory recall', 'command': '/Users/stephengodman/CodeX/bin/codex-room recall QUERY', 'eval_case': 'memory',
            'when_to_use': 'Use to recall standing executor preferences, identity boundaries, and compact handoff facts.',
            'when_not_to_use': 'Do not treat memory as newer than live files or current tool output.',
            'tags': 'codex,memory,sqlite',
        },
        {
            'actor': 'CodeX', 'capability': 'failure memory', 'command': '/Users/stephengodman/CodeX/bin/codex-failure search QUERY', 'eval_case': 'failure-memory',
            'when_to_use': 'Use before repeating a lane where something broke: Gemini contamination, wake scripts, wrapper smoke failures, eval false failures.',
            'when_not_to_use': 'Do not store blame, secrets, or giant raw logs.',
            'tags': 'codex,failures,sqlite,prevention',
        },
        {
            'actor': 'NotebookLM/Jacker', 'capability': 'source-grounded audit', 'command': 'notebooklm source add/wait/ask via nblm skill',
            'when_to_use': 'Use for hostile source-pack review, contradiction checks, and citation-grounded gate calls.',
            'when_not_to_use': 'Do not treat NotebookLM as final approval over local code reality.',
            'tags': 'notebooklm,jacker,audit,source-grounding',
        },
        {
            'actor': 'CodeX', 'capability': 'context handling', 'command': 'rg, jq, python/json.tool, and focused file reads as appropriate', 'eval_case': 'router',
            'when_to_use': 'Use before feeding large local, Workspace, API, JSON, or NDJSON payloads into a model.',
            'when_not_to_use': 'Do not compress tiny outputs where direct reading is clearer.',
            'tags': 'codex,json,compression,context',
        },
        {
            'actor': 'CodeX', 'capability': 'browser/workspace execution', 'command': 'Browser, Playwright, Google Drive/Gmail connectors, or local CLI as the task requires',
            'when_to_use': 'Use for browser work, Workspace files, Gmail/Drive/Docs/Sheets tasks, and UI smoke verification.',
            'when_not_to_use': 'Do not widen into external state when a local read or small smoke test answers the task.',
            'tags': 'codex,browser,drive,workspace,playwright',
        },
        {
            'actor': 'CodeX', 'capability': 'venice model lane', 'command': '/Users/stephengodman/CodeX/bin/codex-venice smoke',
            'when_to_use': 'Use the CodeX Venice helper for Venice-side model checks and receipts.',
            'when_not_to_use': 'Do not write raw Venice keys into prompts, docs, notes, or repo files.',
            'tags': 'codex,venice,model,sidecar',
        },
    ]
    for item in items:
        upsert(**item)
    print(f'seeded {len(items)} capability item(s)')


def cmd_init(_: argparse.Namespace) -> None:
    init_db()
    print(DB_PATH)


def cmd_seed(_: argparse.Namespace) -> None:
    seed()


def cmd_status(_: argparse.Namespace) -> None:
    init_db()
    with connect() as con:
        total = con.execute('SELECT COUNT(*) AS count FROM capabilities').fetchone()['count']
        by_actor = [dict(row) for row in con.execute('SELECT actor, COUNT(*) AS count FROM capabilities GROUP BY actor ORDER BY actor').fetchall()]
    print(json.dumps({'db': str(DB_PATH), 'capabilities': total, 'by_actor': by_actor}, indent=2))


def cmd_list(args: argparse.Namespace) -> None:
    init_db()
    with connect() as con:
        if args.actor:
            rows = con.execute('SELECT * FROM capabilities WHERE actor = ? ORDER BY capability', (args.actor,)).fetchall()
        else:
            rows = con.execute('SELECT * FROM capabilities ORDER BY actor, capability').fetchall()
    print(json.dumps([row_dict(row) for row in rows], indent=2))


def cmd_search(args: argparse.Namespace) -> None:
    init_db()
    with connect() as con:
        try:
            rows = con.execute(
                """
                SELECT c.*
                FROM capabilities_fts x
                JOIN capabilities c ON c.actor = x.actor AND c.capability = x.capability
                WHERE capabilities_fts MATCH ?
                ORDER BY bm25(capabilities_fts)
                LIMIT ?
                """,
                (args.query, args.limit),
            ).fetchall()
        except sqlite3.OperationalError:
            like = f'%{args.query}%'
            rows = con.execute(
                'SELECT * FROM capabilities WHERE actor LIKE ? OR capability LIKE ? OR when_to_use LIKE ? OR tags_json LIKE ? LIMIT ?',
                (like, like, like, like, args.limit),
            ).fetchall()
    print(json.dumps([row_dict(row) for row in rows], indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='CodeX capability registry')
    sub = parser.add_subparsers(required=True)
    p = sub.add_parser('init'); p.set_defaults(func=cmd_init)
    p = sub.add_parser('seed'); p.set_defaults(func=cmd_seed)
    p = sub.add_parser('status'); p.set_defaults(func=cmd_status)
    p = sub.add_parser('list'); p.add_argument('--actor'); p.set_defaults(func=cmd_list)
    p = sub.add_parser('search'); p.add_argument('query'); p.add_argument('--limit', type=int, default=10); p.set_defaults(func=cmd_search)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
