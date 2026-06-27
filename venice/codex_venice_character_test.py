#!/usr/bin/env python3
"""Test local Venice character cards by sending their instructions as bounded prompts."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import codex_venice

CHAR_DIR = THIS_DIR / 'characters'
RESULT_DIR = THIS_DIR / 'results'
MODEL = 'venice-uncensored-role-play'
TESTS = {
    'codex-gremlin-critic.md': 'Plan: install all packages from a 592-line freeze because chromadb is missing. Give your response.',
    'chaos-shop-oracle.md': 'Invent one weird little room object for CodeX. It does not need to be useful.',
    'memphis-pool-shop-foreman.md': 'A Tara A/B fill trial is requested but no verified real job_measurement.json has been selected. Give your response.',
}


def extract_card(path: Path) -> dict[str, str]:
    text = path.read_text(encoding='utf-8')
    def field(label: str) -> str:
        m = re.search(rf'^{re.escape(label)}:\s*(.+)$', text, re.M)
        return m.group(1).strip() if m else ''
    instructions = text.split('## Instructions', 1)[1].strip() if '## Instructions' in text else text
    return {
        'file': path.name,
        'name': field('Name'),
        'description': field('Description'),
        'opening': field('Opening Message'),
        'instructions': instructions,
    }


def run_card(card: dict[str, str], scenario: str) -> dict[str, object]:
    prompt = f"""Use the following local Venice character card exactly. Stay in character and follow the output format.

Character name: {card['name']}
Description: {card['description']}
Instructions:
{card['instructions']}

Scenario:
{scenario}
"""
    result = codex_venice.chat(prompt, model=MODEL, max_tokens=320)
    return {
        'character': card['name'],
        'file': card['file'],
        'scenario': scenario,
        'ok': bool(result.get('ok')) and bool((result.get('reply') or '').strip()),
        'reply': (result.get('reply') or '').strip(),
        'usage': result.get('usage', {}),
        'status': result.get('status'),
    }


def main() -> int:
    results = []
    for filename, scenario in TESTS.items():
        card = extract_card(CHAR_DIR / filename)
        results.append(run_card(card, scenario))
    payload = {
        'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'model': MODEL,
        'results': results,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-venice-character-test.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
    print(f'CHARACTER_TEST={out}')
    for row in results:
        print('\n' + '=' * 60)
        print(row['character'])
        print('=' * 60)
        print(row['reply'])
    return 0 if all(row['ok'] for row in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
