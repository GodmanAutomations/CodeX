#!/usr/bin/env python3
"""Failure memory helper for CodeX."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path('/Users/stephengodman/CodeX/failures/codex-failures.sqlite3')


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def tags_json(tags: str | None) -> str:
    values = [item.strip().lower() for item in (tags or '').split(',') if item.strip()]
    return json.dumps(sorted(set(values)))


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
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                lane TEXT NOT NULL,
                severity TEXT NOT NULL,
                symptom TEXT NOT NULL,
                cause TEXT NOT NULL,
                fix TEXT NOT NULL,
                prevention TEXT NOT NULL,
                tags_json TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            DROP TABLE IF EXISTS failures_fts;
            CREATE VIRTUAL TABLE failures_fts USING fts5(key, lane, symptom, cause, fix, prevention, tags);
            """
        )
        rows = con.execute('SELECT * FROM failures').fetchall()
        for row in rows:
            con.execute(
                'INSERT INTO failures_fts (key, lane, symptom, cause, fix, prevention, tags) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (row['key'], row['lane'], row['symptom'], row['cause'], row['fix'], row['prevention'], ' '.join(json.loads(row['tags_json']))),
            )


def upsert_failure(
    *,
    key: str,
    lane: str,
    severity: str,
    symptom: str,
    cause: str,
    fix: str,
    prevention: str,
    tags: str = '',
    source: str = 'manual',
) -> None:
    init_db()
    stamp = now()
    tag_data = tags_json(tags)
    with connect() as con:
        con.execute(
            """
            INSERT INTO failures (key, lane, severity, symptom, cause, fix, prevention, tags_json, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                lane=excluded.lane,
                severity=excluded.severity,
                symptom=excluded.symptom,
                cause=excluded.cause,
                fix=excluded.fix,
                prevention=excluded.prevention,
                tags_json=excluded.tags_json,
                source=excluded.source,
                updated_at=excluded.updated_at
            """,
            (key, lane, severity, symptom, cause, fix, prevention, tag_data, source, stamp, stamp),
        )
        con.execute('DELETE FROM failures_fts WHERE key = ?', (key,))
        con.execute(
            'INSERT INTO failures_fts (key, lane, symptom, cause, fix, prevention, tags) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (key, lane, symptom, cause, fix, prevention, ' '.join(json.loads(tag_data))),
        )


def row_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data['tags'] = json.loads(data.pop('tags_json'))
    return data


def seed() -> None:
    seeds = [
        {
            'key': 'codex-memory-fts-empty-search',
            'lane': 'codex-memory',
            'severity': 'low',
            'symptom': 'CodeX memory search smoke returned empty for seeded smoke-test preference.',
            'cause': 'FTS table was created contentless and not indexed in a searchable way.',
            'fix': 'Rebuilt FTS as a normal fts5 table and reindexed existing memory rows during init.',
            'prevention': 'Every new SQLite memory/search helper must smoke test status, seed, and search.',
            'tags': 'codex,sqlite,fts,memory',
        },
        {
            'key': 'eval-false-failures',
            'lane': 'codex-evals',
            'severity': 'low',
            'symptom': 'Initial eval suite failed on wording/count expectations while underlying systems were healthy.',
            'cause': 'Eval checks were too string-literal and expected exact phrasing or literal count values.',
            'fix': 'Adjusted evals to measure behavior: required tool routes, pulse_rows greater than zero, and current Gemini prompt wording.',
            'prevention': 'Evals should check behavior and invariants, not brittle prose unless the prose is the actual contract.',
            'tags': 'codex,evals,false-failure',
        },
    ]
    for item in seeds:
        upsert_failure(source='seed', **item)
    print(f'seeded {len(seeds)} failure item(s)')


def cmd_init(_: argparse.Namespace) -> None:
    init_db()
    print(DB_PATH)


def cmd_seed(_: argparse.Namespace) -> None:
    seed()


def cmd_status(_: argparse.Namespace) -> None:
    init_db()
    with connect() as con:
        count = con.execute('SELECT COUNT(*) AS count FROM failures').fetchone()['count']
        by_lane = [dict(row) for row in con.execute('SELECT lane, COUNT(*) AS count FROM failures GROUP BY lane ORDER BY lane').fetchall()]
    print(json.dumps({'db': str(DB_PATH), 'failures': count, 'by_lane': by_lane}, indent=2))


def cmd_add(args: argparse.Namespace) -> None:
    upsert_failure(
        key=args.key,
        lane=args.lane,
        severity=args.severity,
        symptom=args.symptom,
        cause=args.cause,
        fix=args.fix,
        prevention=args.prevention,
        tags=args.tags,
        source=args.source,
    )
    print(f'upserted {args.key}')


def cmd_list(args: argparse.Namespace) -> None:
    init_db()
    with connect() as con:
        if args.lane:
            rows = con.execute('SELECT * FROM failures WHERE lane = ? ORDER BY severity DESC, key', (args.lane,)).fetchall()
        else:
            rows = con.execute('SELECT * FROM failures ORDER BY lane, key').fetchall()
    print(json.dumps([row_dict(row) for row in rows], indent=2))


def cmd_search(args: argparse.Namespace) -> None:
    init_db()
    with connect() as con:
        try:
            rows = con.execute(
                """
                SELECT f.*
                FROM failures_fts x
                JOIN failures f ON f.key = x.key
                WHERE failures_fts MATCH ?
                ORDER BY bm25(failures_fts)
                LIMIT ?
                """,
                (args.query, args.limit),
            ).fetchall()
        except sqlite3.OperationalError:
            like = f'%{args.query}%'
            rows = con.execute(
                'SELECT * FROM failures WHERE key LIKE ? OR symptom LIKE ? OR cause LIKE ? OR fix LIKE ? OR prevention LIKE ? LIMIT ?',
                (like, like, like, like, like, args.limit),
            ).fetchall()
    print(json.dumps([row_dict(row) for row in rows], indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='CodeX failure memory helper')
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser('init')
    p.set_defaults(func=cmd_init)

    p = sub.add_parser('seed')
    p.set_defaults(func=cmd_seed)

    p = sub.add_parser('status')
    p.set_defaults(func=cmd_status)

    p = sub.add_parser('add')
    p.add_argument('--key', required=True)
    p.add_argument('--lane', default='general')
    p.add_argument('--severity', default='medium')
    p.add_argument('--symptom', required=True)
    p.add_argument('--cause', required=True)
    p.add_argument('--fix', required=True)
    p.add_argument('--prevention', required=True)
    p.add_argument('--tags', default='')
    p.add_argument('--source', default='manual')
    p.set_defaults(func=cmd_add)

    p = sub.add_parser('list')
    p.add_argument('--lane')
    p.set_defaults(func=cmd_list)

    p = sub.add_parser('search')
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=10)
    p.set_defaults(func=cmd_search)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
