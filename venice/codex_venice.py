#!/usr/bin/env python3
"""CodeX Venice API helper.

Reads VENICE_API_KEY or VENICE_ADMIN_KEY from the process environment.
Never stores keys on disk.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request
from typing import Any


BASE_URL = "https://api.venice.ai/api/v1"
DEFAULT_MODEL = "venice-uncensored-1-2"


def get_key() -> str:
    key = os.environ.get("VENICE_API_KEY") or os.environ.get("VENICE_ADMIN_KEY")
    if not key:
        for name in ("VENICE_API_KEY", "VENICE_ADMIN_KEY"):
            try:
                result = subprocess.run(
                    ["/bin/launchctl", "getenv", name],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
            except OSError:
                continue
            key = result.stdout.strip()
            if key:
                os.environ[name] = key
                break
    if not key:
        raise SystemExit("Missing VENICE_API_KEY or VENICE_ADMIN_KEY in environment or launchctl.")
    return key


def request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {get_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return {
                "ok": 200 <= resp.status < 300,
                "status": resp.status,
                "data": json.loads(body) if body else {},
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "error": body[:2000],
        }


def list_models(limit: int) -> dict[str, Any]:
    result = request("GET", "/models")
    if not result["ok"]:
        return result
    data = result["data"].get("data", [])
    models = [item.get("id") for item in data if isinstance(item, dict) and item.get("id")]
    return {
        "ok": True,
        "status": result["status"],
        "model_count": len(models),
        "models": models[:limit],
    }


def search(query: str, limit: int, provider: str) -> dict[str, Any]:
    payload = {
        "query": query,
        "limit": max(1, min(limit, 20)),
        "search_provider": provider,
    }
    result = request("POST", "/augment/search", payload)
    if not result["ok"]:
        return result
    data = result["data"]
    return {
        "ok": True,
        "status": result["status"],
        "query": data.get("query", query),
        "provider": provider,
        "results": data.get("results", []),
    }


def list_characters(limit: int, search_query: str | None = None) -> dict[str, Any]:
    params = []
    if search_query:
        params.append(("search", search_query))
    if limit:
        params.append(("limit", str(max(1, min(limit, 100)))))
    query = ""
    if params:
        from urllib.parse import urlencode
        query = "?" + urlencode(params)
    result = request("GET", "/characters" + query)
    if not result["ok"]:
        return result
    data = result["data"].get("data", [])
    return {
        "ok": True,
        "status": result["status"],
        "count": len(data),
        "characters": data[:limit],
    }


def chat(prompt: str, model: str, max_tokens: int, character_slug: str | None = None) -> dict[str, Any]:
    venice_parameters: dict[str, Any] = {"include_venice_system_prompt": False}
    if character_slug:
        venice_parameters["character_slug"] = character_slug
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "venice_parameters": venice_parameters,
    }
    result = request("POST", "/chat/completions", payload)
    if not result["ok"]:
        return result
    data = result["data"]
    message = data.get("choices", [{}])[0].get("message", {})
    content = message.get("content") or message.get("reasoning_content") or ""
    return {
        "ok": True,
        "status": result["status"],
        "model": model,
        "character_slug": character_slug,
        "reply": content,
        "usage": data.get("usage", {}),
    }


def smoke() -> dict[str, Any]:
    models = list_models(10)
    if not models.get("ok"):
        return {"ok": False, "models": models}
    response = chat("Reply with exactly: VENICE_API_OK", DEFAULT_MODEL, 16)
    return {
        "ok": response.get("ok") and response.get("reply") == "VENICE_API_OK",
        "models": models,
        "chat": response,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CodeX Venice API helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    models_cmd = sub.add_parser("models", help="List available Venice models.")
    models_cmd.add_argument("--limit", type=int, default=20)

    chat_cmd = sub.add_parser("chat", help="Send one Venice chat completion.")
    chat_cmd.add_argument("prompt")
    chat_cmd.add_argument("--model", default=DEFAULT_MODEL)
    chat_cmd.add_argument("--max-tokens", type=int, default=128)
    chat_cmd.add_argument("--character-slug")

    search_cmd = sub.add_parser("search", help="Search the web through Venice augment/search.")
    search_cmd.add_argument("query")
    search_cmd.add_argument("--limit", type=int, default=8)
    search_cmd.add_argument("--provider", choices=["brave", "google"], default="brave")

    characters_cmd = sub.add_parser("characters", help="List/search Venice API characters.")
    characters_cmd.add_argument("--limit", type=int, default=10)
    characters_cmd.add_argument("--search")

    sub.add_parser("smoke", help="Run auth/model/chat smoke test.")

    args = parser.parse_args()
    if args.command == "models":
        payload = list_models(max(1, min(args.limit, 100)))
    elif args.command == "chat":
        payload = chat(args.prompt, args.model, max(1, min(args.max_tokens, 4096)), args.character_slug)
    elif args.command == "search":
        payload = search(args.query, args.limit, args.provider)
    elif args.command == "characters":
        payload = list_characters(args.limit, args.search)
    else:
        payload = smoke()
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
