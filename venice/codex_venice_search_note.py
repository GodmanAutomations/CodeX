#!/usr/bin/env python3
"""Run Venice search and save a markdown note."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import codex_venice

OUT_DIR = Path('/Users/stephengodman/Candice-Code/research/venice-search')


def slugify(text: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:72] or 'search'


def clean(text: str) -> str:
    text = html.unescape(text or '')
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description='Save a Venice search as markdown.')
    parser.add_argument('query')
    parser.add_argument('--limit', type=int, default=8)
    parser.add_argument('--provider', choices=['brave', 'google'], default='brave')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()

    payload = codex_venice.search(args.query, args.limit, args.provider)
    if not payload.get('ok'):
        print(payload)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = args.out or OUT_DIR / f'{stamp}-{slugify(args.query)}.md'
    lines = [
        f'# Venice Search: {args.query}',
        '',
        f'Created: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}',
        f'Provider: {args.provider}',
        '',
        '## Results',
        '',
    ]
    for i, item in enumerate(payload.get('results', []), 1):
        title = clean(item.get('title', 'untitled'))
        url = item.get('url', '')
        date = clean(item.get('date', ''))
        content = clean(item.get('content', ''))[:900]
        lines.extend([
            f'### {i}. {title}',
            '',
            f'- URL: {url}',
            f'- Date: {date or "not provided"}',
            '',
            content,
            '',
        ])
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
