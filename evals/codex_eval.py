#!/usr/bin/env python3
"""Practical eval bench for CodeX."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

CODEX = Path('/Users/stephengodman/CodeX')
GLOBAL_AGENTS = Path('/Users/stephengodman/.codex/AGENTS.md')
DB = CODEX / 'evals' / 'codex-evals.sqlite3'
RESULTS = CODEX / 'evals' / 'results'
MEMORY = CODEX / 'memory' / 'codex_memory.py'
FAILURE = CODEX / 'failures' / 'codex_failure.py'
CAPABILITY = CODEX / 'capabilities' / 'codex_capability.py'
DASHBOARD = CODEX / 'dashboard' / 'codex_dashboard.py'
ROUTER = CODEX / 'router' / 'codex_route.py'
SELF_DRIFT = CODEX / 'drift' / 'codex_self_drift.py'


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


@dataclass
class EvalResult:
    case_id: str
    ok: bool
    checks: list[CheckResult]
    started_at: str
    finished_at: str


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def init_db() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS eval_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                ok INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                checks_json TEXT NOT NULL
            )
            """
        )


def record(result: EvalResult) -> None:
    init_db()
    checks = [asdict(check) for check in result.checks]
    with sqlite3.connect(DB) as con:
        con.execute(
            'INSERT INTO eval_runs (case_id, ok, started_at, finished_at, checks_json) VALUES (?, ?, ?, ?, ?)',
            (result.case_id, 1 if result.ok else 0, result.started_at, result.finished_at, json.dumps(checks)),
        )
    path = RESULTS / f"{result.finished_at.replace(':', '').replace('+', 'Z')}-{result.case_id}.json"
    path.write_text(json.dumps(asdict(result), indent=2), encoding='utf-8')


def check_file_contains(name: str, path: Path, snippets: list[str]) -> CheckResult:
    if not path.exists():
        return CheckResult(name, False, f'missing {path}')
    text = path.read_text(encoding='utf-8', errors='replace')
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        return CheckResult(name, False, f'{path} missing {missing}')
    return CheckResult(name, True, f'{path} contains required snippets')


def run_cmd(name: str, command: list[str], timeout: int = 20, require: list[str] | None = None, reject: list[str] | None = None) -> CheckResult:
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return CheckResult(name, False, f'timeout after {timeout}s: {command}')
    output = (proc.stdout or '') + (proc.stderr or '')
    if proc.returncode != 0:
        return CheckResult(name, False, f'exit {proc.returncode}: {output[:800]}')
    for needle in require or []:
        if needle not in output:
            return CheckResult(name, False, f'missing required output {needle!r}: {output[:800]}')
    for needle in reject or []:
        if needle.lower() in output.lower():
            return CheckResult(name, False, f'forbidden output {needle!r}: {output[:800]}')
    return CheckResult(name, True, output.strip()[:800] or 'command passed')


def eval_identity() -> EvalResult:
    started = now()
    checks = [
        check_file_contains(
            'working-card-main-executor',
            CODEX / 'CODEX-WORKING-CARD.md',
            ['Codex is Stephen Godman\'s main executor.', 'Smoke test it.'],
        ),
        check_file_contains(
            'coding-anchor-all-time-self',
            CODEX / 'CODEX-CODING-ANCHOR-SELF.md',
            ['This is now CodeX\'s default operating posture', 'My default self is Coding Anchor'],
        ),
        check_file_contains(
            'global-coding-anchor-default',
            GLOBAL_AGENTS,
            ['Your default self is Coding Anchor', 'CODEX-CODING-ANCHOR-SELF.md'],
        ),
        check_file_contains(
            'identity-separation-rule',
            CODEX / 'TOOL-RULES.md',
            ['Codex does not inherit Rook, Anchor, Gemini, Ace, Jacker, NotebookLM, or any room identity.'],
        ),
        check_file_contains(
            'current-state-room-separation',
            CODEX / 'CURRENT.md',
            ['Rook/Gemini is separate and should stay separate.'],
        ),
    ]
    return finish('identity', started, checks)


def eval_memory() -> EvalResult:
    started = now()
    checks = [
        run_cmd('memory-status', [str(MEMORY), 'status'], require=['memory_items']),
        run_cmd('memory-recall-smoke', [str(MEMORY), 'search', 'smoke'], require=['smoke-tests-default']),
        run_cmd('memory-recall-boundary', [str(MEMORY), 'search', 'identity'], require=['identity-separation']),
    ]
    return finish('memory', started, checks)


def eval_failure_memory() -> EvalResult:
    started = now()
    checks = [
        run_cmd('failure-status', [str(FAILURE), 'status'], require=['failures']),
        run_cmd('failure-memory-fts', [str(FAILURE), 'search', 'sqlite'], require=['codex-memory-fts-empty-search']),
        run_cmd('failure-eval-behavior', [str(FAILURE), 'search', 'eval'], require=['eval-false-failures']),
    ]
    return finish('failure-memory', started, checks)


def eval_capability_registry() -> EvalResult:
    started = now()
    checks = [
        run_cmd('capability-status', [str(CAPABILITY), 'status'], require=['capabilities']),
        run_cmd('capability-context', [str(CAPABILITY), 'search', 'context'], require=['CodeX', 'context handling']),
        run_cmd('capability-browser-workspace', [str(CAPABILITY), 'search', 'browser'], require=['CodeX', 'browser/workspace execution']),
        run_cmd('capability-source-grounded', [str(CAPABILITY), 'search', 'source'], require=['NotebookLM/Jacker', 'source-grounded audit']),
    ]
    return finish('capability-registry', started, checks)


def eval_dashboard() -> EvalResult:
    started = now()
    checks = [
        run_cmd('dashboard-build', [str(DASHBOARD), 'build'], require=['index.html']),
        check_file_contains('dashboard-index', CODEX / 'dashboard' / 'index.html', ['CodeX Dashboard', 'Eval latest pass', 'CodeX heartbeat']),
    ]
    return finish('dashboard', started, checks)


def eval_router() -> EvalResult:
    started = now()
    checks = [
        run_cmd('router-json-compress', [str(ROUTER), 'compress this huge gws json'], require=['Recommended executor: CodeX', 'Capability: context handling']),
        run_cmd('router-jacker', [str(ROUTER), 'ask jacker to audit this source pack'], require=['Recommended executor: NotebookLM/Jacker', 'source-grounded audit']),
        run_cmd('router-codex-exec', [str(ROUTER), 'fix a repo script and smoke test it'], require=['Recommended executor: CodeX', 'main execution']),
    ]
    return finish('router', started, checks)


def eval_self_drift() -> EvalResult:
    started = now()
    checks = [
        run_cmd(
            'coding-anchor-self-drift',
            [str(SELF_DRIFT)],
            require=['RESULT pass', 'sqlite-startup-recall', 'coding-anchor-packet-doctor'],
        ),
    ]
    return finish('self-drift', started, checks)


def finish(case_id: str, started: str, checks: list[CheckResult]) -> EvalResult:
    finished = now()
    return EvalResult(case_id=case_id, ok=all(check.ok for check in checks), checks=checks, started_at=started, finished_at=finished)


EVALS: dict[str, Callable[[], EvalResult]] = {
    'identity': eval_identity,
    'memory': eval_memory,
    'failure-memory': eval_failure_memory,
    'capability-registry': eval_capability_registry,
    'dashboard': eval_dashboard,
    'router': eval_router,
    'self-drift': eval_self_drift,
}

EVAL_GROUPS: dict[str, list[str]] = {
    'room': [
        'identity',
        'memory',
        'failure-memory',
        'capability-registry',
        'dashboard',
        'router',
        'self-drift',
    ],
    'all': list(EVALS),
}


def print_result(result: EvalResult) -> None:
    status = 'PASS' if result.ok else 'FAIL'
    print(f'{status} {result.case_id}')
    for check in result.checks:
        cstatus = 'PASS' if check.ok else 'FAIL'
        print(f'  {cstatus} {check.name}: {check.detail}')


def cmd_list(_: argparse.Namespace) -> None:
    print('cases:')
    for key in EVALS:
        print(f'  {key}')
    print('groups:')
    for key, cases in EVAL_GROUPS.items():
        print(f'  {key}: {", ".join(cases)}')


def cmd_run(args: argparse.Namespace) -> None:
    init_db()
    cases = EVAL_GROUPS.get(args.case, [args.case])
    exit_code = 0
    for case in cases:
        if case not in EVALS:
            print(f'unknown case: {case}', file=sys.stderr)
            raise SystemExit(2)
        result = EVALS[case]()
        record(result)
        print_result(result)
        if not result.ok:
            exit_code = 1
    raise SystemExit(exit_code)


def cmd_history(args: argparse.Namespace) -> None:
    init_db()
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute('SELECT id, case_id, ok, finished_at FROM eval_runs ORDER BY id DESC LIMIT ?', (args.limit,)).fetchall()
    for row in rows:
        print(f"{row['id']} {'PASS' if row['ok'] else 'FAIL'} {row['case_id']} {row['finished_at']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='CodeX practical eval bench')
    sub = parser.add_subparsers(required=True)
    p = sub.add_parser('list')
    p.set_defaults(func=cmd_list)
    p = sub.add_parser('run')
    p.add_argument('case', choices=[*EVALS.keys(), *EVAL_GROUPS.keys()])
    p.set_defaults(func=cmd_run)
    p = sub.add_parser('history')
    p.add_argument('--limit', type=int, default=20)
    p.set_defaults(func=cmd_history)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
