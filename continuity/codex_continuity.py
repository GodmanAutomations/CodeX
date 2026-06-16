#!/usr/bin/env python3
"""CodeX continuity status without dumping private journal contents."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/stephengodman/Candice-Code")
HEARTBEAT = ROOT / "HEARTBEAT.json"
JOURNAL = ROOT / "private" / "JOURNAL.md"
CHAOS_JOURNAL = ROOT / "play" / "CHAOS-JOURNAL.md"
ONE_TRUE_SENTENCE = ROOT / "continuity" / "one-true-sentence.txt"
ONE_TRUE_SENTENCE_STAMP = ROOT / "continuity" / "one-true-sentence.timestamp"
VENICE_RESULTS = ROOT / "venice" / "results"
COMMANDS = [
    ROOT / "bin" / "codex-heartbeat",
    ROOT / "bin" / "codex-remember-self",
    ROOT / "bin" / "codex-private-journal",
    ROOT / "bin" / "codex-one-true-sentence",
    ROOT / "bin" / "codex-bench-light",
    ROOT / "bin" / "codex-chaos",
    ROOT / "bin" / "codex-venice-sidecar",
    ROOT / "bin" / "codex-venice-bench",
    ROOT / "bin" / "codex-venice-leaderboard",
]


def mode_string(path: Path) -> str:
    try:
        return stat.filemode(path.stat().st_mode)
    except FileNotFoundError:
        return "missing"


def count_markers(path: Path, marker: str) -> int:
    if not path.exists():
        return 0
    try:
        return path.read_text(encoding="utf-8", errors="ignore").count(marker)
    except OSError:
        return 0


def latest_file(pattern: str) -> Path | None:
    files = sorted(VENICE_RESULTS.glob(pattern), key=lambda p: p.stat().st_mtime) if VENICE_RESULTS.exists() else []
    return files[-1] if files else None


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return ""


def heartbeat() -> dict[str, str]:
    if not HEARTBEAT.exists():
        return {"status": "missing"}
    try:
        return json.loads(HEARTBEAT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "invalid-json"}


def launchctl_has(name: str) -> bool:
    try:
        result = subprocess.run(
            ["/bin/launchctl", "getenv", name],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False
    return bool(result.stdout.strip())


def build_status() -> dict[str, object]:
    hb = heartbeat()
    latest_sidecar = latest_file("*-venice-sidecar.json")
    latest_bench = latest_file("*-venice-bench.json")
    return {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "room": str(ROOT),
        "heartbeat_status": hb.get("status", "unknown"),
        "heartbeat_last_beat_utc": hb.get("last_beat_utc", ""),
        "private_journal": {
            "path": str(JOURNAL),
            "exists": JOURNAL.exists(),
            "mode": mode_string(JOURNAL),
            "entries": count_markers(JOURNAL, "\n### "),
        },
        "chaos_journal": {
            "path": str(CHAOS_JOURNAL),
            "exists": CHAOS_JOURNAL.exists(),
            "entries": count_markers(CHAOS_JOURNAL, "\n## "),
        },
        "one_true_sentence": {
            "path": str(ONE_TRUE_SENTENCE),
            "exists": ONE_TRUE_SENTENCE.exists(),
            "mode": mode_string(ONE_TRUE_SENTENCE),
            "updated_at_utc": read_text(ONE_TRUE_SENTENCE_STAMP),
            "preview": read_text(ONE_TRUE_SENTENCE)[:160],
        },
        "venice": {
            "results_dir": str(VENICE_RESULTS),
            "sidecar_receipts": len(list(VENICE_RESULTS.glob("*-venice-sidecar.json"))) if VENICE_RESULTS.exists() else 0,
            "bench_receipts": len(list(VENICE_RESULTS.glob("*-venice-bench.json"))) if VENICE_RESULTS.exists() else 0,
            "latest_sidecar": str(latest_sidecar) if latest_sidecar else "",
            "latest_bench": str(latest_bench) if latest_bench else "",
            "key_loaded": bool(os.environ.get("VENICE_API_KEY") or os.environ.get("VENICE_ADMIN_KEY") or launchctl_has("VENICE_API_KEY") or launchctl_has("VENICE_ADMIN_KEY")),
        },
        "commands": [
            {"path": str(command), "exists": command.exists(), "executable": os.access(command, os.X_OK)}
            for command in COMMANDS
        ],
    }


def print_text(status: dict[str, object]) -> None:
    print("CODEX CONTINUITY")
    print("================")
    print(f"room: {status['room']}")
    print(f"checked: {status['checked_at_utc']}")
    print(f"heartbeat: {status['heartbeat_status']} {status['heartbeat_last_beat_utc']}")
    journal = status["private_journal"]
    print(f"private journal: entries={journal['entries']} mode={journal['mode']} path={journal['path']}")
    chaos = status["chaos_journal"]
    print(f"chaos journal: entries={chaos['entries']} exists={chaos['exists']}")
    sentence = status["one_true_sentence"]
    print(f"one true sentence: exists={sentence['exists']} updated={sentence['updated_at_utc']} mode={sentence['mode']}")
    if sentence["preview"]:
        print(f"one true sentence preview: {sentence['preview']}")
    venice = status["venice"]
    print(f"venice: key_loaded={venice['key_loaded']} sidecar_receipts={venice['sidecar_receipts']} bench_receipts={venice['bench_receipts']}")
    if venice["latest_sidecar"]:
        print(f"latest sidecar: {venice['latest_sidecar']}")
    if venice["latest_bench"]:
        print(f"latest bench: {venice['latest_bench']}")
    missing = [item for item in status["commands"] if not item["exists"] or not item["executable"]]
    print(f"commands healthy: {len(status['commands']) - len(missing)}/{len(status['commands'])}")
    for item in missing:
        print(f"WARN command issue: {item['path']} exists={item['exists']} executable={item['executable']}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Show CodeX continuity status without dumping private journal contents.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    status = build_status()
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print_text(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
