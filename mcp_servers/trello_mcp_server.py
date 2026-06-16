#!/usr/bin/env python3
"""Stephen-native Trello MCP server.

Exposes the Memphis Pool live board and Artesian backup board through MCP
without storing Trello secrets in MCP config. Credentials are read from
environment variables first, then Stephen's local credential profile.
"""
from __future__ import annotations

import argparse
import mimetypes
import os
import re
import hashlib
import json
import math
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://api.trello.com/1"
DEFAULT_TIMEOUT = 30
ARTIFACT_ROOT = Path("/Users/stephengodman/Candice-Code/work-artifacts/trello-mcp")
RAG_CLI = Path("/Users/stephengodman/000_AI/bin/rag")
POOL_JOBS_ROOT = Path("/Users/stephengodman/godman-pool-data/jobs")
LOCAL_TRELLO_CONFIG_PATH = Path("/Users/stephengodman/.trello-mcp/config.json")
TRELLO_MCP_LAUNCHER_PATH = Path("/Users/stephengodman/Candice-Code/mcp_servers/trello_mcp_launcher.sh")
CODEX_CONFIG_PATH = Path("/Users/stephengodman/.codex/config.toml")
CLAUDE_CONFIG_PATH = Path("/Users/stephengodman/.claude.json")
SUPPORTED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff"}
SUPPORTED_SHEET_EXTENSIONS = {".xls", ".xlsx", ".csv"}
SUPPORTED_WORK_ORDER_EXTENSIONS = SUPPORTED_SHEET_EXTENSIONS | {".pdf", ".txt"}
MATCH_STOPWORDS = {
    "pool",
    "liner",
    "measure",
    "measures",
    "install",
    "reset",
    "memphis",
    "artesian",
    "covered",
    "need",
    "needs",
    "the",
    "and",
    "for",
    "http",
    "https",
    "www",
    "com",
    "trello",
    "cards",
    "card",
    "attachments",
    "attachment",
    "download",
    "xls",
    "xlsx",
    "csv",
    "pdf",
    "jpg",
    "jpeg",
    "drive",
    "road",
    "street",
    "lane",
    "court",
    "cove",
    "circle",
    "avenue",
    "trail",
    "terrace",
    "parkway",
    "boulevard",
}
KNOWN_BOARDS = {
    "memphis": {
        "id": "6a2f3f45d1e13218cfc620c3",
        "name": "Memphis Pool - New Admin 2026-06-14",
        "role": "new default live jobs and billing board",
    },
    "legacy_memphis": {
        "id": "60df29145c9a576f23056516",
        "name": "Memphis Pool",
        "role": "legacy source board; keep for verification/history until archived",
    },
    "artesian": {
        "id": "60431cb6af79f452db557abb",
        "name": "Artesian Pools",
        "role": "backup / synced PWA board",
    },
}
PROFILE_PATHS = [
    Path("/Users/stephengodman/.claude/0stephen-profile/credentials.md"),
    Path("/Users/stephengodman/.claude/stephen-profile/credentials.md"),
]
OP_VAULT = "3i56wtg5jxdvaiz7ksc6bmh65y"
OP_TRELLO_ITEM = "ifrjvey3q2pztbbyv5e7zhd6da"
OP_TIMEOUT_SECONDS = int(os.getenv("TRELLO_OP_TIMEOUT_SECONDS", "8"))
OP_FAILURE_RETRY_SECONDS = int(os.getenv("TRELLO_OP_FAILURE_RETRY_SECONDS", "300"))
_CREDENTIAL_CACHE: tuple[str, str] | None = None
_OP_FAILURE_CACHE: dict[str, dict[str, Any]] = {}

mcp = FastMCP("trello")


class TrelloError(RuntimeError):
    pass


def _profile_text() -> str:
    for path in PROFILE_PATHS:
        if path.exists():
            return path.read_text(errors="ignore")
    return ""


def _local_trello_config() -> dict[str, Any]:
    if not LOCAL_TRELLO_CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(LOCAL_TRELLO_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _file_status(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": str(path),
        "exists": exists,
        "mode": oct(path.stat().st_mode & 0o777) if exists else None,
        "size": path.stat().st_size if exists else None,
    }


def _text_file_contains(path: Path, needle: str) -> bool:
    if not path.exists():
        return False
    try:
        return needle in path.read_text(errors="ignore")
    except Exception:
        return False


def _runtime_environment_summary() -> dict[str, Any]:
    key = os.getenv("TRELLO_API_KEY") or os.getenv("TRELLO_KEY")
    token = os.getenv("TRELLO_API_TOKEN") or os.getenv("TRELLO_TOKEN")
    return {
        "key_present": bool(key),
        "token_present": bool(token),
        "complete": bool(key and token),
        "disable_op_fallback": _op_fallback_disabled(),
        "op_run_timeout_seconds": os.getenv("TRELLO_OP_RUN_TIMEOUT_SECONDS"),
    }


def _launcher_config_summary() -> dict[str, Any]:
    launcher = _file_status(TRELLO_MCP_LAUNCHER_PATH)
    launcher["executable"] = bool(TRELLO_MCP_LAUNCHER_PATH.exists() and os.access(TRELLO_MCP_LAUNCHER_PATH, os.X_OK))
    config_needle = str(TRELLO_MCP_LAUNCHER_PATH)
    return {
        "launcher": launcher,
        "codex_config": {
            **_file_status(CODEX_CONFIG_PATH),
            "references_launcher": _text_file_contains(CODEX_CONFIG_PATH, config_needle),
        },
        "claude_config": {
            **_file_status(CLAUDE_CONFIG_PATH),
            "references_launcher": _text_file_contains(CLAUDE_CONFIG_PATH, config_needle),
        },
    }


def _configured_boards() -> dict[str, dict[str, str]]:
    boards = json.loads(json.dumps(KNOWN_BOARDS))
    config = _local_trello_config()
    config_keys = {
        "memphis": "boardId",
        "legacy_memphis": "legacyMemphisBoardId",
        "artesian": "artesianBoardId",
    }
    for alias, key in config_keys.items():
        value = str(config.get(key) or "").strip()
        if value:
            boards.setdefault(alias, {})["id"] = value
            boards[alias]["id_source"] = str(LOCAL_TRELLO_CONFIG_PATH)
    return boards


def _trello_section(text: str) -> str:
    match = re.search(r"(?ims)^#{2,4}\s+Trello\b(.*?)(?=^#{2,4}\s+|\Z)", text)
    return match.group(1) if match else text


def _extract_labeled_value(text: str, labels: list[str]) -> str | None:
    for label in labels:
        pattern = rf"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*[:=](?:\*\*)?\s*(.+?)\s*$"
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip().strip("`").strip()
            if value and "[redacted]" not in value.lower():
                return value
    return None


def _op_fallback_disabled() -> bool:
    return os.getenv("TRELLO_DISABLE_OP_FALLBACK", "").strip().lower() in {"1", "true", "yes", "on"}


def _op_failure_cache_snapshot() -> dict[str, Any]:
    now = time.monotonic()
    snapshot = {}
    for field, cached in _OP_FAILURE_CACHE.items():
        age = round(now - float(cached.get("cached_at_monotonic") or now), 3)
        remaining = max(0.0, round(OP_FAILURE_RETRY_SECONDS - age, 3))
        snapshot[field] = {
            "status": cached.get("status"),
            "cached": True,
            "age_seconds": age,
            "retry_after_seconds": remaining,
        }
    return snapshot


def _cache_op_failure(result: dict[str, Any]) -> None:
    if result.get("ok"):
        _OP_FAILURE_CACHE.pop(str(result.get("field") or ""), None)
        return
    cacheable_statuses = {"timeout", "op_not_found", "error", "nonzero_exit", "empty"}
    if result.get("status") in cacheable_statuses:
        cached = {k: v for k, v in result.items() if k != "value"}
        cached["cached_at_monotonic"] = time.monotonic()
        _OP_FAILURE_CACHE[str(result.get("field") or "")] = cached


def _cached_op_failure(field: str) -> dict[str, Any] | None:
    cached = _OP_FAILURE_CACHE.get(field)
    if not cached:
        return None
    age = time.monotonic() - float(cached.get("cached_at_monotonic") or 0)
    if age >= OP_FAILURE_RETRY_SECONDS:
        _OP_FAILURE_CACHE.pop(field, None)
        return None
    result = {k: v for k, v in cached.items() if k != "cached_at_monotonic"}
    result.update(
        {
            "ok": False,
            "field": field,
            "status": f"cached_{cached.get('status')}",
            "cached": True,
            "age_seconds": round(age, 3),
            "retry_after_seconds": max(0.0, round(OP_FAILURE_RETRY_SECONDS - age, 3)),
        }
    )
    return result


def _op_field_result(field: str, *, use_failure_cache: bool = True) -> dict[str, Any]:
    if _op_fallback_disabled():
        return {"ok": False, "field": field, "status": "disabled_by_env", "elapsed_seconds": 0.0}
    if use_failure_cache:
        cached = _cached_op_failure(field)
        if cached:
            return cached
    started = time.monotonic()
    try:
        result = subprocess.run(
            [
                "op",
                "item",
                "get",
                OP_TRELLO_ITEM,
                "--vault",
                OP_VAULT,
                "--field",
                field,
                "--reveal",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=OP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        result = {"ok": False, "field": field, "status": "timeout", "elapsed_seconds": round(time.monotonic() - started, 3)}
        _cache_op_failure(result)
        return result
    except FileNotFoundError:
        result = {"ok": False, "field": field, "status": "op_not_found", "elapsed_seconds": round(time.monotonic() - started, 3)}
        _cache_op_failure(result)
        return result
    except Exception as exc:
        result = {
            "ok": False,
            "field": field,
            "status": "error",
            "error_type": type(exc).__name__,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
        _cache_op_failure(result)
        return result
    elapsed = round(time.monotonic() - started, 3)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        op_result = {
            "ok": False,
            "field": field,
            "status": "nonzero_exit",
            "returncode": result.returncode,
            "detail": detail[:180],
            "elapsed_seconds": elapsed,
        }
        _cache_op_failure(op_result)
        return op_result
    value = result.stdout.strip()
    op_result = {
        "ok": bool(value),
        "field": field,
        "status": "ok" if value else "empty",
        "value": value or None,
        "elapsed_seconds": elapsed,
    }
    _cache_op_failure(op_result)
    return op_result


def _op_field(field: str) -> str | None:
    result = _op_field_result(field)
    return result.get("value") if result.get("ok") else None


def _credential_source_summary(*, try_op: bool = False) -> dict[str, Any]:
    env_key = os.getenv("TRELLO_API_KEY") or os.getenv("TRELLO_KEY")
    env_token = os.getenv("TRELLO_API_TOKEN") or os.getenv("TRELLO_TOKEN")
    profile_path = next((path for path in PROFILE_PATHS if path.exists()), None)
    profile_text = _profile_text()
    section = _trello_section(profile_text)
    profile_key = _extract_labeled_value(section, ["API Key", "Trello API Key", "Key"])
    profile_token = _extract_labeled_value(section, ["API Token", "Trello API Token", "Token"])
    summary: dict[str, Any] = {
        "cache_loaded": _CREDENTIAL_CACHE is not None,
        "environment": {
            "key_present": bool(env_key),
            "token_present": bool(env_token),
            "complete": bool(env_key and env_token),
        },
        "profile": {
            "path": str(profile_path) if profile_path else None,
            "exists": profile_path is not None,
            "trello_section_found": bool(profile_text and section != profile_text),
            "key_present": bool(profile_key),
            "token_present": bool(profile_token),
            "complete": bool(profile_key and profile_token),
        },
        "onepassword": {
            "item_id": OP_TRELLO_ITEM,
            "vault_id": OP_VAULT,
            "timeout_seconds": OP_TIMEOUT_SECONDS,
            "failure_retry_seconds": OP_FAILURE_RETRY_SECONDS,
            "disabled_by_env": _op_fallback_disabled(),
            "failure_cache": _op_failure_cache_snapshot(),
            "checked": False,
        },
    }
    if try_op:
        op_checks = {}
        for field in ("API Key", "Token"):
            result = _op_field_result(field)
            op_checks[field] = {k: v for k, v in result.items() if k != "value"}
        summary["onepassword"].update(
            {
                "checked": True,
                "fields": op_checks,
                "complete": all(item.get("ok") for item in op_checks.values()),
            }
        )
    return summary


def _credential_recommendation(summary: dict[str, Any], *, try_op: bool) -> str:
    if summary["environment"]["complete"]:
        return "Live Trello operations can use TRELLO_API_KEY/TRELLO_API_TOKEN from the MCP runtime environment."
    if summary["profile"]["complete"]:
        return "Live Trello operations can use the local profile credentials."
    if summary["onepassword"].get("complete"):
        return "Live Trello operations can use the configured 1Password item."

    onepassword = summary.get("onepassword") or {}
    fields = onepassword.get("fields") or {}
    statuses = {str(item.get("status") or "") for item in fields.values()}
    cached = onepassword.get("failure_cache") or {}
    cached_statuses = {str(item.get("status") or "") for item in cached.values()}
    combined_statuses = statuses | cached_statuses

    if onepassword.get("disabled_by_env"):
        return (
            "No complete env/profile credentials found, and TRELLO_DISABLE_OP_FALLBACK is enabled. "
            "Set TRELLO_API_KEY and TRELLO_API_TOKEN in the MCP runtime for live Trello operations."
        )
    if any("timeout" in status for status in combined_statuses):
        return (
            "1Password Trello lookup timed out. Set TRELLO_API_KEY and TRELLO_API_TOKEN in the MCP runtime "
            "to make live Trello operations reliable."
        )
    if try_op:
        return (
            "No complete Trello credential source found. Add API Key and API Token to the profile, "
            "or set TRELLO_API_KEY and TRELLO_API_TOKEN in the MCP runtime."
        )
    return (
        "No complete env/profile credentials found in fast mode. Set TRELLO_API_KEY and TRELLO_API_TOKEN "
        "in the MCP runtime, or run diagnostics with try_onepassword=True to test 1Password."
    )


def _credentials() -> tuple[str, str]:
    global _CREDENTIAL_CACHE
    if _CREDENTIAL_CACHE:
        return _CREDENTIAL_CACHE

    key = os.getenv("TRELLO_API_KEY") or os.getenv("TRELLO_KEY")
    token = os.getenv("TRELLO_API_TOKEN") or os.getenv("TRELLO_TOKEN")

    if key and token:
        _CREDENTIAL_CACHE = (key, token)
        return key, token

    section = _trello_section(_profile_text())
    key = key or _extract_labeled_value(section, ["API Key", "Trello API Key", "Key"])
    token = token or _extract_labeled_value(section, ["API Token", "Trello API Token", "Token"])
    key = key or _op_field("API Key")
    token = token or _op_field("Token")

    if not key or not token:
        raise TrelloError(
            "Trello credentials not found. Set TRELLO_API_KEY/TRELLO_API_TOKEN "
            "or add API Key and API Token under the Trello section of the local profile. "
            "If 1Password is slow, set TRELLO_DISABLE_OP_FALLBACK=1 to fail fast."
        )

    _CREDENTIAL_CACHE = (key, token)
    return key, token


def _board_id(board: str | None = None) -> str:
    key = (board or "memphis").strip()
    boards = _configured_boards()
    if key in boards:
        return boards[key]["id"]
    return key


def _request(method: str, endpoint: str, *, params: dict[str, Any] | None = None) -> Any:
    key, token = _credentials()
    req_params = {"key": key, "token": token}
    if params:
        req_params.update({k: v for k, v in params.items() if v is not None})

    response = requests.request(
        method,
        f"{BASE_URL}/{endpoint.lstrip('/')}",
        params=req_params,
        timeout=DEFAULT_TIMEOUT,
    )
    if not response.ok:
        raise TrelloError(f"Trello {method} {endpoint} failed: {response.status_code} {response.text[:300]}")
    if response.status_code == 204 or not response.text:
        return {"ok": True}
    return response.json()


def _request_files(
    method: str,
    endpoint: str,
    *,
    params: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
) -> Any:
    key, token = _credentials()
    req_params = {"key": key, "token": token}
    if params:
        req_params.update({k: v for k, v in params.items() if v is not None})

    response = requests.request(
        method,
        f"{BASE_URL}/{endpoint.lstrip('/')}",
        params=req_params,
        files=files,
        timeout=DEFAULT_TIMEOUT,
    )
    if not response.ok:
        raise TrelloError(f"Trello {method} {endpoint} failed: {response.status_code} {response.text[:300]}")
    if response.status_code == 204 or not response.text:
        return {"ok": True}
    return response.json()


def _download_request(url: str) -> bytes:
    key, token = _credentials()
    headers = {
        "Authorization": f'OAuth oauth_consumer_key="{key}", oauth_token="{token}"',
        "Accept": "*/*",
    }
    response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    if not response.ok:
        response = requests.get(url, params={"key": key, "token": token}, timeout=DEFAULT_TIMEOUT)
    if not response.ok:
        raise TrelloError(f"Trello attachment download failed: {response.status_code} {response.text[:300]}")
    return response.content


def _card_summary(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": card.get("id"),
        "name": card.get("name"),
        "shortUrl": card.get("shortUrl"),
        "idList": card.get("idList"),
        "closed": card.get("closed"),
        "due": card.get("due"),
        "labels": [label.get("name") or label.get("color") for label in card.get("labels", [])],
    }


def _card_with_board_context(card: dict[str, Any], *, list_name: str | None = None) -> dict[str, Any]:
    return {
        "id": card.get("id"),
        "name": card.get("name"),
        "url": card.get("url") or card.get("shortUrl"),
        "shortUrl": card.get("shortUrl"),
        "idList": card.get("idList"),
        "list": list_name,
    }


def _find_card_by_query(query: str, board: str = "memphis") -> dict[str, Any]:
    q = (query or "").strip().lower()
    if not q:
        raise TrelloError("card query is required")
    lists = get_lists(board)
    list_names = {item["id"]: item["name"] for item in lists}
    cards = _request(
        "GET",
        f"boards/{_board_id(board)}/cards",
        params={"filter": "open", "fields": "id,name,url,shortUrl,idList,closed"},
    )
    matches = [card for card in cards if q in str(card.get("name") or "").lower()]
    exact = [card for card in matches if str(card.get("name") or "").strip().lower() == q]
    if len(exact) == 1:
        return _card_with_board_context(exact[0], list_name=list_names.get(exact[0].get("idList")))
    if len(matches) == 1:
        return _card_with_board_context(matches[0], list_name=list_names.get(matches[0].get("idList")))
    if not matches:
        raise TrelloError(f"No open card matching {query!r} on board {board!r}")
    preview = [
        {
            "id": card.get("id"),
            "name": card.get("name"),
            "list": list_names.get(card.get("idList"), "UNKNOWN"),
            "url": card.get("url") or card.get("shortUrl"),
        }
        for card in matches[:8]
    ]
    raise TrelloError(f"Multiple cards match {query!r}: {json.dumps(preview)}")


def _safe_name(name: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", name or "artifact").strip("-")
    return clean[:120] or "artifact"


def _attachment_download_url(card_id: str, attachment: dict[str, Any]) -> str:
    url = attachment.get("url") or ""
    parsed = urlparse(url)
    path = parsed.path
    if "/download/" in path and parsed.netloc.endswith("trello.com"):
        return f"https://api.trello.com{path}"
    if parsed.netloc == "api.trello.com" and "/download/" in path:
        return url
    return f"{BASE_URL}/cards/{card_id}/attachments/{attachment['id']}/download/{_safe_name(attachment.get('name', 'attachment'))}"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _artifact_dir(kind: str) -> Path:
    path = ARTIFACT_ROOT / kind
    path.mkdir(parents=True, exist_ok=True)
    return path


def _excel_preview(path: Path, max_rows: int = 40, max_cols: int = 20) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        from openpyxl import load_workbook

        workbook = load_workbook(path, read_only=True, data_only=True)
        sheets = {}
        for sheet in workbook.worksheets:
            rows = []
            for row in sheet.iter_rows(max_row=max_rows, max_col=max_cols, values_only=True):
                values = ["" if value is None else str(value) for value in row]
                if any(v.strip() for v in values):
                    rows.append(values)
            sheets[sheet.title] = rows
        workbook.close()
        return {"type": "xlsx", "sheets": sheets}

    if suffix == ".xls":
        import xlrd

        workbook = xlrd.open_workbook(path)
        sheets = {}
        for sheet in workbook.sheets():
            rows = []
            for r in range(min(sheet.nrows, max_rows)):
                values = ["" if sheet.cell_value(r, c) is None else str(sheet.cell_value(r, c)) for c in range(min(sheet.ncols, max_cols))]
                if any(v.strip() for v in values):
                    rows.append(values)
            sheets[sheet.name] = rows
        return {"type": "xls", "sheets": sheets}

    if suffix == ".csv":
        import csv

        rows = []
        with path.open(newline="", errors="ignore") as f:
            for i, row in enumerate(csv.reader(f)):
                if i >= max_rows:
                    break
                rows.append(row[:max_cols])
        return {"type": "csv", "sheets": {"csv": rows}}

    raise TrelloError(f"Unsupported sheet type: {path.suffix}")


def _flatten_preview_text(preview: dict[str, Any]) -> str:
    chunks = []
    for sheet, rows in preview.get("sheets", {}).items():
        chunks.append(str(sheet))
        for row in rows:
            chunks.append(" | ".join(str(v) for v in row if str(v).strip()))
    return "\n".join(chunks)


def _extract_address_candidates(text: str) -> list[str]:
    candidates = []
    for line in text.splitlines():
        s = re.sub(r"\s+", " ", line).strip(" -:\t")
        if not s:
            continue
        has_number = bool(re.search(r"\b\d{2,6}\b", s))
        has_street_word = bool(re.search(r"\b(st|street|rd|road|dr|drive|ave|avenue|ln|lane|ct|court|cv|cove|cir|circle|way|pkwy|parkway|blvd|trail|terrace)\b", s, re.I))
        if has_number and has_street_word:
            candidates.append(s[:220])
    deduped = []
    for item in candidates:
        if item.lower() not in {x.lower() for x in deduped}:
            deduped.append(item)
    return deduped[:10]


def _searchable_fragment(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def _match_tokens(text: str) -> set[str]:
    tokens = set()
    for token in re.findall(r"[A-Za-z0-9]+", text.lower()):
        if len(token) >= 3 and token not in MATCH_STOPWORDS:
            tokens.add(token)
            if token == "bills":
                tokens.add("bill")
    return tokens


def _score_text(tokens: set[str], text: str) -> int:
    if not tokens:
        return 0
    haystack = _match_tokens(text)
    return len(tokens & haystack)


def _run_rag(args: list[str], timeout: int = 180) -> dict[str, Any]:
    if not RAG_CLI.exists():
        raise TrelloError(f"RAG CLI not found: {RAG_CLI}")
    env = os.environ.copy()
    env.setdefault("RAG_LOCAL_API_RETRY_ATTEMPTS", "1")
    try:
        result = subprocess.run(
            [str(RAG_CLI), *args, "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise TrelloError(f"RAG command timed out after {timeout}s: {' '.join(args)}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise TrelloError(f"RAG command failed: {detail[:500]}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise TrelloError(f"RAG command returned non-JSON output: {result.stdout[:500]}") from exc
    if not payload.get("ok", False):
        raise TrelloError(f"RAG command returned errors: {payload.get('errors')}")
    return payload


def _pool_record_kind(result: dict[str, Any]) -> str:
    path = str(result.get("path") or "").lower()
    text = str(result.get("text") or "").lower()
    if "/drive-bills/" in path or "record kind: bill" in text:
        return "bill"
    if "/drive-work-orders/" in path or "record kind: work_order" in text:
        return "work_order"
    return "unknown"


def _pool_record_year(result: dict[str, Any]) -> str | None:
    path = str(result.get("path") or "")
    text = str(result.get("text") or "")
    for value in (path, text):
        match = re.search(r"\b(20\d{2})\b", value)
        if match:
            return match.group(1)
    return None


def _pool_record_summary(result: dict[str, Any], excerpt_chars: int = 1400) -> dict[str, Any]:
    text = str(result.get("text") or "")
    return {
        "kind": _pool_record_kind(result),
        "year": _pool_record_year(result),
        "score": result.get("score"),
        "distance": result.get("distance"),
        "file": result.get("file"),
        "path": result.get("path"),
        "chunk": result.get("chunk"),
        "text_excerpt": text[: max(200, min(excerpt_chars, 4000))],
    }


def _lexical_pool_record_search(query: str, record_kind: str = "any", max_results: int = 20) -> list[dict[str, Any]]:
    if not POOL_JOBS_ROOT.exists():
        return []
    kind = (record_kind or "any").strip().lower()
    tokens = _match_tokens(query)
    if not tokens:
        return []
    candidates = []
    for path in POOL_JOBS_ROOT.rglob("*.md"):
        result = {
            "text": path.read_text(encoding="utf-8", errors="ignore"),
            "file": path.name,
            "path": str(path),
            "chunk": "1/1",
        }
        result_kind = _pool_record_kind(result)
        if kind != "any" and result_kind != kind:
            continue
        haystack = _match_tokens(f"{path.name}\n{result['text']}")
        overlap = tokens & haystack
        if not overlap:
            continue
        score = min(0.91, 0.70 + len(overlap) * 0.06)
        result["score"] = score
        result["distance"] = round(max(0.0, 1.0 - score), 6)
        result["lexical_overlap"] = sorted(overlap)
        candidates.append(result)
    candidates.sort(key=lambda item: (len(item.get("lexical_overlap") or []), item.get("score") or 0.0), reverse=True)
    return [_pool_record_summary(item) for item in candidates[: max(1, min(max_results, 100))]]


def _label_names(card: dict[str, Any]) -> list[str]:
    names = []
    for label in card.get("labels") or []:
        value = label.get("name") or label.get("color")
        if value:
            names.append(str(value))
    return names


def _card_record_search_text(
    card: dict[str, Any],
    *,
    list_name: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> str:
    parts = [
        str(card.get("name") or ""),
        str(card.get("desc") or ""),
        " ".join(_label_names(card)),
        str(list_name or ""),
    ]
    for candidate in _extract_address_candidates("\n".join(parts)):
        parts.append(candidate)
    for item in attachments or []:
        name = str(item.get("name") or "")
        ext = str(item.get("extension") or "")
        if name:
            parts.append(name)
        if ext:
            parts.append(ext)

    seen = set()
    compact = []
    for part in parts:
        clean = _searchable_fragment(part)
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        compact.append(clean)
    return " ".join(compact)[:1200]


def _card_name_anchor_tokens(card: dict[str, Any]) -> set[str]:
    name = _searchable_fragment(card.get("name") or "")
    head = re.split(r"\s+[-–]\s+", name, maxsplit=1)[0]
    ordered = [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]+", head)
        if len(token) >= 3 and token.lower() not in MATCH_STOPWORDS
    ]
    if not ordered:
        return set()
    if len(ordered) == 1:
        return {ordered[0]}
    return {ordered[-1]}


def _strong_card_tokens(card: dict[str, Any], query: str) -> set[str]:
    name = _searchable_fragment(card.get("name") or "")
    head = re.split(r"\s+[-–]\s+", name, maxsplit=1)[0]
    tokens = _match_tokens(head)
    for candidate in _extract_address_candidates(query):
        tokens.update(_match_tokens(candidate))
    return tokens


def _record_match_detail(
    card_tokens: set[str],
    record: dict[str, Any],
    *,
    strong_tokens: set[str] | None = None,
    name_anchor_tokens: set[str] | None = None,
) -> dict[str, Any]:
    searchable = " ".join(
        str(record.get(key) or "")
        for key in ("file", "path", "text_excerpt")
    )
    record_tokens = _match_tokens(searchable)
    overlap = sorted(card_tokens & record_tokens)
    strong_overlap = sorted((strong_tokens or set()) & record_tokens)
    name_anchor_overlap = sorted((name_anchor_tokens or set()) & record_tokens)
    score = float(record.get("score") or 0.0)
    overlap_count = len(overlap)
    strong_overlap_count = len(strong_overlap)
    has_name_anchor = not name_anchor_tokens or bool(name_anchor_overlap)

    if has_name_anchor and strong_overlap_count >= 3 and score >= 0.78:
        confidence = "exact"
        reason = "name_anchor_plus_multiple_specific_card_tokens"
    elif has_name_anchor and strong_overlap_count >= 2 and score >= 0.84:
        confidence = "exact"
        reason = "name_anchor_and_high_score"
    elif has_name_anchor and strong_overlap_count >= 1 and score >= 0.72:
        confidence = "likely"
        reason = "name_anchor_overlap"
    elif strong_overlap_count >= 2 and score >= 0.72:
        confidence = "review"
        reason = "specific_card_tokens_without_name_anchor"
    elif score >= 0.78 and overlap_count >= 2:
        confidence = "review"
        reason = "good_score_but_missing_name_anchor"
    else:
        confidence = "weak"
        reason = "low_score_or_low_overlap"

    return {
        "confidence": confidence,
        "reason": reason,
        "overlap_tokens": overlap[:20],
        "overlap_count": overlap_count,
        "strong_overlap_tokens": strong_overlap[:20],
        "strong_overlap_count": strong_overlap_count,
        "name_anchor_tokens": sorted(name_anchor_tokens or []),
        "name_anchor_overlap": name_anchor_overlap[:20],
        "score": score,
    }


def _confidence_rank(value: str) -> int:
    return {"exact": 4, "likely": 3, "review": 2, "weak": 1, "no_match": 0}.get(value, 0)


def _record_candidate_preview(candidate: dict[str, Any], excerpt_chars: int = 360) -> dict[str, Any]:
    match = candidate.get("match") or {}
    excerpt = str(candidate.get("text_excerpt") or "")
    return {
        "kind": candidate.get("kind"),
        "year": candidate.get("year"),
        "confidence": match.get("confidence"),
        "reason": match.get("reason"),
        "score": candidate.get("score"),
        "file": candidate.get("file"),
        "path": candidate.get("path"),
        "retrieval_sources": candidate.get("retrieval_sources") or [],
        "overlap_tokens": match.get("overlap_tokens") or [],
        "text_excerpt": excerpt[: max(120, min(excerpt_chars, 1200))],
    }


def _empty_match_buckets() -> dict[str, list[dict[str, Any]]]:
    return {"exact": [], "likely": [], "review": [], "weak": [], "no_match": []}


def _dms_to_decimal(values: Any, ref: str) -> float | None:
    try:
        deg, minute, sec = values
        decimal = float(deg) + float(minute) / 60 + float(sec) / 3600
        return -decimal if ref in {"S", "W"} else decimal
    except Exception:
        return None


def _photo_metadata(path: Path) -> dict[str, Any]:
    from PIL import ExifTags, Image

    with Image.open(path) as img:
        exif = img.getexif()
        if not exif:
            return {"path": str(path), "has_gps": False, "taken_at": None}
        named = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        gps_raw = named.get("GPSInfo")
        gps = {}
        if gps_raw:
            gps = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_raw.items()}
        lat = _dms_to_decimal(gps.get("GPSLatitude"), gps.get("GPSLatitudeRef")) if gps else None
        lng = _dms_to_decimal(gps.get("GPSLongitude"), gps.get("GPSLongitudeRef")) if gps else None
        return {
            "path": str(path),
            "filename": path.name,
            "size": path.stat().st_size,
            "sha256": _sha256(path),
            "taken_at": named.get("DateTimeOriginal") or named.get("DateTime"),
            "latitude": lat,
            "longitude": lng,
            "has_gps": lat is not None and lng is not None,
        }


def _distance_ft(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_ft = 20902231.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return radius_ft * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@mcp.tool()
def trello_credential_diagnostics(try_onepassword: bool = False) -> dict[str, Any]:
    """Report non-secret Trello credential source availability.

    By default this does not call 1Password, so it cannot hang on an auth
    prompt. Set try_onepassword=True for a bounded, value-redacted field check.
    """
    summary = _credential_source_summary(try_op=try_onepassword)
    complete_sources = []
    if summary["environment"]["complete"]:
        complete_sources.append("environment")
    if summary["profile"]["complete"]:
        complete_sources.append("profile")
    if summary["onepassword"].get("complete"):
        complete_sources.append("onepassword")
    return {
        "ok": bool(complete_sources) or not try_onepassword,
        "complete_sources": complete_sources,
        "recommendation": _credential_recommendation(summary, try_op=try_onepassword),
        "diagnostics": summary,
        "secrets_returned": False,
    }


@mcp.tool()
def trello_config_diagnostics() -> dict[str, Any]:
    """Report non-secret local Trello MCP config status."""
    config = _local_trello_config()
    expected_keys = {
        "memphis": "boardId",
        "legacy_memphis": "legacyMemphisBoardId",
        "artesian": "artesianBoardId",
    }
    board_sources = {}
    for alias, key in expected_keys.items():
        value = str(config.get(key) or "").strip()
        board_sources[alias] = {
            "config_key": key,
            "present": bool(value),
            "chars": len(value),
            "active_board_id": _board_id(alias),
            "source": str(LOCAL_TRELLO_CONFIG_PATH) if value else "built_in_default",
        }
    return {
        "ok": True,
        "path": str(LOCAL_TRELLO_CONFIG_PATH),
        "exists": LOCAL_TRELLO_CONFIG_PATH.exists(),
        "mode": oct(LOCAL_TRELLO_CONFIG_PATH.stat().st_mode & 0o777) if LOCAL_TRELLO_CONFIG_PATH.exists() else None,
        "contains_credentials": any(
            key.lower() in {"key", "token", "apikey", "apitoken", "api_key", "api_token"}
            for key in config.keys()
        ),
        "board_sources": board_sources,
        "secrets_returned": False,
    }


@mcp.tool()
def trello_runtime_diagnostics(include_live_health: bool = False) -> dict[str, Any]:
    """Report non-secret Trello MCP runtime readiness.

    This is intended as the first operator check in a fresh MCP session. It
    does not call Trello unless include_live_health is true.
    """
    credential_status = trello_credential_diagnostics(False)
    config_status = trello_config_diagnostics()
    runtime_env = _runtime_environment_summary()
    launcher_status = _launcher_config_summary()
    complete_sources = credential_status.get("complete_sources") or []
    blockers = []

    if not runtime_env["complete"] and not complete_sources:
        blockers.append("no_complete_credential_source")
    if not launcher_status["launcher"]["exists"]:
        blockers.append("launcher_missing")
    elif not launcher_status["launcher"]["executable"]:
        blockers.append("launcher_not_executable")
    if not launcher_status["codex_config"]["references_launcher"]:
        blockers.append("codex_config_not_pointing_at_launcher")
    if not launcher_status["claude_config"]["references_launcher"]:
        blockers.append("claude_config_not_pointing_at_launcher")
    if config_status.get("contains_credentials"):
        blockers.append("local_board_config_contains_credential_like_keys")

    live_health: dict[str, Any] = {
        "checked": False,
        "ok": None,
        "error": None,
    }
    if include_live_health:
        try:
            health = trello_health()
            live_health = {
                "checked": True,
                "ok": bool(health.get("ok")),
                "member_present": bool(health.get("member")),
                "known_board_aliases": sorted((health.get("known_boards") or {}).keys()),
            }
        except Exception as exc:
            live_health = {
                "checked": True,
                "ok": False,
                "error": str(exc)[:500],
            }

    recommendation = credential_status.get("recommendation")
    if include_live_health and live_health.get("checked") and not live_health.get("ok"):
        error_text = str(live_health.get("error") or "").lower()
        if "invalid key" in error_text:
            recommendation = (
                "Trello credentials resolve into the runtime, but Trello rejects the API key. "
                "Update the Trello API key/token source before running live packet tools."
            )
        elif "invalid token" in error_text:
            recommendation = (
                "Trello credentials resolve into the runtime, but Trello rejects the token. "
                "Update the Trello API token source before running live packet tools."
            )

    return {
        "ok": not blockers and (not include_live_health or bool(live_health.get("ok"))),
        "blockers": blockers,
        "credential_sources": complete_sources,
        "runtime_environment": runtime_env,
        "launcher": launcher_status,
        "board_config": config_status,
        "live_health": live_health,
        "recommendation": recommendation,
        "safety": {
            "secrets_returned": False,
            "trello_writes": False,
            "google_drive_writes": False,
            "pi5_writes": False,
            "live_trello_read": bool(include_live_health),
        },
    }


@mcp.tool()
def trello_health() -> dict[str, Any]:
    """Verify Trello credentials by reading the authenticated member profile."""
    member = _request("GET", "members/me", params={"fields": "id,username,fullName"})
    return {
        "ok": True,
        "member": {k: member.get(k) for k in ("id", "username", "fullName")},
        "known_boards": _configured_boards(),
    }


@mcp.tool()
def list_known_boards() -> dict[str, Any]:
    """List Stephen's built-in board aliases and IDs."""
    return _configured_boards()


@mcp.tool()
def list_boards(filter: str = "open") -> list[dict[str, Any]]:
    """List boards visible to the authenticated Trello account."""
    boards = _request("GET", "members/me/boards", params={"filter": filter, "fields": "id,name,url,closed"})
    return [{k: b.get(k) for k in ("id", "name", "url", "closed")} for b in boards]


@mcp.tool()
def get_board(board: str = "memphis") -> dict[str, Any]:
    """Read a board by alias ('memphis' or 'artesian') or raw board ID."""
    return _request("GET", f"boards/{_board_id(board)}", params={"fields": "id,name,url,closed,dateLastActivity"})


@mcp.tool()
def get_lists(board: str = "memphis", filter: str = "open") -> list[dict[str, Any]]:
    """List Trello lists on a board."""
    lists = _request("GET", f"boards/{_board_id(board)}/lists", params={"filter": filter, "fields": "id,name,closed,pos"})
    return [{k: item.get(k) for k in ("id", "name", "closed", "pos")} for item in lists]


@mcp.tool()
def get_labels(board: str = "memphis") -> list[dict[str, Any]]:
    """List labels on a board."""
    labels = _request("GET", f"boards/{_board_id(board)}/labels", params={"fields": "id,name,color"})
    return [{k: label.get(k) for k in ("id", "name", "color")} for label in labels]


@mcp.tool()
def get_cards(board: str = "memphis", filter: str = "open", limit: int = 50) -> list[dict[str, Any]]:
    """List cards on a board, summarized for scanning."""
    cards = _request(
        "GET",
        f"boards/{_board_id(board)}/cards",
        params={"filter": filter, "fields": "id,name,shortUrl,idList,closed,due,labels"},
    )
    return [_card_summary(card) for card in cards[: max(1, min(limit, 500))]]


@mcp.tool()
def get_cards_in_list(list_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """List cards in a Trello list."""
    cards = _request(
        "GET",
        f"lists/{list_id}/cards",
        params={"fields": "id,name,shortUrl,idList,closed,due,labels"},
    )
    return [_card_summary(card) for card in cards[: max(1, min(limit, 500))]]


@mcp.tool()
def get_card(card_id: str) -> dict[str, Any]:
    """Read one card with useful fields."""
    return _request(
        "GET",
        f"cards/{card_id}",
        params={"fields": "id,name,desc,shortUrl,idList,idBoard,closed,due,labels,dateLastActivity"},
    )


@mcp.tool()
def index_trello_job_cards(board: str = "memphis", limit: int = 500) -> list[dict[str, Any]]:
    """Index cards with lightweight address candidates for artifact matching."""
    cards = _request(
        "GET",
        f"boards/{_board_id(board)}/cards",
        params={"filter": "open", "fields": "id,name,desc,shortUrl,idList,idBoard,closed,due,dateLastActivity"},
    )
    indexed = []
    for card in cards[: max(1, min(limit, 1000))]:
        text = f"{card.get('name', '')}\n{card.get('desc', '')}"
        indexed.append(
            {
                "id": card.get("id"),
                "name": card.get("name"),
                "shortUrl": card.get("shortUrl"),
                "idList": card.get("idList"),
                "dateLastActivity": card.get("dateLastActivity"),
                "address_candidates": _extract_address_candidates(text),
            }
        )
    return indexed


@mcp.tool()
def search_cards(query: str, board: str = "memphis", limit: int = 25) -> list[dict[str, Any]]:
    """Search cards on one board by name or description text."""
    q = (query or "").strip().lower()
    if not q:
        return []
    cards = _request(
        "GET",
        f"boards/{_board_id(board)}/cards",
        params={"filter": "open", "fields": "id,name,desc,shortUrl,idList,closed,due,labels"},
    )
    hits = [card for card in cards if q in (card.get("name", "") + "\n" + card.get("desc", "")).lower()]
    return [_card_summary(card) for card in hits[: max(1, min(limit, 100))]]


@mcp.tool()
def create_card(list_id: str, name: str, desc: str = "", due: str | None = None, pos: str = "bottom") -> dict[str, Any]:
    """Create a card in a Trello list."""
    return _request("POST", "cards", params={"idList": list_id, "name": name, "desc": desc, "due": due, "pos": pos})


@mcp.tool()
def update_card(card_id: str, name: str | None = None, desc: str | None = None, due: str | None = None) -> dict[str, Any]:
    """Update basic card fields. Omitted fields are left unchanged."""
    return _request("PUT", f"cards/{card_id}", params={"name": name, "desc": desc, "due": due})


@mcp.tool()
def move_card(card_id: str, list_id: str, pos: str = "bottom") -> dict[str, Any]:
    """Move a card to another list."""
    return _request("PUT", f"cards/{card_id}", params={"idList": list_id, "pos": pos})


@mcp.tool()
def archive_card(card_id: str) -> dict[str, Any]:
    """Archive a card instead of deleting it."""
    return _request("PUT", f"cards/{card_id}", params={"closed": "true"})


@mcp.tool()
def add_comment(card_id: str, text: str) -> dict[str, Any]:
    """Add a comment to a Trello card."""
    return _request("POST", f"cards/{card_id}/actions/comments", params={"text": text})


@mcp.tool()
def add_checklist(card_id: str, name: str) -> dict[str, Any]:
    """Add a checklist to a Trello card."""
    return _request("POST", "checklists", params={"idCard": card_id, "name": name})


@mcp.tool()
def add_checklist_item(checklist_id: str, name: str, checked: bool = False) -> dict[str, Any]:
    """Add an item to a Trello checklist."""
    return _request(
        "POST",
        f"checklists/{checklist_id}/checkItems",
        params={"name": name, "checked": str(checked).lower()},
    )


@mcp.tool()
def add_attachment_url(card_id: str, url: str, name: str | None = None) -> dict[str, Any]:
    """Attach a URL to a Trello card."""
    return _request("POST", f"cards/{card_id}/attachments", params={"url": url, "name": name})


@mcp.tool()
def get_card_attachments(card_id: str, filter: str = "false") -> list[dict[str, Any]]:
    """List attachments on a Trello card."""
    attachments = _request(
        "GET",
        f"cards/{card_id}/attachments",
        params={"filter": filter, "fields": "id,name,url,bytes,date,mimeType,isUpload,previews"},
    )
    return [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "url": item.get("url"),
            "bytes": item.get("bytes"),
            "date": item.get("date"),
            "mimeType": item.get("mimeType"),
            "isUpload": item.get("isUpload"),
            "extension": Path(item.get("name") or "").suffix.lower(),
            "preview_count": len(item.get("previews") or []),
        }
        for item in attachments
    ]


@mcp.tool()
def index_trello_sheet_attachments(board: str = "memphis", limit_cards: int = 500) -> list[dict[str, Any]]:
    """Find XLS/XLSX/CSV attachments already present on board cards."""
    cards = _request(
        "GET",
        f"boards/{_board_id(board)}/cards",
        params={"filter": "open", "fields": "id,name,shortUrl,idList"},
    )
    hits = []
    for card in cards[: max(1, min(limit_cards, 1000))]:
        attachments = get_card_attachments(card["id"])
        for item in attachments:
            if item["extension"] in SUPPORTED_SHEET_EXTENSIONS:
                hits.append(
                    {
                        "card_id": card.get("id"),
                        "card_name": card.get("name"),
                        "card_url": card.get("shortUrl"),
                        "list_id": card.get("idList"),
                        "attachment": item,
                    }
                )
    return hits


@mcp.tool()
def audit_board_artifacts(board: str = "memphis", include_complete: bool = False, limit_cards: int = 500) -> dict[str, Any]:
    """Read-only board artifact audit for cards, addresses, and sheet attachments.

    Defaults to active/non-Complete lists so the live workflow is quick to audit.
    Set include_complete=True for a slower historical/backlog audit.
    """
    board_info = get_board(board)
    lists = get_lists(board)
    list_names = {item["id"]: item["name"] for item in lists}
    cards = _request(
        "GET",
        f"boards/{_board_id(board)}/cards",
        params={"filter": "open", "fields": "id,name,desc,shortUrl,idList,dateLastActivity"},
    )
    if not include_complete:
        cards = [card for card in cards if list_names.get(card.get("idList")) != "Complete"]
    cards = cards[: max(1, min(limit_cards, 1000))]

    list_summary: dict[str, dict[str, Any]] = {}
    extension_counts: dict[str, int] = {}
    cards_with_address = 0
    cards_with_sheets = 0
    cards_without_sheets = 0
    cards_without_address = 0
    sample_gaps = []

    for card in cards:
        list_name = list_names.get(card.get("idList"), "UNKNOWN")
        row = list_summary.setdefault(
            list_name,
            {
                "cards": 0,
                "cards_with_address_candidates": 0,
                "cards_with_sheet_attachments": 0,
                "sheet_attachments": 0,
            },
        )
        row["cards"] += 1

        address_candidates = _extract_address_candidates(f"{card.get('name', '')}\n{card.get('desc', '')}")
        if address_candidates:
            cards_with_address += 1
            row["cards_with_address_candidates"] += 1
        else:
            cards_without_address += 1

        attachments = get_card_attachments(card["id"])
        sheet_attachments = [item for item in attachments if item["extension"] in SUPPORTED_SHEET_EXTENSIONS]
        if sheet_attachments:
            cards_with_sheets += 1
            row["cards_with_sheet_attachments"] += 1
            row["sheet_attachments"] += len(sheet_attachments)
            for item in sheet_attachments:
                ext = item["extension"] or "unknown"
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
        else:
            cards_without_sheets += 1
            if len(sample_gaps) < 12:
                sample_gaps.append(
                    {
                        "card_id": card.get("id"),
                        "card_url": card.get("shortUrl"),
                        "list": list_name,
                        "has_address_candidates": bool(address_candidates),
                    }
                )

    return {
        "board": {k: board_info.get(k) for k in ("id", "name", "url", "closed", "dateLastActivity")},
        "scope": {
            "include_complete": include_complete,
            "cards_audited": len(cards),
            "limit_cards": limit_cards,
        },
        "summary": {
            "cards_with_address_candidates": cards_with_address,
            "cards_without_address_candidates": cards_without_address,
            "cards_with_sheet_attachments": cards_with_sheets,
            "cards_without_sheet_attachments": cards_without_sheets,
            "sheet_attachments": sum(extension_counts.values()),
            "sheet_extensions": extension_counts,
        },
        "lists": list_summary,
        "sample_cards_without_sheet_attachments": sample_gaps,
    }


def _board_snapshot(
    board: str = "memphis",
    *,
    include_complete: bool = True,
    limit_cards: int = 1000,
    sample_cards_per_list: int = 8,
) -> dict[str, Any]:
    board_info = get_board(board)
    lists = get_lists(board, filter="all" if include_complete else "open")
    labels = get_labels(board)
    list_by_id = {item["id"]: item for item in lists}
    cards = _request(
        "GET",
        f"boards/{_board_id(board)}/cards",
        params={
            "filter": "all" if include_complete else "open",
            "fields": "id,name,shortUrl,idList,closed,due,dateLastActivity,labels,badges",
        },
    )
    if not include_complete:
        cards = [card for card in cards if not card.get("closed") and not list_by_id.get(card.get("idList"), {}).get("closed")]
    cards = cards[: max(1, min(int(limit_cards), 2000))]

    by_list: dict[str, dict[str, Any]] = {}
    label_counts: dict[str, int] = {}
    total_attachments = 0
    total_check_items = 0
    total_check_items_checked = 0
    due_cards = 0
    closed_cards = 0

    for item in lists:
        by_list[item["name"]] = {
            "list_id": item.get("id"),
            "closed": bool(item.get("closed")),
            "cards": 0,
            "open_cards": 0,
            "closed_cards": 0,
            "due_cards": 0,
            "attachment_count": 0,
            "check_items": 0,
            "check_items_checked": 0,
            "sample_cards": [],
        }

    for card in cards:
        list_info = list_by_id.get(card.get("idList")) or {}
        list_name = list_info.get("name") or "UNKNOWN"
        row = by_list.setdefault(
            list_name,
            {
                "list_id": card.get("idList"),
                "closed": bool(list_info.get("closed")),
                "cards": 0,
                "open_cards": 0,
                "closed_cards": 0,
                "due_cards": 0,
                "attachment_count": 0,
                "check_items": 0,
                "check_items_checked": 0,
                "sample_cards": [],
            },
        )
        badges = card.get("badges") or {}
        attachment_count = int(badges.get("attachments") or 0)
        check_items = int(badges.get("checkItems") or 0)
        check_items_checked = int(badges.get("checkItemsChecked") or 0)
        is_closed = bool(card.get("closed"))
        has_due = bool(card.get("due"))

        row["cards"] += 1
        row["closed_cards"] += 1 if is_closed else 0
        row["open_cards"] += 0 if is_closed else 1
        row["due_cards"] += 1 if has_due else 0
        row["attachment_count"] += attachment_count
        row["check_items"] += check_items
        row["check_items_checked"] += check_items_checked
        total_attachments += attachment_count
        total_check_items += check_items
        total_check_items_checked += check_items_checked
        due_cards += 1 if has_due else 0
        closed_cards += 1 if is_closed else 0

        labels_on_card = _label_names(card)
        for label in labels_on_card:
            label_counts[label] = label_counts.get(label, 0) + 1

        if len(row["sample_cards"]) < max(0, min(int(sample_cards_per_list), 25)):
            row["sample_cards"].append(
                {
                    "id": card.get("id"),
                    "name": card.get("name"),
                    "url": card.get("shortUrl"),
                    "closed": is_closed,
                    "due": card.get("due"),
                    "dateLastActivity": card.get("dateLastActivity"),
                    "labels": labels_on_card,
                    "attachment_count": attachment_count,
                    "check_items": check_items,
                    "check_items_checked": check_items_checked,
                }
            )

    return {
        "ok": True,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "board_alias": board,
        "board": {k: board_info.get(k) for k in ("id", "name", "url", "closed", "dateLastActivity")},
        "scope": {
            "include_complete": include_complete,
            "cards_seen": len(cards),
            "limit_cards": limit_cards,
            "sample_cards_per_list": sample_cards_per_list,
        },
        "summary": {
            "lists": len(lists),
            "labels": len(labels),
            "cards": len(cards),
            "open_cards": len(cards) - closed_cards,
            "closed_cards": closed_cards,
            "due_cards": due_cards,
            "attachment_count": total_attachments,
            "check_items": total_check_items,
            "check_items_checked": total_check_items_checked,
            "label_counts": dict(sorted(label_counts.items())),
        },
        "labels": labels,
        "lists": by_list,
        "safety": {
            "read_only": True,
            "trello_writes": False,
            "google_drive_writes": False,
            "auto_attach": False,
        },
    }


def _format_board_snapshot(snapshot: dict[str, Any]) -> str:
    board = snapshot.get("board") or {}
    summary = snapshot.get("summary") or {}
    scope = snapshot.get("scope") or {}
    lines = [
        f"# Board Snapshot - {board.get('name') or 'UNKNOWN'}",
        "",
        f"- Generated: {snapshot.get('generated_at') or datetime.now().isoformat(timespec='seconds')}",
        f"- Board URL: {board.get('url') or 'UNKNOWN'}",
        f"- Board ID: {board.get('id') or 'UNKNOWN'}",
        f"- Include complete/closed: {scope.get('include_complete')}",
        f"- Cards seen: {scope.get('cards_seen')} of limit {scope.get('limit_cards')}",
        "",
        "## Summary",
        "",
        f"- Lists: {summary.get('lists', 0)}",
        f"- Labels: {summary.get('labels', 0)}",
        f"- Cards: {summary.get('cards', 0)}",
        f"- Open cards: {summary.get('open_cards', 0)}",
        f"- Closed cards: {summary.get('closed_cards', 0)}",
        f"- Due cards: {summary.get('due_cards', 0)}",
        f"- Attachments: {summary.get('attachment_count', 0)}",
        f"- Checklist items: {summary.get('check_items_checked', 0)} checked of {summary.get('check_items', 0)}",
        "",
        "## Labels",
        "",
    ]

    label_counts = summary.get("label_counts") or {}
    if label_counts:
        for label, count in label_counts.items():
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- None")

    lines.extend(["", "## Lists", ""])
    for list_name, row in (snapshot.get("lists") or {}).items():
        lines.append(f"### {list_name}")
        lines.append("")
        lines.append(f"- Cards: {row.get('cards', 0)}")
        lines.append(f"- Open: {row.get('open_cards', 0)}")
        lines.append(f"- Closed: {row.get('closed_cards', 0)}")
        lines.append(f"- Due: {row.get('due_cards', 0)}")
        lines.append(f"- Attachments: {row.get('attachment_count', 0)}")
        lines.append(f"- Checklist items: {row.get('check_items_checked', 0)} checked of {row.get('check_items', 0)}")
        samples = row.get("sample_cards") or []
        if samples:
            lines.append("")
            lines.append("Sample cards:")
            for card in samples:
                labels = ", ".join(card.get("labels") or [])
                detail = []
                if labels:
                    detail.append(f"labels: {labels}")
                if card.get("due"):
                    detail.append(f"due: {card.get('due')}")
                if card.get("attachment_count"):
                    detail.append(f"attachments: {card.get('attachment_count')}")
                suffix = f" ({'; '.join(detail)})" if detail else ""
                lines.append(f"- {card.get('name') or 'Untitled'} - {card.get('url') or card.get('id')}{suffix}")
        lines.append("")

    lines.extend(
        [
            "## Safety",
            "",
            "- Trello writes: false",
            "- Google Drive writes: false",
            "- Auto-attach: false",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _load_board_snapshot(path: str) -> dict[str, Any]:
    snapshot_path = Path(path).expanduser()
    if not snapshot_path.exists():
        raise TrelloError(f"Board snapshot JSON not found: {snapshot_path}")
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TrelloError(f"Board snapshot JSON is invalid: {snapshot_path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("summary"), dict) or not isinstance(payload.get("lists"), dict):
        raise TrelloError("Board snapshot JSON must contain summary and lists objects")
    return payload


def _numeric_delta(primary: dict[str, Any], comparison: dict[str, Any], keys: list[str]) -> dict[str, dict[str, int]]:
    deltas = {}
    for key in keys:
        left = int(primary.get(key) or 0)
        right = int(comparison.get(key) or 0)
        deltas[key] = {"primary": left, "comparison": right, "delta": left - right}
    return deltas


def _sample_card_names(snapshot: dict[str, Any]) -> set[str]:
    names = set()
    for row in (snapshot.get("lists") or {}).values():
        for card in row.get("sample_cards") or []:
            name = str(card.get("name") or "").strip()
            if name:
                names.add(name)
    return names


def _compare_board_snapshots(primary: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    primary_summary = primary.get("summary") or {}
    comparison_summary = comparison.get("summary") or {}
    primary_lists = primary.get("lists") or {}
    comparison_lists = comparison.get("lists") or {}
    primary_labels = primary_summary.get("label_counts") or {}
    comparison_labels = comparison_summary.get("label_counts") or {}
    primary_sample_names = _sample_card_names(primary)
    comparison_sample_names = _sample_card_names(comparison)
    numeric_keys = [
        "lists",
        "labels",
        "cards",
        "open_cards",
        "closed_cards",
        "due_cards",
        "attachment_count",
        "check_items",
        "check_items_checked",
    ]

    list_deltas = {}
    for list_name in sorted(set(primary_lists) | set(comparison_lists)):
        left = primary_lists.get(list_name) or {}
        right = comparison_lists.get(list_name) or {}
        list_deltas[list_name] = _numeric_delta(
            left,
            right,
            ["cards", "open_cards", "closed_cards", "due_cards", "attachment_count", "check_items", "check_items_checked"],
        )

    label_deltas = {}
    for label in sorted(set(primary_labels) | set(comparison_labels)):
        left = int(primary_labels.get(label) or 0)
        right = int(comparison_labels.get(label) or 0)
        label_deltas[label] = {"primary": left, "comparison": right, "delta": left - right}

    warnings = []
    if set(primary_lists) != set(comparison_lists):
        warnings.append("list_names_differ")
    if primary_summary.get("cards") != comparison_summary.get("cards"):
        warnings.append("card_count_differs")
    if primary_summary.get("attachment_count") != comparison_summary.get("attachment_count"):
        warnings.append("attachment_count_differs")
    if primary_summary.get("check_items") != comparison_summary.get("check_items"):
        warnings.append("checklist_item_count_differs")

    return {
        "ok": True,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "primary_board": primary.get("board"),
        "comparison_board": comparison.get("board"),
        "summary_deltas": _numeric_delta(primary_summary, comparison_summary, numeric_keys),
        "lists": {
            "primary_only": sorted(set(primary_lists) - set(comparison_lists)),
            "comparison_only": sorted(set(comparison_lists) - set(primary_lists)),
            "deltas": list_deltas,
        },
        "labels": {
            "primary_only": sorted(set(primary_labels) - set(comparison_labels)),
            "comparison_only": sorted(set(comparison_labels) - set(primary_labels)),
            "deltas": label_deltas,
        },
        "sample_cards": {
            "primary_only": sorted(primary_sample_names - comparison_sample_names),
            "comparison_only": sorted(comparison_sample_names - primary_sample_names),
            "overlap": sorted(primary_sample_names & comparison_sample_names),
            "note": "Sample-card comparison is limited to cards captured in each snapshot sample.",
        },
        "warnings": warnings,
        "safety": {
            "local_file_read": True,
            "local_file_write": False,
            "trello_writes": False,
            "google_drive_writes": False,
            "live_trello_read": False,
        },
    }


def _format_board_snapshot_comparison(comparison: dict[str, Any]) -> str:
    primary = comparison.get("primary_board") or {}
    other = comparison.get("comparison_board") or {}
    lines = [
        f"# Board Snapshot Comparison - {primary.get('name') or 'Primary'} vs {other.get('name') or 'Comparison'}",
        "",
        f"- Generated: {comparison.get('generated_at') or datetime.now().isoformat(timespec='seconds')}",
        f"- Primary: {primary.get('name') or 'UNKNOWN'} ({primary.get('url') or primary.get('id') or 'UNKNOWN'})",
        f"- Comparison: {other.get('name') or 'UNKNOWN'} ({other.get('url') or other.get('id') or 'UNKNOWN'})",
        "",
        "## Summary Deltas",
        "",
    ]
    for key, row in (comparison.get("summary_deltas") or {}).items():
        lines.append(f"- {key}: primary {row.get('primary', 0)}, comparison {row.get('comparison', 0)}, delta {row.get('delta', 0)}")

    warnings = comparison.get("warnings") or []
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None")

    lists = comparison.get("lists") or {}
    lines.extend(["", "## Lists", ""])
    primary_only = lists.get("primary_only") or []
    comparison_only = lists.get("comparison_only") or []
    lines.append(f"- Primary-only lists: {', '.join(primary_only) if primary_only else 'none'}")
    lines.append(f"- Comparison-only lists: {', '.join(comparison_only) if comparison_only else 'none'}")
    lines.append("")
    for list_name, deltas in (lists.get("deltas") or {}).items():
        card_delta = (deltas.get("cards") or {}).get("delta", 0)
        attachment_delta = (deltas.get("attachment_count") or {}).get("delta", 0)
        checklist_delta = (deltas.get("check_items") or {}).get("delta", 0)
        lines.append(f"- {list_name}: cards delta {card_delta}, attachments delta {attachment_delta}, checklist items delta {checklist_delta}")

    labels = comparison.get("labels") or {}
    lines.extend(["", "## Labels", ""])
    lines.append(f"- Primary-only labels: {', '.join(labels.get('primary_only') or []) or 'none'}")
    lines.append(f"- Comparison-only labels: {', '.join(labels.get('comparison_only') or []) or 'none'}")

    samples = comparison.get("sample_cards") or {}
    lines.extend(["", "## Sample Cards", ""])
    lines.append(f"- Primary-only sample cards: {len(samples.get('primary_only') or [])}")
    lines.append(f"- Comparison-only sample cards: {len(samples.get('comparison_only') or [])}")
    lines.append(f"- Overlap sample cards: {len(samples.get('overlap') or [])}")
    lines.append(f"- Note: {samples.get('note')}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Trello writes: false",
            "- Google Drive writes: false",
            "- Live Trello read: false",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _load_board_snapshot_comparison(path: str) -> dict[str, Any]:
    comparison_path = Path(path).expanduser()
    if not comparison_path.exists():
        raise TrelloError(f"Board snapshot comparison JSON not found: {comparison_path}")
    try:
        payload = json.loads(comparison_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TrelloError(f"Board snapshot comparison JSON is invalid: {comparison_path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("summary_deltas"), dict):
        raise TrelloError("Board snapshot comparison JSON must contain summary_deltas")
    return payload


def _cutover_readiness(comparison: dict[str, Any], proposed_action: str) -> dict[str, Any]:
    summary_deltas = comparison.get("summary_deltas") or {}
    lists = comparison.get("lists") or {}
    labels = comparison.get("labels") or {}
    samples = comparison.get("sample_cards") or {}
    warnings = list(comparison.get("warnings") or [])
    blockers = []
    review_items = []

    critical_delta_keys = ["cards", "open_cards", "attachment_count", "check_items"]
    for key in critical_delta_keys:
        delta = int((summary_deltas.get(key) or {}).get("delta") or 0)
        if delta != 0:
            blockers.append(f"{key}_delta_{delta}")

    if lists.get("primary_only") or lists.get("comparison_only"):
        blockers.append("list_sets_differ")
    if warnings:
        review_items.extend(warnings)
    if labels.get("primary_only") or labels.get("comparison_only"):
        review_items.append("label_sets_differ")
    if samples.get("primary_only") or samples.get("comparison_only"):
        review_items.append("sample_cards_differ")

    ready = not blockers
    recommendation = (
        "Do not archive or delete the legacy board yet. Resolve blockers and regenerate snapshots."
        if blockers
        else "No blocking deltas found in this comparison. Review notes still require human confirmation before archive/cutover."
    )

    return {
        "ok": True,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "proposed_action": proposed_action,
        "ready_for_cutover": ready,
        "ready_for_archive": ready and proposed_action in {"archive_legacy_memphis", "archive_legacy_board"},
        "blockers": blockers,
        "review_items": sorted(set(review_items)),
        "recommendation": recommendation,
        "comparison_summary": {
            "primary_board": comparison.get("primary_board"),
            "comparison_board": comparison.get("comparison_board"),
            "summary_deltas": summary_deltas,
            "warnings": warnings,
            "primary_only_lists": lists.get("primary_only") or [],
            "comparison_only_lists": lists.get("comparison_only") or [],
            "primary_only_labels": labels.get("primary_only") or [],
            "comparison_only_labels": labels.get("comparison_only") or [],
            "primary_only_sample_cards": len(samples.get("primary_only") or []),
            "comparison_only_sample_cards": len(samples.get("comparison_only") or []),
            "overlap_sample_cards": len(samples.get("overlap") or []),
        },
        "required_human_checks": [
            "Confirm snapshots were generated from the intended new Memphis and legacy Memphis boards.",
            "Confirm important cards, attachments, and checklist history are accounted for.",
            "Confirm no active work remains only on the legacy board.",
            "Confirm archive/delete action is intentional before any Trello write tool is used.",
        ],
        "safety": {
            "local_file_read": True,
            "local_file_write": False,
            "trello_writes": False,
            "google_drive_writes": False,
            "live_trello_read": False,
            "archive_or_delete_performed": False,
        },
    }


def _format_cutover_readiness(readiness: dict[str, Any]) -> str:
    summary = readiness.get("comparison_summary") or {}
    primary = summary.get("primary_board") or {}
    comparison = summary.get("comparison_board") or {}
    lines = [
        "# Board Cutover Readiness",
        "",
        f"- Generated: {readiness.get('generated_at') or datetime.now().isoformat(timespec='seconds')}",
        f"- Proposed action: {readiness.get('proposed_action')}",
        f"- Primary board: {primary.get('name') or 'UNKNOWN'}",
        f"- Comparison board: {comparison.get('name') or 'UNKNOWN'}",
        f"- Ready for cutover: {readiness.get('ready_for_cutover')}",
        f"- Ready for archive: {readiness.get('ready_for_archive')}",
        "",
        "## Recommendation",
        "",
        readiness.get("recommendation") or "UNKNOWN",
        "",
        "## Blockers",
        "",
    ]
    blockers = readiness.get("blockers") or []
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- None")

    lines.extend(["", "## Review Items", ""])
    review_items = readiness.get("review_items") or []
    if review_items:
        for item in review_items:
            lines.append(f"- {item}")
    else:
        lines.append("- None")

    lines.extend(["", "## Summary Deltas", ""])
    for key, row in (summary.get("summary_deltas") or {}).items():
        lines.append(f"- {key}: primary {row.get('primary', 0)}, comparison {row.get('comparison', 0)}, delta {row.get('delta', 0)}")

    lines.extend(["", "## Required Human Checks", ""])
    for item in readiness.get("required_human_checks") or []:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Trello writes: false",
            "- Google Drive writes: false",
            "- Live Trello read: false",
            "- Archive/delete performed: false",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


@mcp.tool()
def write_board_snapshot_report(
    board: str = "memphis",
    include_complete: bool = True,
    limit_cards: int = 1000,
    sample_cards_per_list: int = 8,
) -> dict[str, Any]:
    """Write a local read-only board snapshot report for cutover readiness."""
    snapshot = _board_snapshot(
        board=board,
        include_complete=include_complete,
        limit_cards=limit_cards,
        sample_cards_per_list=sample_cards_per_list,
    )
    audit_dir = _artifact_dir("audits")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    board_name = _safe_name((snapshot.get("board") or {}).get("name") or board)
    stem = _safe_name(f"board-snapshot-{board_name}-{timestamp}")
    json_path = audit_dir / f"{stem}.json"
    md_path = audit_dir / f"{stem}.md"

    json_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_format_board_snapshot(snapshot), encoding="utf-8")

    return {
        "ok": True,
        "markdown_path": str(md_path),
        "json_path": str(json_path),
        "summary": snapshot.get("summary"),
        "scope": snapshot.get("scope"),
        "safety": {
            "local_file_write": True,
            "trello_writes": False,
            "google_drive_writes": False,
            "auto_attach": False,
        },
    }


@mcp.tool()
def write_board_snapshot_comparison_report(
    primary_snapshot_json: str,
    comparison_snapshot_json: str,
    label: str = "board-snapshot-comparison",
) -> dict[str, Any]:
    """Compare two local board snapshot JSON files and write Markdown/JSON."""
    primary = _load_board_snapshot(primary_snapshot_json)
    comparison_snapshot = _load_board_snapshot(comparison_snapshot_json)
    comparison = _compare_board_snapshots(primary, comparison_snapshot)
    comparison["source_paths"] = {
        "primary_snapshot_json": str(Path(primary_snapshot_json).expanduser()),
        "comparison_snapshot_json": str(Path(comparison_snapshot_json).expanduser()),
    }
    comparison["safety"]["local_file_write"] = True

    audit_dir = _artifact_dir("audits")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    primary_name = _safe_name((primary.get("board") or {}).get("name") or "primary")
    comparison_name = _safe_name((comparison_snapshot.get("board") or {}).get("name") or "comparison")
    stem = _safe_name(f"{label}-{primary_name}-vs-{comparison_name}-{timestamp}")
    json_path = audit_dir / f"{stem}.json"
    md_path = audit_dir / f"{stem}.md"

    json_path.write_text(json.dumps(comparison, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_format_board_snapshot_comparison(comparison), encoding="utf-8")

    return {
        "ok": True,
        "markdown_path": str(md_path),
        "json_path": str(json_path),
        "warnings": comparison.get("warnings"),
        "summary_deltas": comparison.get("summary_deltas"),
        "safety": {
            "local_file_read": True,
            "local_file_write": True,
            "trello_writes": False,
            "google_drive_writes": False,
            "live_trello_read": False,
        },
    }


@mcp.tool()
def write_cutover_readiness_report(
    comparison_json: str,
    proposed_action: str = "archive_legacy_memphis",
) -> dict[str, Any]:
    """Write a local cutover/archive readiness report from a snapshot comparison."""
    comparison = _load_board_snapshot_comparison(comparison_json)
    readiness = _cutover_readiness(comparison, proposed_action)
    readiness["source_paths"] = {
        "comparison_json": str(Path(comparison_json).expanduser()),
    }
    readiness["safety"]["local_file_write"] = True

    audit_dir = _artifact_dir("audits")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    primary_name = _safe_name(((comparison.get("primary_board") or {}).get("name")) or "primary")
    comparison_name = _safe_name(((comparison.get("comparison_board") or {}).get("name")) or "comparison")
    stem = _safe_name(f"cutover-readiness-{primary_name}-vs-{comparison_name}-{timestamp}")
    json_path = audit_dir / f"{stem}.json"
    md_path = audit_dir / f"{stem}.md"

    json_path.write_text(json.dumps(readiness, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_format_cutover_readiness(readiness), encoding="utf-8")

    return {
        "ok": True,
        "ready_for_cutover": readiness.get("ready_for_cutover"),
        "ready_for_archive": readiness.get("ready_for_archive"),
        "blockers": readiness.get("blockers"),
        "review_items": readiness.get("review_items"),
        "recommendation": readiness.get("recommendation"),
        "markdown_path": str(md_path),
        "json_path": str(json_path),
        "safety": {
            "local_file_read": True,
            "local_file_write": True,
            "trello_writes": False,
            "google_drive_writes": False,
            "live_trello_read": False,
            "archive_or_delete_performed": False,
        },
    }


@mcp.tool()
def write_cutover_packet(
    primary_board: str = "memphis",
    comparison_board: str = "legacy_memphis",
    proposed_action: str = "archive_legacy_memphis",
    include_complete: bool = True,
    limit_cards: int = 1000,
    sample_cards_per_list: int = 8,
) -> dict[str, Any]:
    """Write the full local cutover packet: snapshots, comparison, readiness.

    This performs live Trello reads through the snapshot tools when credentials
    are available. It never writes to Trello.
    """
    primary_snapshot = write_board_snapshot_report(
        board=primary_board,
        include_complete=include_complete,
        limit_cards=limit_cards,
        sample_cards_per_list=sample_cards_per_list,
    )
    comparison_snapshot = write_board_snapshot_report(
        board=comparison_board,
        include_complete=include_complete,
        limit_cards=limit_cards,
        sample_cards_per_list=sample_cards_per_list,
    )
    comparison_report = write_board_snapshot_comparison_report(
        primary_snapshot_json=str(primary_snapshot["json_path"]),
        comparison_snapshot_json=str(comparison_snapshot["json_path"]),
        label="cutover-comparison",
    )
    readiness_report = write_cutover_readiness_report(
        comparison_json=str(comparison_report["json_path"]),
        proposed_action=proposed_action,
    )

    return {
        "ok": True,
        "primary_board": primary_board,
        "comparison_board": comparison_board,
        "proposed_action": proposed_action,
        "artifacts": {
            "primary_snapshot_markdown": primary_snapshot.get("markdown_path"),
            "primary_snapshot_json": primary_snapshot.get("json_path"),
            "comparison_snapshot_markdown": comparison_snapshot.get("markdown_path"),
            "comparison_snapshot_json": comparison_snapshot.get("json_path"),
            "comparison_markdown": comparison_report.get("markdown_path"),
            "comparison_json": comparison_report.get("json_path"),
            "readiness_markdown": readiness_report.get("markdown_path"),
            "readiness_json": readiness_report.get("json_path"),
        },
        "readiness": {
            "ready_for_cutover": readiness_report.get("ready_for_cutover"),
            "ready_for_archive": readiness_report.get("ready_for_archive"),
            "blockers": readiness_report.get("blockers"),
            "review_items": readiness_report.get("review_items"),
            "recommendation": readiness_report.get("recommendation"),
        },
        "safety": {
            "local_file_write": True,
            "trello_reads": True,
            "trello_writes": False,
            "google_drive_writes": False,
            "archive_or_delete_performed": False,
        },
    }


@mcp.tool()
def inspect_cards_without_sheet_attachments(
    board: str = "memphis",
    include_complete: bool = False,
    limit_cards: int = 500,
) -> dict[str, Any]:
    """Read-only detail for cards that do not have XLS/XLSX/CSV attachments."""
    board_info = get_board(board)
    lists = get_lists(board)
    list_names = {item["id"]: item["name"] for item in lists}
    cards = _request(
        "GET",
        f"boards/{_board_id(board)}/cards",
        params={"filter": "open", "fields": "id,name,desc,shortUrl,idList,due,dateLastActivity,labels"},
    )
    if not include_complete:
        cards = [card for card in cards if list_names.get(card.get("idList")) != "Complete"]
    cards = cards[: max(1, min(limit_cards, 1000))]

    gaps = []
    for card in cards:
        attachments = get_card_attachments(card["id"])
        sheet_attachments = [item for item in attachments if item["extension"] in SUPPORTED_SHEET_EXTENSIONS]
        if sheet_attachments:
            continue

        list_name = list_names.get(card.get("idList"), "UNKNOWN")
        address_candidates = _extract_address_candidates(f"{card.get('name', '')}\n{card.get('desc', '')}")
        non_sheet_attachments = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "extension": item.get("extension"),
                "mimeType": item.get("mimeType"),
                "bytes": item.get("bytes"),
                "date": item.get("date"),
            }
            for item in attachments
        ]
        labels = [label.get("name") or label.get("color") for label in card.get("labels", [])]

        if list_name in {"BILLS", "My Bill"}:
            reason = "billing_lane_sheet_may_not_be_expected"
        elif "SAFETY COVER" in list_name.upper():
            reason = "safety_cover_lane_may_use_non_tara_artifacts"
        elif list_name == "MEASURES":
            reason = "measure_lane_missing_expected_sheet_review"
        else:
            reason = "missing_sheet_review"

        gaps.append(
            {
                "card_id": card.get("id"),
                "card_name": card.get("name"),
                "card_url": card.get("shortUrl"),
                "list": list_name,
                "labels": labels,
                "due": card.get("due"),
                "dateLastActivity": card.get("dateLastActivity"),
                "address_candidates": address_candidates,
                "non_sheet_attachment_count": len(non_sheet_attachments),
                "non_sheet_attachments": non_sheet_attachments,
                "classification": reason,
            }
        )

    by_classification: dict[str, int] = {}
    by_list: dict[str, int] = {}
    for gap in gaps:
        by_classification[gap["classification"]] = by_classification.get(gap["classification"], 0) + 1
        by_list[gap["list"]] = by_list.get(gap["list"], 0) + 1

    return {
        "board": {k: board_info.get(k) for k in ("id", "name", "url", "closed", "dateLastActivity")},
        "scope": {
            "include_complete": include_complete,
            "cards_scanned": len(cards),
            "limit_cards": limit_cards,
        },
        "summary": {
            "cards_without_sheet_attachments": len(gaps),
            "by_list": by_list,
            "by_classification": by_classification,
        },
        "cards": gaps,
    }


@mcp.tool()
def find_sheet_candidates_for_card(
    card_id: str,
    search_boards_json: str = '["memphis", "legacy_memphis"]',
    include_complete: bool = True,
    limit_candidates: int = 20,
) -> dict[str, Any]:
    """Find likely XLS/XLSX/CSV attachment candidates for a card, read-only."""
    target = get_card(card_id)
    target_text = f"{target.get('name', '')}\n{target.get('desc', '')}"
    target_tokens = _match_tokens(target_text)
    search_boards = json.loads(search_boards_json)
    candidates = []

    for board in search_boards:
        board_info = get_board(board)
        lists = get_lists(board)
        list_names = {item["id"]: item["name"] for item in lists}
        cards = _request(
            "GET",
            f"boards/{_board_id(board)}/cards",
            params={"filter": "all" if include_complete else "open", "fields": "id,name,desc,shortUrl,idList,closed,dateLastActivity"},
        )

        for card in cards:
            if card.get("id") == card_id:
                continue
            name_desc_score = _score_text(target_tokens, f"{card.get('name', '')}\n{card.get('desc', '')}")
            if name_desc_score == 0:
                continue

            attachments = get_card_attachments(card["id"])
            sheet_attachments = [item for item in attachments if item["extension"] in SUPPORTED_SHEET_EXTENSIONS]
            if not sheet_attachments:
                continue

            attachment_score = 0
            for item in sheet_attachments:
                attachment_score = max(attachment_score, _score_text(target_tokens, item.get("name") or ""))

            score = name_desc_score * 2 + attachment_score
            candidates.append(
                {
                    "score": score,
                    "board_alias": board,
                    "board_id": board_info.get("id"),
                    "board_name": board_info.get("name"),
                    "card_id": card.get("id"),
                    "card_name": card.get("name"),
                    "card_url": card.get("shortUrl"),
                    "list": list_names.get(card.get("idList"), "UNKNOWN"),
                    "closed": card.get("closed"),
                    "dateLastActivity": card.get("dateLastActivity"),
                    "name_desc_score": name_desc_score,
                    "attachment_score": attachment_score,
                    "sheet_attachments": [
                        {
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "extension": item.get("extension"),
                            "bytes": item.get("bytes"),
                            "date": item.get("date"),
                        }
                        for item in sheet_attachments
                    ],
                }
            )

    candidates.sort(key=lambda item: (item["score"], item["attachment_score"], item["dateLastActivity"] or ""), reverse=True)
    candidates = candidates[: max(1, min(limit_candidates, 100))]

    return {
        "target": {
            "card_id": target.get("id"),
            "card_name": target.get("name"),
            "card_url": target.get("shortUrl"),
            "tokens": sorted(target_tokens),
        },
        "scope": {
            "search_boards": search_boards,
            "include_complete": include_complete,
            "limit_candidates": limit_candidates,
        },
        "candidates": candidates,
    }


@mcp.tool()
def download_attachment(card_id: str, attachment_id: str, output_dir: str | None = None) -> dict[str, Any]:
    """Download one Trello attachment into the local artifact cache."""
    attachment = _request("GET", f"cards/{card_id}/attachments/{attachment_id}")
    target_dir = Path(output_dir).expanduser() if output_dir else _artifact_dir("attachments")
    target_dir.mkdir(parents=True, exist_ok=True)
    name = _safe_name(attachment.get("name") or attachment_id)
    path = target_dir / f"{card_id}-{attachment_id}-{name}"
    content = _download_request(_attachment_download_url(card_id, attachment))
    path.write_bytes(content)
    return {
        "path": str(path),
        "filename": attachment.get("name"),
        "bytes": len(content),
        "sha256": _sha256(path),
        "mimeType": attachment.get("mimeType"),
        "date": attachment.get("date"),
    }


@mcp.tool()
def read_xls_attachment(card_id: str, attachment_id: str, max_rows: int = 40, max_cols: int = 20) -> dict[str, Any]:
    """Download and preview an XLS/XLSX/CSV attachment from a Trello card."""
    downloaded = download_attachment(card_id, attachment_id)
    path = Path(downloaded["path"])
    if path.suffix.lower() not in SUPPORTED_SHEET_EXTENSIONS:
        raise TrelloError(f"Attachment is not a supported sheet file: {path.name}")
    preview = _excel_preview(path, max_rows=max_rows, max_cols=max_cols)
    text = _flatten_preview_text(preview)
    return {
        "download": downloaded,
        "preview": preview,
        "address_candidates": _extract_address_candidates(text),
    }


def _safe_attachment_name(name: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", name or "attachment").strip("._")
    return clean[:180] or "attachment"


def _attachment_summary(attachment: dict[str, Any]) -> dict[str, Any]:
    name = attachment.get("name") or ""
    return {
        "id": attachment.get("id"),
        "name": name,
        "url": attachment.get("url"),
        "bytes": attachment.get("bytes"),
        "date": attachment.get("date"),
        "mimeType": attachment.get("mimeType"),
        "isUpload": attachment.get("isUpload"),
        "extension": Path(name).suffix.lower(),
    }


def _work_order_attachment_score(attachment: dict[str, Any], name_filter: str = "") -> int:
    name = str(attachment.get("name") or "").lower()
    if name_filter and name_filter.lower() not in name:
        return -1000
    score = 0
    suffix = Path(name).suffix.lower()
    if suffix in {".xls", ".xlsx", ".csv", ".pdf"}:
        score += 40
    if "install" in name:
        score += 35
    if "work" in name and "order" in name:
        score += 30
    if "measure" in name:
        score += 20
    if "liner" in name:
        score += 15
    if "drawing" in name or "scan" in name:
        score += 5
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}:
        score -= 80
    return score


def _normalize_extracted_text(text: str) -> str:
    lines = []
    seen = set()
    for line in (text or "").replace("\r", "\n").splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        if len(clean) < 2 or clean in seen:
            continue
        seen.add(clean)
        lines.append(clean)
    return "\n".join(lines)


def _extract_attachment_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                return _normalize_extracted_text(result.stdout)
        except Exception:
            pass
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return _normalize_extracted_text(text)
        except Exception as exc:
            return f"[pdf text extraction failed: {exc!r}]"

    if suffix == ".xlsx":
        try:
            chunks: list[str] = []
            with zipfile.ZipFile(path) as zf:
                if "xl/sharedStrings.xml" in zf.namelist():
                    root = ElementTree.fromstring(zf.read("xl/sharedStrings.xml"))
                    for node in root.iter():
                        if (node.tag.endswith("}t") or node.tag == "t") and node.text:
                            chunks.append(node.text)
                for name in zf.namelist():
                    if not (name.startswith("xl/worksheets/") and name.endswith(".xml")):
                        continue
                    root = ElementTree.fromstring(zf.read(name))
                    for node in root.iter():
                        if node.text and node.text.strip():
                            chunks.append(node.text)
            return _normalize_extracted_text("\n".join(chunks))
        except Exception as exc:
            return f"[xlsx text extraction failed: {exc!r}]"

    if suffix == ".xls":
        chunks = []
        for cmd in (["strings", "-a", str(path)], ["strings", "-el", str(path)]):
            try:
                result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
                if result.stdout:
                    chunks.append(result.stdout)
            except Exception:
                continue
        return _normalize_extracted_text("\n".join(chunks))

    try:
        return _normalize_extracted_text(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return ""


def _work_order_hints(text: str) -> dict[str, Any]:
    lines = [line for line in (text or "").splitlines() if line.strip()]
    haul_lines = [
        line
        for line in lines
        if re.search(r"\bha(?:u)?l\s*-?\s*off\b|hauloff|trash|dispose|disposal", line, re.IGNORECASE)
    ]
    joined = "\n".join(haul_lines)
    haul_off = None
    if re.search(r"\bno\s+haul\s*-?\s*off\b|\bno\s+hauloff\b", joined, re.IGNORECASE):
        haul_off = "NO HAUL OFF"
    elif re.search(r"\bha(?:u)?l\s*-?\s*off\b|hauloff", joined, re.IGNORECASE):
        haul_off = "HAUL OFF MENTIONED"
    important = [
        line
        for line in lines
        if re.search(
            r"haul|liner|install|measure|steps|inlay|freeform|safety|cover|fold|address|phone|customer",
            line,
            re.IGNORECASE,
        )
    ]
    return {
        "haul_off": haul_off,
        "haul_lines": haul_lines[:12],
        "important_lines": important[:40],
    }


@mcp.tool()
def attach_file_to_card(
    file_path: str,
    card_id: str | None = None,
    card_query: str | None = None,
    board: str = "memphis",
    name: str | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Attach a local file to a Trello card.

    This is a real Trello write. Provide either card_id or a card_query that
    resolves to exactly one open card. Comments are optional and are never
    inferred from a spoken/user prompt.
    """
    if not card_id and not card_query:
        raise TrelloError("card_id or card_query is required")
    path = Path(file_path).expanduser()
    if not path.is_file():
        raise TrelloError(f"File does not exist: {path}")

    card = get_card(card_id) if card_id else _find_card_by_query(str(card_query), board=board)
    content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    attachment_name = (name or path.name).strip()[:256]
    with path.open("rb") as fh:
        attachment = _request_files(
            "POST",
            f"cards/{card['id']}/attachments",
            params={"name": attachment_name},
            files={"file": (path.name, fh, content_type)},
        )
    comment_action = None
    if comment and comment.strip():
        comment_action = add_comment(str(card["id"]), comment.strip()[:1600])
    return {
        "ok": True,
        "card": _card_with_board_context(card),
        "attachment": _attachment_summary(attachment),
        "comment_action_id": comment_action.get("id") if isinstance(comment_action, dict) else None,
        "safety": {
            "trello_writes": True,
            "attachment_written": True,
            "comment_written": bool(comment_action),
            "user_prompt_used_as_comment": False,
        },
    }


@mcp.tool()
def set_card_cover(card_id: str, attachment_id: str) -> dict[str, Any]:
    """Set a Trello card cover to an existing attachment id."""
    if not card_id or not attachment_id:
        raise TrelloError("card_id and attachment_id are required")
    card = _request("PUT", f"cards/{card_id}", params={"idAttachmentCover": attachment_id})
    return {
        "ok": True,
        "card": _card_with_board_context(card),
        "attachment_id": attachment_id,
        "safety": {"trello_writes": True, "cover_changed": True},
    }


@mcp.tool()
def read_card_work_order(
    card_id: str | None = None,
    card_query: str | None = None,
    board: str = "memphis",
    attachment_filter: str = "",
    question: str = "",
    max_text_chars: int = 6000,
) -> dict[str, Any]:
    """Read the best work-order-like attachment on a Trello card.

    This is read-only. It prefers install/work-order spreadsheets and PDFs over
    photos, downloads the selected attachment to the local artifact cache, and
    extracts useful text plus haul-off hints.
    """
    if not card_id and not card_query:
        raise TrelloError("card_id or card_query is required")
    card = get_card(card_id) if card_id else _find_card_by_query(str(card_query), board=board)
    attachments = get_card_attachments(str(card["id"]))
    ranked = sorted(attachments, key=lambda item: _work_order_attachment_score(item, attachment_filter), reverse=True)
    candidates = [
        item
        for item in ranked
        if _work_order_attachment_score(item, attachment_filter) > 0
        and Path(item.get("name") or "").suffix.lower() in SUPPORTED_WORK_ORDER_EXTENSIONS
    ]
    if not candidates:
        return {
            "ok": False,
            "error": f"No readable work-order attachment found on {card.get('name')}",
            "card": _card_with_board_context(card),
            "attachment_filter": attachment_filter,
            "attachments": [_attachment_summary(item) for item in attachments[:30]],
            "safety": {"read_only": True, "trello_writes": False},
        }

    attachment = candidates[0]
    downloaded = download_attachment(str(card["id"]), str(attachment["id"]), output_dir=str(_artifact_dir("work-orders")))
    local_path = Path(downloaded["path"])
    text = _extract_attachment_text(local_path)
    limit = max(500, min(int(max_text_chars), 20000))
    return {
        "ok": True,
        "card": _card_with_board_context(card),
        "attachment": _attachment_summary(attachment),
        "download": downloaded,
        "question": question,
        "hints": _work_order_hints(text),
        "text": text[:limit],
        "text_truncated": len(text) > limit,
        "safety": {
            "read_only": True,
            "trello_writes": False,
            "local_file_write": True,
        },
    }


@mcp.tool()
def scan_tara_xls_forms(source_path: str, max_files: int = 200) -> list[dict[str, Any]]:
    """Read-only scan of local XLS/XLSX/CSV files for Tara/work-order matching."""
    root = Path(source_path).expanduser()
    if not root.exists():
        raise TrelloError(f"Source path does not exist: {root}")
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.suffix.lower() in SUPPORTED_SHEET_EXTENSIONS]
    results = []
    for path in files[: max(1, min(max_files, 1000))]:
        try:
            preview = _excel_preview(path, max_rows=25, max_cols=12)
            results.append(
                {
                    "path": str(path),
                    "filename": path.name,
                    "size": path.stat().st_size,
                    "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                    "sha256": _sha256(path),
                    "address_candidates": _extract_address_candidates(_flatten_preview_text(preview)),
                    "preview": preview,
                }
            )
        except Exception as exc:
            results.append({"path": str(path), "error": str(exc)})
    return results


@mcp.tool()
def scan_pool_photos(source_path: str, max_files: int = 500) -> list[dict[str, Any]]:
    """Read-only scan of local photo files for GPS/time metadata."""
    root = Path(source_path).expanduser()
    if not root.exists():
        raise TrelloError(f"Source path does not exist: {root}")
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.suffix.lower() in SUPPORTED_PHOTO_EXTENSIONS]
    results = []
    for path in files[: max(1, min(max_files, 5000))]:
        try:
            results.append(_photo_metadata(path))
        except Exception as exc:
            results.append({"path": str(path), "filename": path.name, "error": str(exc)})
    return results


@mcp.tool()
def match_photos_to_locations(
    source_path: str,
    locations_json: str,
    radius_ft: int = 300,
    max_files: int = 500,
) -> list[dict[str, Any]]:
    """Match GPS-tagged photos to supplied card/location records.

    locations_json must be a JSON array with objects containing card_id, name,
    latitude, and longitude. This keeps geocoding outside the matcher until the
    address source is verified.
    """
    locations = json.loads(locations_json)
    photos = [p for p in scan_pool_photos(source_path, max_files=max_files) if p.get("has_gps")]
    matches = []
    for photo in photos:
        ranked = []
        for loc in locations:
            if loc.get("latitude") is None or loc.get("longitude") is None:
                continue
            distance = _distance_ft(float(photo["latitude"]), float(photo["longitude"]), float(loc["latitude"]), float(loc["longitude"]))
            if distance <= radius_ft:
                ranked.append(
                    {
                        "card_id": loc.get("card_id"),
                        "card_name": loc.get("name"),
                        "card_url": loc.get("url"),
                        "address": loc.get("address"),
                        "distance_ft": round(distance, 1),
                    }
                )
        if ranked:
            ranked.sort(key=lambda item: item["distance_ft"])
            best = ranked[0]
            confidence = "very_strong" if best["distance_ft"] <= 100 else "likely" if best["distance_ft"] <= 300 else "review"
            matches.append({"photo": photo, "best_match": best, "confidence": confidence, "all_matches": ranked[:5]})
    return matches


@mcp.tool()
def search_pool_records(
    query: str,
    record_kind: str = "any",
    year: str | None = None,
    limit: int = 8,
    min_relevance: float = 0.0,
) -> dict[str, Any]:
    """Search indexed Memphis/Artesian work orders and bills from the local RAG corpus.

    record_kind can be any, work_order, or bill. year should be a four-digit
    year when supplied. This is read-only and restricted to the pool_jobs source.
    """
    q = (query or "").strip()
    if not q:
        raise TrelloError("query is required")
    kind = (record_kind or "any").strip().lower()
    if kind not in {"any", "work_order", "bill"}:
        raise TrelloError("record_kind must be one of: any, work_order, bill")
    if year is not None and not re.fullmatch(r"20\d{2}", str(year)):
        raise TrelloError("year must be a four-digit 20xx year")

    requested_limit = max(1, min(int(limit), 25))
    search_limit = requested_limit if kind == "any" and year is None else min(max(requested_limit * 4, 12), 50)
    args = ["search", q, "--source", "pool_jobs", "--top-k", str(search_limit)]
    if min_relevance:
        args.extend(["--min-relevance", str(min_relevance)])
    payload = _run_rag(args, timeout=180)

    filtered = []
    for result in payload.get("results") or []:
        result_kind = _pool_record_kind(result)
        result_year = _pool_record_year(result)
        if kind != "any" and result_kind != kind:
            continue
        if year is not None and result_year != str(year):
            continue
        filtered.append(_pool_record_summary(result))
        if len(filtered) >= requested_limit:
            break

    return {
        "ok": True,
        "query": q,
        "filters": {"record_kind": kind, "year": str(year) if year is not None else None},
        "source": "pool_jobs",
        "returned": len(filtered),
        "searched_results": len(payload.get("results") or []),
        "results": filtered,
    }


@mcp.tool()
def ask_pool_records(question: str, top_k: int = 8, min_relevance: float = 0.0) -> dict[str, Any]:
    """Ask a natural-language question against indexed pool work orders and bills.

    This is read-only and restricted to the pool_jobs source. Use search_pool_records
    first when you need exact files or tight bill/work-order/year filters.
    """
    q = (question or "").strip()
    if not q:
        raise TrelloError("question is required")
    args = ["ask", q, "--source", "pool_jobs", "--top-k", str(max(1, min(int(top_k), 12)))]
    if min_relevance:
        args.extend(["--min-relevance", str(min_relevance)])
    payload = _run_rag(args, timeout=240)
    return {
        "ok": True,
        "question": q,
        "source": "pool_jobs",
        "answer": payload.get("answer"),
        "sources": [_pool_record_summary(result, excerpt_chars=700) for result in payload.get("results") or []],
        "errors": payload.get("errors") or [],
    }


@mcp.tool()
def find_records_for_card(
    card_id: str,
    record_kind: str = "any",
    include_attachment_names: bool = True,
    limit: int = 8,
    min_relevance: float = 0.0,
) -> dict[str, Any]:
    """Find likely indexed work-order/bill records for one Trello card.

    This is read-only. It reads card fields and optional attachment names, searches
    the local pool_jobs RAG source, and returns review candidates with confidence.
    It never writes to Trello and never attaches records automatically.
    """
    card = get_card(card_id)
    list_name = None
    if card.get("idList"):
        try:
            list_info = _request("GET", f"lists/{card['idList']}", params={"fields": "id,name"})
            list_name = list_info.get("name")
        except Exception:
            list_name = None

    attachments = get_card_attachments(card["id"]) if include_attachment_names else []
    query = _card_record_search_text(card, list_name=list_name, attachments=attachments)
    kind = (record_kind or "any").strip().lower()
    if kind not in {"any", "work_order", "bill"}:
        raise TrelloError("record_kind must be one of: any, work_order, bill")
    if kind == "any" and list_name and "BILL" in list_name.upper():
        kind = "bill"
    if not query:
        return {
            "ok": True,
            "target": {
                "card_id": card.get("id"),
                "card_name": card.get("name"),
                "card_url": card.get("shortUrl"),
                "list": list_name,
            },
            "query": "",
            "summary": {"candidates": 0, "best_confidence": "no_match"},
            "candidates": [],
            "note": "Card had no useful searchable text.",
        }

    search = search_pool_records(
        query,
        record_kind=kind,
        year=None,
        limit=max(1, min(int(limit), 25)),
        min_relevance=min_relevance,
    )
    lexical = _lexical_pool_record_search(
        query,
        record_kind=kind,
        max_results=max(5, min(int(limit) * 3, 50)),
    )
    card_tokens = _match_tokens(query)
    strong_tokens = _strong_card_tokens(card, query)
    name_anchor_tokens = _card_name_anchor_tokens(card)
    if kind == "bill" or (list_name and "BILL" in list_name.upper()):
        name_anchor_tokens = set()
    merged_records: dict[str, dict[str, Any]] = {}
    for record in search.get("results") or []:
        path = str(record.get("path") or record.get("file") or "")
        if path:
            merged_records[path] = {**record, "retrieval_sources": ["rag"]}
    for record in lexical:
        path = str(record.get("path") or record.get("file") or "")
        if not path:
            continue
        if path in merged_records:
            existing = merged_records[path]
            existing["score"] = max(float(existing.get("score") or 0.0), float(record.get("score") or 0.0))
            existing.setdefault("retrieval_sources", ["rag"]).append("lexical")
            if len(str(record.get("text_excerpt") or "")) > len(str(existing.get("text_excerpt") or "")):
                existing["text_excerpt"] = record.get("text_excerpt")
        else:
            merged_records[path] = {**record, "retrieval_sources": ["lexical"]}

    candidates = []
    for record in merged_records.values():
        detail = _record_match_detail(
            card_tokens,
            record,
            strong_tokens=strong_tokens,
            name_anchor_tokens=name_anchor_tokens,
        )
        candidates.append({**record, "match": detail})

    candidates.sort(
        key=lambda item: (
            _confidence_rank(item.get("match", {}).get("confidence", "no_match")),
            float(item.get("score") or 0.0),
            item.get("match", {}).get("overlap_count", 0),
        ),
        reverse=True,
    )
    candidates = candidates[: max(1, min(int(limit), 25))]

    best_confidence = candidates[0]["match"]["confidence"] if candidates else "no_match"
    by_kind: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    for item in candidates:
        kind = item.get("kind") or "unknown"
        confidence = item.get("match", {}).get("confidence", "unknown")
        by_kind[kind] = by_kind.get(kind, 0) + 1
        by_confidence[confidence] = by_confidence.get(confidence, 0) + 1

    return {
        "ok": True,
        "target": {
            "card_id": card.get("id"),
            "card_name": card.get("name"),
            "card_url": card.get("shortUrl"),
            "list": list_name,
            "labels": _label_names(card),
            "due": card.get("due"),
            "dateLastActivity": card.get("dateLastActivity"),
            "attachment_names_used": [item.get("name") for item in attachments if item.get("name")],
        },
        "query": query,
        "source": "pool_jobs",
        "filters": {"record_kind": kind},
        "summary": {
            "candidates": len(candidates),
            "best_confidence": best_confidence,
            "by_kind": by_kind,
            "by_confidence": by_confidence,
            "rag_candidates_seen": search.get("searched_results"),
            "lexical_candidates_seen": len(lexical),
        },
        "candidates": candidates,
        "safety": {
            "read_only": True,
            "trello_writes": False,
            "auto_attach": False,
        },
    }


@mcp.tool()
def review_board_record_matches(
    board: str = "memphis",
    record_kind: str = "any",
    include_complete: bool = False,
    list_names_json: str = "[]",
    limit_cards: int = 20,
    max_candidates_per_card: int = 2,
    min_relevance: float = 0.0,
) -> dict[str, Any]:
    """Review likely pool record matches across a board, read-only.

    Scans a capped set of cards, runs find_records_for_card for each, and
    groups results by best confidence. list_names_json may be a JSON array of
    Trello list names to restrict the scan, for example ["MEASURES", "BILLS"].
    """
    kind = (record_kind or "any").strip().lower()
    if kind not in {"any", "work_order", "bill"}:
        raise TrelloError("record_kind must be one of: any, work_order, bill")

    try:
        selected_lists = json.loads(list_names_json or "[]")
    except json.JSONDecodeError as exc:
        raise TrelloError("list_names_json must be a JSON array of list names") from exc
    if not isinstance(selected_lists, list):
        raise TrelloError("list_names_json must be a JSON array of list names")
    selected_list_names = {str(item).strip() for item in selected_lists if str(item).strip()}

    board_info = get_board(board)
    lists = get_lists(board, filter="all" if include_complete else "open")
    list_names = {item["id"]: item["name"] for item in lists}
    cards = _request(
        "GET",
        f"boards/{_board_id(board)}/cards",
        params={
            "filter": "all" if include_complete else "open",
            "fields": "id,name,desc,shortUrl,idList,closed,due,labels,dateLastActivity",
        },
    )

    scoped_cards = []
    for card in cards:
        list_name = list_names.get(card.get("idList"), "UNKNOWN")
        if card.get("closed") and not include_complete:
            continue
        if not include_complete and list_name == "Complete":
            continue
        if selected_list_names and list_name not in selected_list_names:
            continue
        scoped_cards.append(card)

    scoped_card_count = len(scoped_cards)
    scoped_cards.sort(key=lambda item: item.get("dateLastActivity") or "", reverse=True)
    scoped_cards = scoped_cards[: max(1, min(int(limit_cards), 100))]

    buckets = _empty_match_buckets()
    by_list: dict[str, dict[str, int]] = {}
    errors = []
    cards_reviewed = 0
    card_limit = max(1, min(int(max_candidates_per_card), 8))

    for card in scoped_cards:
        list_name = list_names.get(card.get("idList"), "UNKNOWN")
        list_row = by_list.setdefault(
            list_name,
            {"cards": 0, "exact": 0, "likely": 0, "review": 0, "weak": 0, "no_match": 0},
        )
        list_row["cards"] += 1
        cards_reviewed += 1

        try:
            effective_kind = "bill" if kind == "any" and "BILL" in list_name.upper() else kind
            match = find_records_for_card(
                card["id"],
                record_kind=effective_kind,
                include_attachment_names=True,
                limit=max(3, card_limit),
                min_relevance=min_relevance,
            )
            confidence = match.get("summary", {}).get("best_confidence") or "no_match"
            if confidence not in buckets:
                confidence = "weak"
            list_row[confidence] += 1
            buckets[confidence].append(
                {
                    "card_id": card.get("id"),
                    "card_name": card.get("name"),
                    "card_url": card.get("shortUrl"),
                    "list": list_name,
                    "labels": _label_names(card),
                    "due": card.get("due"),
                    "dateLastActivity": card.get("dateLastActivity"),
                    "query": match.get("query"),
                    "candidate_count": match.get("summary", {}).get("candidates", 0),
                    "by_kind": match.get("summary", {}).get("by_kind", {}),
                    "top_candidates": [
                        _record_candidate_preview(item)
                        for item in (match.get("candidates") or [])[:card_limit]
                    ],
                }
            )
        except Exception as exc:
            list_row["no_match"] += 1
            errors.append(
                {
                    "card_id": card.get("id"),
                    "card_name": card.get("name"),
                    "card_url": card.get("shortUrl"),
                    "list": list_name,
                    "error": str(exc)[:500],
                }
            )
            buckets["no_match"].append(
                {
                    "card_id": card.get("id"),
                    "card_name": card.get("name"),
                    "card_url": card.get("shortUrl"),
                    "list": list_name,
                    "candidate_count": 0,
                    "top_candidates": [],
                    "error": str(exc)[:500],
                }
            )

    bucket_counts = {name: len(items) for name, items in buckets.items()}
    needs_human_review = bucket_counts["review"] + bucket_counts["weak"] + bucket_counts["no_match"]

    return {
        "ok": True,
        "board": {k: board_info.get(k) for k in ("id", "name", "url", "closed", "dateLastActivity")},
        "scope": {
            "record_kind": kind,
            "include_complete": include_complete,
            "selected_lists": sorted(selected_list_names),
            "cards_available_after_scope": scoped_card_count,
            "cards_reviewed": cards_reviewed,
            "limit_cards": limit_cards,
            "max_candidates_per_card": card_limit,
            "source": "pool_jobs",
        },
        "summary": {
            "bucket_counts": bucket_counts,
            "actionable_without_record_writes": bucket_counts["exact"] + bucket_counts["likely"],
            "needs_human_review": needs_human_review,
            "errors": len(errors),
        },
        "by_list": by_list,
        "buckets": buckets,
        "errors": errors,
        "safety": {
            "read_only": True,
            "trello_writes": False,
            "google_drive_writes": False,
            "auto_attach": False,
        },
    }


def _format_board_record_match_report(review: dict[str, Any]) -> str:
    board = review.get("board") or {}
    scope = review.get("scope") or {}
    summary = review.get("summary") or {}
    bucket_counts = summary.get("bucket_counts") or {}
    lines = [
        f"# Board Record Match Report - {board.get('name') or 'UNKNOWN'}",
        "",
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"- Board URL: {board.get('url') or 'UNKNOWN'}",
        f"- Source: {scope.get('source') or 'UNKNOWN'}",
        f"- Record kind: {scope.get('record_kind') or 'any'}",
        f"- Include complete: {scope.get('include_complete')}",
        f"- Selected lists: {', '.join(scope.get('selected_lists') or []) or 'all active lists'}",
        f"- Cards reviewed: {scope.get('cards_reviewed')} of {scope.get('cards_available_after_scope')}",
        "",
        "## Summary",
        "",
        f"- Exact: {bucket_counts.get('exact', 0)}",
        f"- Likely: {bucket_counts.get('likely', 0)}",
        f"- Review: {bucket_counts.get('review', 0)}",
        f"- Weak: {bucket_counts.get('weak', 0)}",
        f"- No match: {bucket_counts.get('no_match', 0)}",
        f"- Actionable without Trello writes: {summary.get('actionable_without_record_writes', 0)}",
        f"- Needs human review: {summary.get('needs_human_review', 0)}",
        f"- Errors: {summary.get('errors', 0)}",
        "",
        "## By List",
        "",
    ]

    for list_name, row in sorted((review.get("by_list") or {}).items()):
        lines.append(
            f"- {list_name}: {row.get('cards', 0)} cards; "
            f"exact {row.get('exact', 0)}, likely {row.get('likely', 0)}, "
            f"review {row.get('review', 0)}, weak {row.get('weak', 0)}, no_match {row.get('no_match', 0)}"
        )

    for bucket in ("exact", "likely", "review", "weak", "no_match"):
        lines.extend(["", f"## {bucket.replace('_', ' ').title()}", ""])
        items = (review.get("buckets") or {}).get(bucket) or []
        if not items:
            lines.append("- None")
            continue
        for item in items:
            lines.append(f"### {item.get('card_name') or 'Untitled card'}")
            lines.append("")
            lines.append(f"- Card: {item.get('card_url') or item.get('card_id')}")
            lines.append(f"- List: {item.get('list') or 'UNKNOWN'}")
            lines.append(f"- Candidate count: {item.get('candidate_count', 0)}")
            if item.get("error"):
                lines.append(f"- Error: {item.get('error')}")
            for index, candidate in enumerate(item.get("top_candidates") or [], start=1):
                lines.append(f"- Candidate {index}: {candidate.get('file') or 'UNKNOWN'}")
                lines.append(f"  - Kind: {candidate.get('kind') or 'unknown'}")
                lines.append(f"  - Year: {candidate.get('year') or 'unknown'}")
                lines.append(f"  - Confidence: {candidate.get('confidence') or 'unknown'}")
                lines.append(f"  - Reason: {candidate.get('reason') or 'unknown'}")
                lines.append(f"  - Path: {candidate.get('path') or 'UNKNOWN'}")
                overlap = ", ".join(candidate.get("overlap_tokens") or [])
                lines.append(f"  - Overlap: {overlap or 'none'}")
            lines.append("")

    if review.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in review.get("errors") or []:
            lines.append(f"- {error.get('card_name') or error.get('card_id')}: {error.get('error')}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Trello writes: false",
            "- Google Drive writes: false",
            "- Auto-attach: false",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _record_match_marker(card_id: str, record_path: str) -> str:
    seed = f"{card_id}|{record_path}".encode("utf-8", errors="ignore")
    digest = hashlib.sha256(seed).hexdigest()[:16]
    return f"codex-record-match:{digest}"


def _card_comment_actions(card_id: str, limit: int = 100) -> list[dict[str, Any]]:
    actions = _request(
        "GET",
        f"cards/{card_id}/actions",
        params={"filter": "commentCard", "limit": max(1, min(int(limit), 1000))},
    )
    return actions if isinstance(actions, list) else []


def _card_has_comment_marker(card_id: str, marker: str) -> bool:
    for action in _card_comment_actions(card_id):
        text = str((action.get("data") or {}).get("text") or "")
        if marker in text:
            return True
    return False


def _proposed_match_actions(review: dict[str, Any], allowed_confidences: set[str]) -> list[dict[str, Any]]:
    actions = []
    for bucket in ("exact", "likely", "review", "weak", "no_match"):
        if bucket not in allowed_confidences:
            continue
        for item in (review.get("buckets") or {}).get(bucket) or []:
            candidates = item.get("top_candidates") or []
            if not candidates:
                continue
            candidate = candidates[0]
            confidence = candidate.get("confidence") or bucket
            if confidence not in allowed_confidences:
                continue
            record_path = candidate.get("path") or ""
            record_name = candidate.get("file") or "matched pool record"
            marker = _record_match_marker(str(item.get("card_id") or ""), record_path)
            comment = (
                "Historical pool record candidate found.\n\n"
                f"- Confidence: {confidence}\n"
                f"- Record: {record_name}\n"
                f"- Kind: {candidate.get('kind') or 'unknown'}\n"
                f"- Year: {candidate.get('year') or 'unknown'}\n"
                f"- Source path: {record_path}\n"
                f"- Marker: {marker}\n\n"
                "Review before attaching or treating this as final."
            )
            actions.append(
                {
                    "card_id": item.get("card_id"),
                    "card_name": item.get("card_name"),
                    "card_url": item.get("card_url"),
                    "list": item.get("list"),
                    "confidence": confidence,
                    "reason": candidate.get("reason"),
                    "record_kind": candidate.get("kind"),
                    "record_year": candidate.get("year"),
                    "record_file": record_name,
                    "record_path": record_path,
                    "idempotency_marker": marker,
                    "proposed_actions": [
                        {
                            "type": "comment",
                            "status": "proposed_only",
                            "text": comment,
                        },
                        {
                            "type": "attachment_review",
                            "status": "proposed_only",
                            "note": "Local record path identified; no Trello attachment was created.",
                            "path": record_path,
                        },
                    ],
                }
            )
    actions.sort(
        key=lambda item: (
            _confidence_rank(str(item.get("confidence") or "")),
            str(item.get("card_name") or ""),
        ),
        reverse=True,
    )
    return actions


def _format_record_match_action_plan(review: dict[str, Any], actions: list[dict[str, Any]]) -> str:
    board = review.get("board") or {}
    scope = review.get("scope") or {}
    lines = [
        f"# Proposed Record Match Actions - {board.get('name') or 'UNKNOWN'}",
        "",
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"- Board URL: {board.get('url') or 'UNKNOWN'}",
        f"- Selected lists: {', '.join(scope.get('selected_lists') or []) or 'all active lists'}",
        f"- Cards reviewed: {scope.get('cards_reviewed')} of {scope.get('cards_available_after_scope')}",
        f"- Proposed actions: {len(actions)}",
        "",
        "## Important",
        "",
        "- This is a proposal only.",
        "- No Trello comments were added.",
        "- No Trello attachments were created.",
        "- No Google Drive writes were performed.",
        "",
        "## Actions",
        "",
    ]

    if not actions:
        lines.append("- None")
    for index, action in enumerate(actions, start=1):
        comment = next(
            (item for item in action.get("proposed_actions") or [] if item.get("type") == "comment"),
            {},
        )
        lines.append(f"### {index}. {action.get('card_name') or 'Untitled card'}")
        lines.append("")
        lines.append(f"- Card: {action.get('card_url') or action.get('card_id')}")
        lines.append(f"- List: {action.get('list') or 'UNKNOWN'}")
        lines.append(f"- Confidence: {action.get('confidence') or 'unknown'}")
        lines.append(f"- Record: {action.get('record_file') or 'UNKNOWN'}")
        lines.append(f"- Record kind: {action.get('record_kind') or 'unknown'}")
        lines.append(f"- Record year: {action.get('record_year') or 'unknown'}")
        lines.append(f"- Record path: {action.get('record_path') or 'UNKNOWN'}")
        lines.append(f"- Marker: {action.get('idempotency_marker') or 'missing'}")
        lines.append("")
        lines.append("Proposed comment:")
        lines.append("")
        lines.append("```text")
        lines.append(str(comment.get("text") or "").rstrip())
        lines.append("```")
        lines.append("")

    lines.extend(
        [
            "## Safety",
            "",
            "- Trello writes: false",
            "- Google Drive writes: false",
            "- Auto-attach: false",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


@mcp.tool()
def write_board_record_match_report(
    board: str = "memphis",
    record_kind: str = "any",
    include_complete: bool = False,
    list_names_json: str = "[]",
    limit_cards: int = 25,
    max_candidates_per_card: int = 2,
    min_relevance: float = 0.0,
) -> dict[str, Any]:
    """Write a local Markdown/JSON audit report for board record matches.

    This wraps review_board_record_matches and writes local files under the MCP
    audit artifact folder. It does not write to Trello or Google Drive.
    """
    review = review_board_record_matches(
        board=board,
        record_kind=record_kind,
        include_complete=include_complete,
        list_names_json=list_names_json,
        limit_cards=limit_cards,
        max_candidates_per_card=max_candidates_per_card,
        min_relevance=min_relevance,
    )
    audit_dir = _artifact_dir("audits")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    board_name = _safe_name((review.get("board") or {}).get("name") or board)
    selected = "-".join((review.get("scope") or {}).get("selected_lists") or ["all-active"])
    stem = _safe_name(f"board-record-matches-{board_name}-{selected}-{timestamp}")
    json_path = audit_dir / f"{stem}.json"
    md_path = audit_dir / f"{stem}.md"

    json_path.write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_format_board_record_match_report(review), encoding="utf-8")

    return {
        "ok": True,
        "markdown_path": str(md_path),
        "json_path": str(json_path),
        "summary": review.get("summary"),
        "scope": review.get("scope"),
        "safety": {
            "local_file_write": True,
            "trello_writes": False,
            "google_drive_writes": False,
            "auto_attach": False,
        },
    }


@mcp.tool()
def write_record_match_action_plan(
    board: str = "memphis",
    record_kind: str = "any",
    include_complete: bool = False,
    list_names_json: str = "[]",
    allowed_confidences_json: str = '["exact", "likely"]',
    limit_cards: int = 25,
    max_candidates_per_card: int = 2,
    min_relevance: float = 0.0,
) -> dict[str, Any]:
    """Write a local proposed-action plan for exact/likely record matches.

    This produces proposed Trello comment/attachment-review actions as local
    Markdown and JSON only. It does not write to Trello or Google Drive.
    """
    try:
        allowed_raw = json.loads(allowed_confidences_json or '["exact", "likely"]')
    except json.JSONDecodeError as exc:
        raise TrelloError("allowed_confidences_json must be a JSON array") from exc
    if not isinstance(allowed_raw, list):
        raise TrelloError("allowed_confidences_json must be a JSON array")
    allowed = {str(item).strip().lower() for item in allowed_raw if str(item).strip()}
    invalid = allowed - {"exact", "likely", "review", "weak", "no_match"}
    if invalid:
        raise TrelloError(f"Unsupported confidence values: {sorted(invalid)}")
    if not allowed:
        raise TrelloError("At least one allowed confidence is required")

    review = review_board_record_matches(
        board=board,
        record_kind=record_kind,
        include_complete=include_complete,
        list_names_json=list_names_json,
        limit_cards=limit_cards,
        max_candidates_per_card=max_candidates_per_card,
        min_relevance=min_relevance,
    )
    actions = _proposed_match_actions(review, allowed)
    payload = {
        "ok": True,
        "board": review.get("board"),
        "scope": {
            **(review.get("scope") or {}),
            "allowed_confidences": sorted(allowed),
        },
        "review_summary": review.get("summary"),
        "proposed_action_count": len(actions),
        "actions": actions,
        "safety": {
            "proposal_only": True,
            "local_file_write": True,
            "trello_writes": False,
            "google_drive_writes": False,
            "auto_attach": False,
        },
    }

    audit_dir = _artifact_dir("audits")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    board_name = _safe_name((review.get("board") or {}).get("name") or board)
    selected = "-".join((review.get("scope") or {}).get("selected_lists") or ["all-active"])
    confidence_label = "-".join(sorted(allowed))
    stem = _safe_name(f"record-match-action-plan-{board_name}-{selected}-{confidence_label}-{timestamp}")
    json_path = audit_dir / f"{stem}.json"
    md_path = audit_dir / f"{stem}.md"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_format_record_match_action_plan(review, actions), encoding="utf-8")

    return {
        "ok": True,
        "markdown_path": str(md_path),
        "json_path": str(json_path),
        "summary": {
            "proposed_action_count": len(actions),
            "allowed_confidences": sorted(allowed),
            "review_summary": review.get("summary"),
        },
        "safety": payload["safety"],
    }


def _load_action_plan(plan_json_path: str) -> dict[str, Any]:
    path = Path(plan_json_path).expanduser()
    if not path.exists():
        raise TrelloError(f"Action plan JSON not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TrelloError(f"Action plan JSON is invalid: {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("actions"), list):
        raise TrelloError("Action plan JSON must contain an actions array")
    return payload


def _comment_text_for_action(action: dict[str, Any]) -> str:
    for proposed in action.get("proposed_actions") or []:
        if proposed.get("type") == "comment" and proposed.get("text"):
            return str(proposed["text"])
    raise TrelloError(f"Action is missing proposed comment text: {action.get('card_name') or action.get('card_id')}")


def _marker_for_action(action: dict[str, Any]) -> str:
    marker = str(action.get("idempotency_marker") or "").strip()
    if marker:
        return marker
    card_id = str(action.get("card_id") or "").strip()
    record_path = str(action.get("record_path") or "").strip()
    if not card_id or not record_path:
        return ""
    return _record_match_marker(card_id, record_path)


def _comment_text_with_marker(action: dict[str, Any], marker: str) -> str:
    comment_text = _comment_text_for_action(action)
    if marker and marker not in comment_text:
        comment_text = f"{comment_text.rstrip()}\n- Marker: {marker}\n"
    return comment_text


@mcp.tool()
def apply_record_match_action_plan(
    plan_json_path: str,
    dry_run: bool = True,
    apply_token: str = "",
    limit_actions: int = 50,
    validate_trello_cards: bool = False,
) -> dict[str, Any]:
    """Validate or apply a record-match action plan.

    Defaults to dry-run. Real Trello comments are only created when dry_run is
    false and apply_token is exactly APPLY_RECORD_MATCH_ACTION_PLAN. This tool
    never creates Trello attachments; attachment entries remain review notes.
    Dry-runs validate local record paths by default and only read Trello cards
    when validate_trello_cards is true.
    """
    payload = _load_action_plan(plan_json_path)
    actions = payload.get("actions") or []
    actions = actions[: max(1, min(int(limit_actions), 100))]
    apply_enabled = not dry_run
    required_token = "APPLY_RECORD_MATCH_ACTION_PLAN"
    if apply_enabled and apply_token != required_token:
        raise TrelloError(f"Refusing Trello writes. Re-run with apply_token={required_token!r} to apply comments.")
    if apply_enabled:
        validate_trello_cards = True

    results = []
    errors = []
    for index, action in enumerate(actions, start=1):
        row = {
            "index": index,
            "card_id": action.get("card_id"),
            "card_name": action.get("card_name"),
            "card_url": action.get("card_url"),
            "confidence": action.get("confidence"),
            "record_path": action.get("record_path"),
            "idempotency_marker": _marker_for_action(action),
            "idempotency_marker_source": "plan" if action.get("idempotency_marker") else "computed",
            "validated": False,
            "applied": False,
            "planned_writes": [],
        }
        try:
            if not action.get("card_id"):
                raise TrelloError("Action missing card_id")
            marker = row["idempotency_marker"]
            if not marker:
                raise TrelloError("Action missing idempotency_marker")
            if validate_trello_cards:
                card = get_card(str(action["card_id"]))
                row["current_card_name"] = card.get("name")
                row["trello_card_validated"] = True
                row["duplicate_comment_found"] = _card_has_comment_marker(str(action["card_id"]), marker)
            else:
                row["current_card_name"] = None
                row["trello_card_validated"] = False
                row["trello_card_validation_skipped"] = True
                row["duplicate_comment_found"] = None
            record_path = Path(str(action.get("record_path") or "")).expanduser()
            row["record_exists"] = record_path.exists()
            if action.get("record_path") and not record_path.exists():
                raise TrelloError(f"Record path no longer exists: {record_path}")
            comment_text = _comment_text_with_marker(action, str(marker))
            row["planned_writes"].append({"type": "comment", "chars": len(comment_text)})
            row["planned_writes"].append(
                {
                    "type": "attachment_review",
                    "applied": False,
                    "note": "Attachments are not auto-created by this tool.",
                }
            )
            row["validated"] = True
            if apply_enabled:
                if row.get("duplicate_comment_found"):
                    row["applied"] = False
                    row["skipped"] = True
                    row["skip_reason"] = "duplicate_comment_marker_found"
                else:
                    comment = add_comment(str(action["card_id"]), comment_text)
                    row["applied"] = True
                    row["comment_action_id"] = comment.get("id")
        except Exception as exc:
            row["error"] = str(exc)[:500]
            errors.append(row)
        results.append(row)

    applied_count = sum(1 for item in results if item.get("applied"))
    validated_count = sum(1 for item in results if item.get("validated"))
    return {
        "ok": not errors,
        "mode": "dry_run" if dry_run else "apply",
        "plan_json_path": str(Path(plan_json_path).expanduser()),
        "summary": {
            "actions_seen": len(actions),
            "validated": validated_count,
            "applied_comments": applied_count,
            "errors": len(errors),
        },
        "results": results,
        "safety": {
            "dry_run": dry_run,
            "trello_comments_written": applied_count,
            "trello_attachments_written": 0,
            "requires_apply_token_for_writes": True,
            "required_apply_token": required_token,
            "validate_trello_cards": validate_trello_cards,
        },
    }


@mcp.tool()
def preview_stephen_bill(
    board: str = "memphis",
    list_name: str = "Jobs that I need to bill for",
    limit: int = 100,
    read_work_orders: bool = True,
) -> dict[str, Any]:
    """Build Stephen's read-only billing preview from Trello jobs ready to bill."""
    command = [
        "/Users/stephengodman/Candice-Code/bin/trello-preview-bill",
        "--json",
        "--board",
        board,
        "--list",
        list_name,
        "--limit",
        str(max(1, min(int(limit), 500))),
    ]
    if not read_work_orders:
        command.append("--no-work-orders")
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=180)
    output = result.stdout.strip() or result.stderr.strip()
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise TrelloError(f"billing preview returned invalid JSON: {output[:600]}") from exc
    payload.setdefault("ok", result.returncode == 0)
    payload.setdefault("safety", {})
    payload["safety"].update(
        {
            "read_only": True,
            "trello_writes": False,
            "google_drive_writes": False,
            "pi5_writes": False,
            "local_report_files_written": not bool(payload.get("error")),
            "secrets_returned": False,
        }
    )
    return payload


@mcp.tool()
def draft_stephen_bill(
    board: str = "memphis",
    list_name: str = "Jobs that I need to bill for",
    limit: int = 100,
    include_review: bool = False,
    read_work_orders: bool = False,
) -> dict[str, Any]:
    """Create a local PDF/CSV/Markdown draft bill from Trello jobs ready to bill."""
    command = [
        "/Users/stephengodman/Candice-Code/bin/trello-draft-bill",
        "--json",
        "--board",
        board,
        "--list",
        list_name,
        "--limit",
        str(max(1, min(int(limit), 500))),
    ]
    if include_review:
        command.append("--include-review")
    if read_work_orders:
        command.append("--read-work-orders")
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=240)
    output = result.stdout.strip() or result.stderr.strip()
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise TrelloError(f"bill draft returned invalid JSON: {output[:600]}") from exc
    payload.setdefault("ok", result.returncode == 0)
    payload.setdefault("safety", {})
    payload["safety"].update(
        {
            "trello_writes": False,
            "google_drive_writes": False,
            "pi5_writes": False,
            "local_bill_files_written": not bool(payload.get("error")),
            "secrets_returned": False,
        }
    )
    return payload


@mcp.tool()
def copy_board(source_board: str = "memphis", name: str | None = None, keep_from_source: str = "cards") -> dict[str, Any]:
    """Copy a Trello board. Defaults to copying Memphis Pool with cards."""
    source_id = _board_id(source_board)
    if not name:
        today = datetime.now().strftime("%Y-%m-%d")
        source_name = KNOWN_BOARDS.get(source_board, {}).get("name", source_board)
        name = f"{source_name} - Stephen Admin Copy {today}"
    return _request(
        "POST",
        "boards",
        params={
            "name": name,
            "idBoardSource": source_id,
            "keepFromSource": keep_from_source,
            "defaultLists": "false",
        },
    )


def _cli_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _run_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Trello MCP local operator commands")
    parser.add_argument("--runtime-diagnostics", action="store_true", help="Print redacted runtime diagnostics and exit.")
    parser.add_argument("--include-live-health", action="store_true", help="Include a read-only Trello health call with diagnostics.")
    parser.add_argument("--write-cutover-packet", action="store_true", help="Write the local Memphis cutover packet and exit.")
    parser.add_argument("--search-cards", action="store_true", help="Search Trello cards by name/description and exit.")
    parser.add_argument("--read-work-order", action="store_true", help="Read a work-order-like attachment from a Trello card and exit.")
    parser.add_argument("--attach-file", action="store_true", help="Attach a local file to a Trello card and exit. This writes to Trello.")
    parser.add_argument("--set-cover", action="store_true", help="Set a Trello card cover attachment and exit. This writes to Trello.")
    parser.add_argument("--primary-board", default="memphis")
    parser.add_argument("--comparison-board", default="legacy_memphis")
    parser.add_argument("--proposed-action", default="archive_legacy_memphis")
    parser.add_argument("--board", default="memphis")
    parser.add_argument("--query", default=None)
    parser.add_argument("--card-id", default=None)
    parser.add_argument("--card-query", default=None)
    parser.add_argument("--file-path", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--comment", default=None)
    parser.add_argument("--attachment-id", default=None)
    parser.add_argument("--attachment-filter", default="")
    parser.add_argument("--question", default="")
    parser.add_argument("--max-text-chars", type=int, default=6000)
    parser.add_argument("--include-complete", default="true")
    parser.add_argument("--limit-cards", type=int, default=1000)
    parser.add_argument("--sample-cards-per-list", type=int, default=8)
    args = parser.parse_args(argv)

    try:
        if args.runtime_diagnostics:
            payload = trello_runtime_diagnostics(include_live_health=args.include_live_health)
        elif args.search_cards:
            if not args.query:
                raise TrelloError("--query is required with --search-cards")
            payload = {
                "ok": True,
                "board": args.board,
                "query": args.query,
                "cards": search_cards(query=args.query, board=args.board, limit=args.limit_cards),
                "safety": {
                    "read_only": True,
                    "trello_writes": False,
                    "google_drive_writes": False,
                    "pi5_writes": False,
                },
            }
        elif args.read_work_order:
            payload = read_card_work_order(
                card_id=args.card_id,
                card_query=args.card_query,
                board=args.board,
                attachment_filter=args.attachment_filter,
                question=args.question,
                max_text_chars=args.max_text_chars,
            )
        elif args.attach_file:
            if not args.file_path:
                raise TrelloError("--file-path is required with --attach-file")
            payload = attach_file_to_card(
                file_path=args.file_path,
                card_id=args.card_id,
                card_query=args.card_query,
                board=args.board,
                name=args.name,
                comment=args.comment,
            )
        elif args.set_cover:
            if not args.card_id or not args.attachment_id:
                raise TrelloError("--card-id and --attachment-id are required with --set-cover")
            payload = set_card_cover(card_id=args.card_id, attachment_id=args.attachment_id)
        elif args.write_cutover_packet:
            payload = write_cutover_packet(
                primary_board=args.primary_board,
                comparison_board=args.comparison_board,
                proposed_action=args.proposed_action,
                include_complete=_cli_bool(args.include_complete),
                limit_cards=args.limit_cards,
                sample_cards_per_list=args.sample_cards_per_list,
            )
        else:
            parser.error("choose --runtime-diagnostics, --search-cards, --read-work-order, --attach-file, --set-cover, or --write-cutover-packet")
            return 2
    except Exception as exc:
        payload = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc)[:800],
            "safety": {
                "secrets_returned": False,
                "trello_writes": False,
                "google_drive_writes": False,
                "pi5_writes": False,
            },
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(_run_cli(sys.argv[1:]))
    mcp.run()
