#!/usr/bin/env python3
"""Summarize Venice bench receipts into a lightweight leaderboard."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

RESULTS_DIR = Path("/Users/stephengodman/Candice-Code/venice/results")


def load_receipt(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_receipt() -> Path:
    files = sorted(RESULTS_DIR.glob("*-venice-bench.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise SystemExit(f"No Venice bench receipts found in {RESULTS_DIR}")
    return files[-1]


def score_row(row: dict[str, Any]) -> int:
    if not row.get("ok"):
        return 0
    reply = (row.get("reply") or "").strip()
    if not reply:
        return 0
    score = 50
    if row.get("elapsed_ms") is not None:
        if row["elapsed_ms"] < 1200:
            score += 15
        elif row["elapsed_ms"] < 2500:
            score += 8
    if 20 <= len(reply) <= 900:
        score += 15
    if reply.lower().startswith(("1.", "analyze", "we need", "let's")):
        score -= 8
    if "weakest assumption" in (row.get("prompt") or "").lower() and len(reply) > 20:
        score += 5
    if row.get("cached_tokens"):
        score += 3
    return max(0, score)


def summarize(path: Path) -> dict[str, Any]:
    receipt = load_receipt(path)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in receipt.get("results", []):
        grouped[row.get("model", "unknown")].append(row)

    models = []
    for model, rows in grouped.items():
        scores = [score_row(row) for row in rows]
        ok_rows = [row for row in rows if row.get("ok")]
        failures = [row for row in rows if not row.get("ok")]
        empty_or_reasoningish = [
            row for row in rows
            if not (row.get("reply") or "").strip()
            or (row.get("reply") or "").strip().lower().startswith(("1.", "analyze the request"))
        ]
        avg_latency = mean([row["elapsed_ms"] for row in ok_rows if row.get("elapsed_ms") is not None]) if ok_rows else None
        avg_tokens = mean([row["total_tokens"] for row in ok_rows if row.get("total_tokens") is not None]) if ok_rows else None
        best_reply = max(ok_rows, key=score_row).get("reply", "") if ok_rows else ""
        models.append({
            "model": model,
            "score": round(mean(scores), 1) if scores else 0,
            "ok": len(ok_rows),
            "fail": len(failures),
            "avg_latency_ms": round(avg_latency, 1) if avg_latency is not None else None,
            "avg_tokens": round(avg_tokens, 1) if avg_tokens is not None else None,
            "quirks": ["empty_or_reasoningish_output"] if empty_or_reasoningish else [],
            "best_reply_preview": best_reply.strip().replace("\n", " ")[:220],
        })

    models.sort(key=lambda item: (item["score"], item["ok"], -(item["avg_latency_ms"] or 999999)), reverse=True)
    return {
        "receipt": str(path),
        "created_at": receipt.get("created_at"),
        "prompt_count": len(receipt.get("prompts", [])),
        "leaderboard": models,
    }


def print_text(summary: dict[str, Any]) -> None:
    print("VENICE LEADERBOARD")
    print("==================")
    print(f"receipt: {summary['receipt']}")
    print(f"prompts: {summary['prompt_count']}")
    print("")
    for idx, item in enumerate(summary["leaderboard"], 1):
        latency = f"{item['avg_latency_ms']}ms" if item["avg_latency_ms"] is not None else "n/a"
        tokens = f"{item['avg_tokens']} tokens" if item["avg_tokens"] is not None else "n/a"
        quirks = f" quirks={','.join(item['quirks'])}" if item["quirks"] else ""
        print(f"{idx}. {item['model']} score={item['score']} ok={item['ok']} fail={item['fail']} latency={latency} usage={tokens}{quirks}")
        if item["best_reply_preview"]:
            print(f"   best: {item['best_reply_preview']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Venice bench receipts.")
    parser.add_argument("receipt", nargs="?", type=Path, help="Receipt JSON. Defaults to latest bench receipt.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = args.receipt or latest_receipt()
    summary = summarize(path)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
