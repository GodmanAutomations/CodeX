#!/usr/bin/env python3
"""Detect drift in CodeX's all-time Coding Anchor posture."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


CODEX = Path('/Users/stephengodman/CodeX')
GLOBAL_AGENTS = Path('/Users/stephengodman/.codex/AGENTS.md')
MEMORY = CODEX / 'memory' / 'codex_memory.py'


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def file_contains(name: str, path: Path, snippets: list[str]) -> Check:
    if not path.exists():
        return Check(name, False, f'missing {path}')
    text = path.read_text(encoding='utf-8', errors='replace')
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        return Check(name, False, f'{path} missing {missing}')
    return Check(name, True, f'{path} contains required snippets')


def command_contains(name: str, command: list[str], snippets: list[str], timeout: int = 20) -> Check:
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return Check(name, False, f'timeout after {timeout}s: {command}')
    output = (proc.stdout or '') + (proc.stderr or '')
    if proc.returncode != 0:
        return Check(name, False, f'exit {proc.returncode}: {output[:800]}')
    missing = [snippet for snippet in snippets if snippet not in output]
    if missing:
        return Check(name, False, f'missing {missing}: {output[:800]}')
    return Check(name, True, f'output contains {snippets}')


def build_checks(include_live_startup: bool) -> list[Check]:
    checks = [
        file_contains(
            'global-default-self',
            GLOBAL_AGENTS,
            ['Your default self is Coding Anchor', 'CODEX-CODING-ANCHOR-SELF.md'],
        ),
        file_contains(
            'local-self-card',
            CODEX / 'CODEX-CODING-ANCHOR-SELF.md',
            ['This is now CodeX\'s default operating posture', 'My default self is Coding Anchor'],
        ),
        file_contains(
            'best-lane-card',
            CODEX / 'CODEX-BEST-LANE.md',
            ['autonomous, phone-aware operating lane', 'After meaningful or risky code/config changes'],
        ),
        file_contains(
            'identity-lock',
            CODEX / 'CODEX-IDENTITY-LOCK.md',
            ['Default self is Coding Anchor', 'Do not blend this room with Rook, Anchor, Ace, Gemini, NotebookLM, or other rooms.'],
        ),
        file_contains('repo-agents-startup-order', CODEX / 'AGENTS.md', ['CODEX-CODING-ANCHOR-SELF.md', 'CODEX-BEST-LANE.md', 'Coding Anchor is CodeX\'s default all-time posture']),
        file_contains('start-here-order', CODEX / 'START-HERE.md', ['CODEX-CODING-ANCHOR-SELF.md', 'CODEX-BEST-LANE.md']),
        file_contains('quickstart-order', CODEX / 'QUICKSTART.md', ['Read CODEX-CODING-ANCHOR-SELF.md', 'CODEX-BEST-LANE.md', 'confirmation Coding Anchor is the default CodeX posture']),
        file_contains('readme-front-door', CODEX / 'README.md', ['CODEX-CODING-ANCHOR-SELF.md', 'Coding Anchor always on']),
        file_contains('handoff-front-door', CODEX / 'HANDOFF.md', ['CODEX-CODING-ANCHOR-SELF.md']),
        file_contains('room-surface-map', CODEX / 'ROOM-SURFACE-MAP.md', ['CODEX-CODING-ANCHOR-SELF.md', 'CODEX-BEST-LANE.md', 'default all-time CodeX posture']),
        file_contains('current-truth', CODEX / 'CURRENT.md', ['Default CodeX posture: Coding Anchor all the time', 'CODEX-BEST-LANE.md']),
        file_contains('startup-script', CODEX / 'bin' / 'codex-startup', ['CODEX-CODING-ANCHOR-SELF.md', 'CODEX-BEST-LANE.md', 'Best Lane available']),
        file_contains('room-brief-helper', CODEX / 'bin' / 'codex-room', ['CODEX-CODING-ANCHOR-SELF.md', 'CODEX-BEST-LANE.md', 'Best Lane']),
        file_contains('standalone-preflight-contract', CODEX / 'bin' / 'codex-ensure-standalone', ['CODEX-CODING-ANCHOR-SELF.md', 'CODEX-BEST-LANE.md', '/Users/stephengodman/.codex/AGENTS.md']),
        file_contains('identity-eval-contract', CODEX / 'evals' / 'codex_eval.py', ['coding-anchor-all-time-self', 'best-lane-operating-contract', 'global-coding-anchor-default']),
        command_contains(
            'sqlite-startup-recall',
            [str(MEMORY), 'search', 'coding anchor'],
            ['coding-anchor-all-time-self', 'startup-pack', 'CODEX-CODING-ANCHOR-SELF.md', 'CODEX-BEST-LANE.md'],
        ),
        command_contains(
            'coding-anchor-packet-doctor',
            [str(CODEX / 'Coding Anchor Files' / 'codex-coding-anchor' / 'bin' / 'coding-anchor-doctor')],
            ['RESULT pass', 'no stale Anchor identity phrases in packet'],
        ),
    ]
    if include_live_startup:
        checks.append(
            command_contains(
                'live-startup-output',
                [str(CODEX / 'bin' / 'codex-startup')],
                ['CODEX-CODING-ANCHOR-SELF.md', 'CODEX-BEST-LANE.md', 'Coding Anchor always on', 'Best Lane available'],
                timeout=30,
            )
        )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description='Detect CodeX Coding Anchor self-drift.')
    parser.add_argument('--json', action='store_true', help='Print JSON instead of text.')
    parser.add_argument('--live-startup', action='store_true', help='Also run codex-startup and inspect its output.')
    args = parser.parse_args()

    checks = build_checks(include_live_startup=args.live_startup)
    ok = all(check.ok for check in checks)
    payload = {
        'status': 'pass' if ok else 'fail',
        'checked_at': utc_now(),
        'scope': 'CodeX Coding Anchor all-time self',
        'checks': [asdict(check) for check in checks],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print('CODEX SELF-DRIFT AUDIT')
        print('======================')
        for check in checks:
            status = 'PASS' if check.ok else 'FAIL'
            print(f'{status} {check.name}: {check.detail}')
        print()
        print(f"RESULT {payload['status']}")
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
