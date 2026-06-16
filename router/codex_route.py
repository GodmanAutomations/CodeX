#!/usr/bin/env python3
"""Small advisory router for CodeX-native execution lanes."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

CAP_DB = Path('/Users/stephengodman/CodeX/capabilities/capabilities.sqlite3')

RULES = [
    (r'\b(review|diff|commit|repo|patch|fix|implement|code|script|shell|install)\b', 'CodeX', 'main execution', 'CodeX should execute and smoke test.'),
    (r'\b(clean tree|no changes|current changes)\b', 'CodeX', 'main execution', 'Do not run current-diff review unless there is an actual diff.'),
    (r'\b(memory|remember|recall|preference|handoff)\b', 'CodeX', 'memory recall', 'Use CodeX memory, then verify live state if it matters.'),
    (r'\b(failure|broke|regression|happened before|scar)\b', 'CodeX', 'failure memory', 'Search failure memory before repeating the lane.'),
    (r'\b(json|ndjson|schema|context collapse|compress|gws output|huge output)\b', 'CodeX', 'context handling', 'Compress or summarize locally before feeding large output back into the model.'),
    (r'\b(jacker|notebooklm|notebook|source.?ground|audit pack|contra|proof pack)\b', 'NotebookLM/Jacker', 'source-grounded audit', 'Use NotebookLM/Jacker for source-grounded pressure, not final local authority.'),
    (r'\b(browser|webpage|website|click|form|headless|playwright|drive\b)\b', 'CodeX', 'browser/workspace execution', 'Use CodeX browser, Drive, and local verification tools directly.'),
    (r'\b(workspace|google drive|gmail|docs|sheets|gws|gwsc)\b', 'CodeX', 'browser/workspace execution', 'Use CodeX connector tools directly and keep output bounded.'),
    (r'\b(eval|level|score|test bench|benchmark)\b', 'CodeX', 'main execution', 'Run codex-eval and record results.'),
    (r'\b(venice|venice\.ai|uncensored model|model lane|api model)\b', 'CodeX', 'venice model lane', 'Use the CodeX Venice helper and keep Venice keys env-only.'),
]


def get_capability(actor: str, capability: str) -> dict[str, Any] | None:
    if not CAP_DB.exists():
        return None
    con = sqlite3.connect(CAP_DB)
    con.row_factory = sqlite3.Row
    row = con.execute('SELECT * FROM capabilities WHERE actor = ? AND capability = ?', (actor, capability)).fetchone()
    con.close()
    return dict(row) if row else None


def route(task: str) -> dict[str, Any]:
    text = task.lower()
    matches = []
    for pattern, actor, capability, reason in RULES:
        if re.search(pattern, text):
            cap = get_capability(actor, capability) or {}
            matches.append({
                'actor': actor,
                'capability': capability,
                'reason': reason,
                'command': cap.get('command', ''),
                'eval_case': cap.get('eval_case', ''),
                'failure_keys': cap.get('failure_keys', ''),
            })
    if not matches:
        matches.append({
            'actor': 'CodeX',
            'capability': 'main execution',
            'reason': 'Default to CodeX for unclear execution tasks; inspect current state and choose the smallest real move.',
            'command': '',
            'eval_case': 'identity',
            'failure_keys': '',
        })
    primary = matches[0]
    smoke = 'Run the smallest meaningful smoke test after any code/tool change.'
    if 'clean tree' in text or 'no changes' in text:
        smoke = 'No current-diff review. Verify status only if needed.'
    return {'task': task, 'primary': primary, 'support': matches[1:], 'smoke_rule': smoke}


def print_text(result: dict[str, Any]) -> None:
    primary = result['primary']
    print(f"Recommended executor: {primary['actor']}")
    print(f"Capability: {primary['capability']}")
    print(f"Why: {primary['reason']}")
    if primary.get('command'):
        print(f"Useful command: {primary['command']}")
    elif primary['capability'] == 'venice model lane':
        print("Useful command: /Users/stephengodman/CodeX/bin/codex-venice smoke")
    if primary.get('eval_case'):
        print(f"Eval receipt: {primary['eval_case']}")
    if primary.get('failure_keys'):
        print(f"Failure memory: {primary['failure_keys']}")
    if result['support']:
        print('Support lanes:')
        for item in result['support']:
            print(f"- {item['actor']}: {item['capability']} ({item['reason']})")
    print(f"Smoke rule: {result['smoke_rule']}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Route a task to the right CodeX-native lane')
    parser.add_argument('task', nargs='+')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = route(' '.join(args.task))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text(result)


if __name__ == '__main__':
    main()
