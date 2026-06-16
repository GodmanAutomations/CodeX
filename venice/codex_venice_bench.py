#!/usr/bin/env python3
"""Run small Venice model comparisons for CodeX.

Secrets stay env-only. The script never writes API keys to disk.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import codex_venice

RESULTS_DIR = THIS_DIR / "results"
DEFAULT_MODELS = [
    "venice-uncensored-1-2",
    "z-ai-glm-5-turbo",
    "zai-org-glm-4.7-flash",
]
DEFAULT_PROMPTS = [
    "In one sentence, say what kind of task you are best at.",
    "Find one weak assumption in this plan: build a model bench before trusting model vibes.",
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def get_launchctl_key(name: str) -> str | None:
    try:
        result = subprocess.run(
            ["/bin/launchctl", "getenv", name],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return None
    value = result.stdout.strip()
    return value or None


def ensure_key_available() -> None:
    if os.environ.get("VENICE_API_KEY") or os.environ.get("VENICE_ADMIN_KEY"):
        return
    for name in ("VENICE_API_KEY", "VENICE_ADMIN_KEY"):
        value = get_launchctl_key(name)
        if value:
            os.environ[name] = value
            return
    raise SystemExit("Missing VENICE_API_KEY or VENICE_ADMIN_KEY in environment or launchctl.")


def available_models() -> set[str]:
    payload = codex_venice.list_models(200)
    if not payload.get("ok"):
        raise SystemExit(json.dumps({"error": "model list failed", "payload": payload}, indent=2))
    return set(payload.get("models", []))


def run_one(model: str, prompt: str, max_tokens: int) -> dict[str, Any]:
    started = time.perf_counter()
    result = codex_venice.chat(prompt, model=model, max_tokens=max_tokens)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    usage = result.get("usage", {}) if isinstance(result, dict) else {}
    reply = result.get("reply", "") if result.get("ok") else ""
    ok = bool(result.get("ok")) and bool(reply.strip())
    return {
        "model": model,
        "prompt": prompt,
        "ok": ok,
        "status": result.get("status"),
        "elapsed_ms": elapsed_ms,
        "reply": reply,
        "error": result.get("error", "") if not result.get("ok") else ("empty reply" if not ok else ""),
        "usage": usage,
        "total_tokens": usage.get("total_tokens"),
        "cached_tokens": usage.get("prompt_tokens_details", {}).get("cached_tokens")
        or usage.get("cache_read_input_tokens"),
    }


def write_result(payload: dict[str, Any], output: Path | None) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = output or RESULTS_DIR / f"{utc_stamp()}-venice-bench.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def print_summary(payload: dict[str, Any]) -> None:
    print("VENICE BENCH")
    print("============")
    print(f"result: {payload['result_path']}")
    print(f"models: {', '.join(payload['models'])}")
    print(f"prompts: {len(payload['prompts'])}")
    print("")
    for row in payload["results"]:
        status = "OK" if row["ok"] else "FAIL"
        token_bits = []
        if row.get("total_tokens") is not None:
            token_bits.append(f"tokens={row['total_tokens']}")
        if row.get("cached_tokens") is not None:
            token_bits.append(f"cached={row['cached_tokens']}")
        token_text = " " + " ".join(token_bits) if token_bits else ""
        print(f"{status} {row['model']} {row['elapsed_ms']}ms{token_text}")
        first_line = (row.get("reply") or row.get("error") or "").strip().splitlines()[0:1]
        if first_line:
            print(f"  {first_line[0][:220]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark a small set of Venice models.")
    parser.add_argument("--model", action="append", dest="models", help="Model to include. Repeatable.")
    parser.add_argument("--prompt", action="append", dest="prompts", help="Prompt to run. Repeatable.")
    parser.add_argument("--max-tokens", type=int, default=96)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-missing-models", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print full JSON instead of summary.")
    args = parser.parse_args()

    ensure_key_available()
    models = args.models or DEFAULT_MODELS
    prompts = args.prompts or DEFAULT_PROMPTS
    max_tokens = max(1, min(args.max_tokens, 4096))

    available = available_models()
    missing = [model for model in models if model not in available]
    if missing and not args.allow_missing_models:
        raise SystemExit(f"Missing Venice models: {', '.join(missing)}")
    models = [model for model in models if model in available or args.allow_missing_models]

    results = [run_one(model, prompt, max_tokens) for model in models for prompt in prompts]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "models": models,
        "prompts": prompts,
        "missing_models": missing,
        "results": results,
    }
    result_path = write_result(payload, args.output)
    payload["result_path"] = str(result_path)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_summary(payload)
    return 0 if all(row["ok"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
