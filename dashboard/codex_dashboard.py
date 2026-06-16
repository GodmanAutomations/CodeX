#!/usr/bin/env python3
"""Generate a static CodeX dashboard."""

from __future__ import annotations

import argparse
import html
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CODEX = Path('/Users/stephengodman/Candice-Code')
OUT = CODEX / 'dashboard' / 'index.html'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def sqlite_count(path: Path, table: str, where: str = '') -> int | None:
    try:
        con = sqlite3.connect(path)
        cur = con.cursor()
        sql = f'SELECT COUNT(*) FROM {table}' + (f' WHERE {where}' if where else '')
        value = cur.execute(sql).fetchone()[0]
        con.close()
        return int(value)
    except Exception:
        return None


def eval_summary() -> list[dict[str, Any]]:
    db = CODEX / 'evals' / 'codex-evals.sqlite3'
    if not db.exists():
        return []
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT e.case_id, e.ok, e.finished_at
        FROM eval_runs e
        JOIN (SELECT case_id, MAX(id) AS id FROM eval_runs GROUP BY case_id) latest ON latest.id = e.id
        ORDER BY e.case_id
        """
    ).fetchall()
    con.close()
    return [dict(row) for row in rows]


def build_html() -> str:
    codex_hb = read_json(CODEX / 'HEARTBEAT.json')

    memory_count = sqlite_count(CODEX / 'memory' / 'codex-memory.sqlite3', 'memory_items')
    failure_count = sqlite_count(CODEX / 'failures' / 'codex-failures.sqlite3', 'failures')
    capability_count = sqlite_count(CODEX / 'capabilities' / 'capabilities.sqlite3', 'capabilities')
    evals = eval_summary()
    pass_count = sum(1 for row in evals if row.get('ok'))

    cards = [
        ('CodeX heartbeat', codex_hb.get('last_beat_utc', 'missing')),
        ('CodeX memory items', memory_count),
        ('Failure memories', failure_count),
        ('Capabilities', capability_count),
        ('Eval latest pass', f'{pass_count}/{len(evals)}'),
    ]
    card_html = ''.join(f'<section class="card"><h2>{html.escape(str(k))}</h2><p>{html.escape(str(v))}</p></section>' for k, v in cards)
    eval_rows = ''.join(
        f"<tr><td>{html.escape(row['case_id'])}</td><td class={'pass' if row['ok'] else 'fail'}>{'PASS' if row['ok'] else 'FAIL'}</td><td>{html.escape(row['finished_at'])}</td></tr>"
        for row in evals
    )
    return f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>CodeX Dashboard</title>
<style>
:root {{ --bg:#10130f; --panel:#f2ecd8; --ink:#1e2119; --muted:#6f735d; --good:#2f7d4f; --bad:#a33a2f; --line:#d9cfac; }}
body {{ margin:0; font-family: Georgia, 'Times New Roman', serif; background: radial-gradient(circle at 20% 0%, #2d3426, var(--bg) 46%); color: var(--panel); }}
main {{ max-width: 1100px; margin: 0 auto; padding: 42px 24px; }}
h1 {{ font-size: 46px; margin: 0 0 8px; letter-spacing: -0.04em; }}
.sub {{ color:#d7cfb3; margin-bottom: 28px; }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:16px; }}
.card {{ background: var(--panel); color: var(--ink); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow: 0 18px 40px rgba(0,0,0,.24); }}
.card h2 {{ font-size:15px; color:var(--muted); margin:0 0 10px; text-transform:uppercase; letter-spacing:.08em; }}
.card p {{ font-size:20px; margin:0; overflow-wrap:anywhere; }}
table {{ width:100%; border-collapse: collapse; margin-top:28px; background:rgba(242,236,216,.96); color:var(--ink); border-radius:18px; overflow:hidden; }}
th, td {{ padding:12px 14px; border-bottom:1px solid var(--line); text-align:left; }}
th {{ color:var(--muted); text-transform:uppercase; font-size:12px; letter-spacing:.08em; }}
.pass {{ color:var(--good); font-weight:bold; }} .fail {{ color:var(--bad); font-weight:bold; }}
.footer {{ color:#c7bea1; margin-top:22px; font-size:13px; }}
</style>
</head>
<body><main>
<h1>CodeX Dashboard</h1>
<div class="sub">Executor lane status generated {html.escape(utc_now())}</div>
<div class="grid">{card_html}</div>
<table><thead><tr><th>Eval</th><th>Status</th><th>Finished</th></tr></thead><tbody>{eval_rows}</tbody></table>
<div class="footer">Local-only dashboard. Receipts beat vibes.</div>
</main></body></html>'''


def cmd_build(_: argparse.Namespace) -> None:
    OUT.write_text(build_html(), encoding='utf-8')
    print(OUT)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Build CodeX dashboard')
    sub = parser.add_subparsers(required=True)
    p = sub.add_parser('build')
    p.set_defaults(func=cmd_build)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
