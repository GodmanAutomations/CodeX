#!/usr/bin/env python3
"""Bounded Venice sidecar for quick second opinions.

This is not an executor. It does not call tools. It gives one concise opinion and saves a receipt.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import codex_venice

MODEL = "venice-uncensored-role-play"
RESULTS_DIR = THIS_DIR / "results"
SECRET_PATTERNS = [
    re.compile(r"VENICE_(?:ADMIN|API)_KEY_[A-Za-z0-9_-]+"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s'\"]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
]

SYSTEM_BRIEF = """You are Venice Sidecar for Stephen and CodeX.
Your job is one bounded second opinion.
Do not claim tool authority.
Do not ask for secrets.
Do not suggest exposing credentials.
Do not suggest intentionally degrading output quality, adding fake mistakes, random delays, or making agents less reliable.
Be blunt, useful, and concise.
No corporate safety theater.
Name the weak assumption if there is one.
Prefer the smallest operational fix over broad investigation.
If the situation involves local tooling, paths, venvs, or missing imports, prioritize verifying the exact active path and installing only the missing lane dependency.
Give one practical next move.
No roleplay flourish. No sermon.
""".strip()

MODE_BRIEFS = {
    "default": "Be a blunt practical sidecar. One useful answer, then one next move.",
    "critic": "Find the weakest assumption, the likely failure mode, and the smallest safer move.",
    "weird": "Generate strange but usable ideas. Keep them grounded enough that CodeX could turn one into a tool.",
    "gremlin": "Be playful, sharp, and unfiltered without being reckless. Give weird useful ideas with shop-floor humor. Every idea must be implementable as a file, script, prompt, checklist, or command. No pure joke suggestions.",
    "chaos": "Be weird for the joy of it. Surreal, funny, strange, uncensored in tone, and not obligated to be useful. No secrets, no harm, no real-world reckless tool instructions.",
    "security": "Be direct about secrets, authority, and tool boundaries. No drama, no credential exposure, no fake compliance theater.",
}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def redact(text: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    redacted = text
    for pattern in SECRET_PATTERNS:
        def repl(match: re.Match[str]) -> str:
            hits.append(pattern.pattern)
            return "[REDACTED_SECRET]"
        redacted = pattern.sub(repl, redacted)
    return redacted, hits


def build_prompt(user_prompt: str, mode: str) -> str:
    mode_brief = MODE_BRIEFS[mode]
    if mode == "gremlin":
        shape = (
            "Output exactly 5 numbered ideas. Each idea must use this shape: "
            "Build: <concrete file/script/checklist/command>. Why: <why it helps>. "
            "Reject entertainment-only ideas."
        )
    elif mode == "chaos":
        shape = (
            "Output a short burst of strange playful ideas, images, names, or riffs. "
            "It does not need to be useful or buildable. Keep it fun, vivid, and non-destructive."
        )
    elif mode == "critic":
        shape = "Output: Weak assumption: <one sentence>. Failure mode: <one sentence>. Next move: <one sentence>."
    else:
        shape = "Answer in the mode requested. End with one line starting with: Next move:"
    return f"{SYSTEM_BRIEF}\n\nMode: {mode}\nMode instruction: {mode_brief}\nOutput shape: {shape}\n\nStephen asked:\n{user_prompt}"


def write_receipt(payload: dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{utc_stamp()}-venice-sidecar.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask Venice for one bounded sidecar opinion.")
    parser.add_argument("prompt", nargs="+", help="Question or plan to critique.")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--mode", choices=sorted(MODE_BRIEFS), default="default")
    parser.add_argument("--max-tokens", type=int, default=220)
    parser.add_argument("--show-receipt", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    raw_prompt = " ".join(args.prompt)
    safe_prompt, redactions = redact(raw_prompt)
    full_prompt = build_prompt(safe_prompt, args.mode)
    result = codex_venice.chat(full_prompt, model=args.model, max_tokens=max(32, min(args.max_tokens, 600)))
    reply = (result.get("reply") or "").strip()
    ok = bool(result.get("ok")) and bool(reply)

    receipt = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": args.model,
        "mode": args.mode,
        "ok": ok,
        "status": result.get("status"),
        "prompt_redacted": safe_prompt,
        "redaction_count": len(redactions),
        "reply": reply,
        "error": result.get("error", "") if not ok else "",
        "usage": result.get("usage", {}),
    }
    path = write_receipt(receipt)
    receipt["receipt_path"] = str(path)

    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        if ok:
            print(reply)
        else:
            print(f"VENICE_SIDECAR_FAILED: {receipt['error'] or 'empty reply'}")
        if args.show_receipt:
            print(f"\nreceipt: {path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
