"""Read-only helpers for the CodeX recon data MCP."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from recon_data_paths import BILLING_RATES_PATH, BUILDOUT_DIR, DATA_ROOT, LEGACY_DATA_ROOT, OUTPUTS_DIR, PROCESSED_DIR, RAW_DIR, SCRIPTS_DIR


MAX_CELL_CHARS = 700
CSV_SEARCH_FILES = {
    "billing_patterns": "billing_patterns.csv",
    "billing_reconciliation": "billing_reconciliation.csv",
    "bills": "bills_index.csv",
    "drive_bills": "drive_api_bills.csv",
    "drive_work_orders": "drive_api_work_orders.csv",
    "events": "events_extracted.csv",
    "invoice_prep": "invoice_prep_queue.csv",
    "messages": "messages_normalized.csv",
    "photo_matches": "photo_message_matches.csv",
    "photos": "photo_index.csv",
    "trello_actions": "trello_actions.csv",
    "trello_cards": "trello_cards.csv",
    "trello_work_order_attachments": "trello_work_order_attachments.csv",
    "work_order_jobs": "work_order_jobs.csv",
    "work_orders": "work_orders_index.csv",
}

REPORT_DESCRIPTIONS = {
    "JOB_PROOF_PACKETS.md": "Customer/job proof packets assembled from work orders, messages, photos, Trello, and bills.",
    "BILLING_READY_PACKETS.md": "Billing candidates grouped by send-now and verify-first status.",
    "INVOICE_PREP_QUEUE.md": "Manual invoice prep queue with known prices and blocking questions.",
    "MISSING_FROM_BILLING.md": "Jobs that may be complete but not clearly found in prior bills.",
    "ALREADY_BILLED_CHECK.md": "Prior-bill duplicate check report.",
    "LAST_BILL_CHECK.md": "Most recent bill comparison report.",
    "PHOTO_JOB_MATCHES.md": "Photo-to-job/message match summary without raw photo dumps.",
    "PHOTO_EVIDENCE_INDEX.md": "Photo evidence index summary.",
    "TRELLO_RECON.md": "Trello workflow state compared to other evidence.",
    "WORK_ORDER_INDEX.md": "Work order index and extracted job definitions.",
    "VERIFY_FIRST.md": "Items requiring review before action or billing.",
    "SUMMARY_INDEX.md": "High-level run summary.",
}

JOB_ALIAS_REPLACEMENTS = {
    "clairre": "claire",
    "nandrijog": "nandrajog",
    "norrris": "norris",
}

SOURCE_PRIORITY = {
    "invoice_prep_queue": 1,
    "billing_reconciliation": 2,
}


class ReconDataError(RuntimeError):
    pass


def load_billing_rates() -> dict[str, Any]:
    if not BILLING_RATES_PATH.exists():
        return {"ok": False, "source": str(BILLING_RATES_PATH), "base": {}, "notes": {}, "error": "rate file missing"}
    payload = json.loads(BILLING_RATES_PATH.read_text(encoding="utf-8"))
    payload.setdefault("ok", True)
    payload.setdefault("source", payload.get("source_path") or str(BILLING_RATES_PATH))
    payload["rate_file_path"] = str(BILLING_RATES_PATH)
    payload.setdefault("source_path", str(BILLING_RATES_PATH))
    payload["source_note"] = payload.get(
        "authority",
        "Local Stephen billing override used by Recon; no writes are made from this rate table.",
    )
    payload["safety"] = safety()
    return payload


def _rate_base() -> dict[str, int]:
    rates = load_billing_rates()
    base = rates.get("base") or {}
    normalized = {str(k): int(v) for k, v in base.items() if isinstance(v, int)}
    if "liner_install_inlays" in normalized and "liner_install_inlet" not in normalized:
        normalized["liner_install_inlet"] = normalized["liner_install_inlays"]
    if "liner_install_inlet" in normalized and "liner_install_inlays" not in normalized:
        normalized["liner_install_inlays"] = normalized["liner_install_inlet"]
    if "ab_measure" in normalized and "measure_ab" not in normalized:
        normalized["measure_ab"] = normalized["ab_measure"]
    if "measure_ab" in normalized and "ab_measure" not in normalized:
        normalized["ab_measure"] = normalized["measure_ab"]
    return normalized


def _pricing_text(*parts: object) -> str:
    return "\n".join(str(part or "") for part in parts).lower()


def infer_billing_amount(work_text: str, context_text: str = "") -> dict[str, Any]:
    """Infer Stephen's likely billing amount from local rate rules.

    This is an estimate for review, not an invoice write. It intentionally keeps
    uncertain work types as needs_rate instead of guessing.
    """
    base = _rate_base()
    text = _pricing_text(work_text, context_text)
    compact = re.sub(r"\s+", " ", text).strip()
    components: list[dict[str, Any]] = []
    warnings: list[str] = []
    work_keys: list[str] = []

    has_snap = bool(re.search(r"snap\s*-?\s*in", compact))
    has_measure = bool(re.search(r"\bmeasure(?:d|ment|ments|s)?\b", compact))
    has_install = bool(re.search(r"\binstall(?:ed|ation)?\b|\bliner replacement\b", compact))
    has_liner = "liner" in compact
    has_ab = bool(re.search(r"\ba/?b\b|\bab measurement\b", compact))
    if re.search(r"cheaper than a/?b|non[- ]?a/?b|not a/?b", compact):
        has_ab = False
    has_inlay = bool(re.search(r"\binlay\b|\bliner\s+over\s+step|\bsteps?\b|\bbench\b", compact) or has_ab)
    has_cover = bool(re.search(r"safety\s+cover|cover\s+install|ultra\s+loc|mesh\s+safety", compact))
    has_reset = bool(re.search(r"\breset\b|\bre[- ]?set\b", compact))
    has_anchor = bool(re.search(r"\banchor\b|\bwall anchors?\b|\brope anchors?\b", compact))
    no_charge = "no charge" in compact
    warranty = "warranty" in compact

    if has_snap:
        work_keys.append("snap_in")
        components.append({"key": "snap_in", "label": "Snap-in", "amount": base.get("snap_in")})
    elif has_measure and has_install and has_liner:
        measure_key = "ab_measure" if has_inlay else "measure"
        install_key = "liner_install_inlays" if has_inlay else "liner_install"
        work_keys.extend([measure_key, install_key])
        components.append({"key": measure_key, "label": "A/B measure" if measure_key == "ab_measure" else "Measure", "amount": base.get(measure_key)})
        components.append({"key": install_key, "label": "Inlay/liner-over-step install" if install_key == "liner_install_inlays" else "Regular liner install", "amount": base.get(install_key)})
    elif has_measure:
        key = "ab_measure" if has_inlay else "measure"
        work_keys.append(key)
        components.append({"key": key, "label": "A/B measure" if key == "ab_measure" else "Measure", "amount": base.get(key)})
    elif has_install and has_liner:
        key = "liner_install_inlays" if has_inlay else "liner_install"
        work_keys.append(key)
        components.append({"key": key, "label": "Inlay/liner-over-step install" if key == "liner_install_inlays" else "Regular liner install", "amount": base.get(key)})
    elif has_anchor:
        work_keys.append("anchor_repair")
        warnings.append("anchor work has no confirmed rate rule")
    elif has_cover:
        work_keys.append("safety_cover")
        components.append({"key": "safety_cover", "label": "Safety cover", "amount": base.get("safety_cover")})
    elif has_reset:
        work_keys.append("liner_reset")
        components.append({"key": "liner_reset", "label": "Liner reset", "amount": base.get("liner_reset")})
    else:
        work_keys.append("unknown")
        warnings.append("could not infer a confirmed work type")

    if no_charge:
        warnings.append("source text says no charge; verify whether Stephen should bill it anyway")
    if warranty:
        warnings.append("warranty mentioned; verify billability")
    if any(term in compact for term in ["travel", "drive upcharge", "far drive", "water valley", "corinth", "haul off", "hauloff"]):
        warnings.append("possible travel/haul-off/add-on amount not in confirmed base rates")

    missing_rates = [item["key"] for item in components if item.get("amount") is None]
    amount = sum(int(item["amount"]) for item in components if isinstance(item.get("amount"), int))
    if not components or missing_rates:
        amount_value: int | None = None
        price_status = "needs_rate"
    else:
        amount_value = amount
        price_status = "needs_review" if warnings else "priced"

    return {
        "work_keys": work_keys,
        "components": components,
        "amount": amount_value,
        "amount_display": f"${amount_value:,.2f}" if amount_value is not None else "NEEDS RATE",
        "price_status": price_status,
        "warnings": warnings,
        "rate_source": str(BILLING_RATES_PATH),
        "input_preview": _safe_text(work_text or context_text, limit=300),
    }


def _row_pricing(row: dict[str, str], *extra_parts: object) -> dict[str, Any]:
    work_text = _pricing_text(
        row.get("work_done"),
        row.get("work_type"),
        row.get("work_order_match"),
        row.get("file_name"),
        row.get("card_name"),
        row.get("name"),
        row.get("source_note"),
        *extra_parts,
    )
    inferred = infer_billing_amount(work_text)
    existing = row.get("base_price") or row.get("manual_review_amount") or ""
    if re.fullmatch(r"\d+(?:\.\d+)?", str(existing).strip()):
        inferred["existing_amount"] = int(float(str(existing).strip()))
        inferred["existing_amount_display"] = f"${inferred['existing_amount']:,.2f}"
    elif existing:
        inferred["existing_amount"] = None
        inferred["existing_amount_display"] = str(existing)
    return inferred


def add_pricing_to_rows(rows: list[dict[str, str]], *extra_parts: object) -> list[dict[str, Any]]:
    enriched = []
    for row in rows:
        enriched.append({**row, "pricing": _row_pricing(row, *extra_parts)})
    return enriched


def summarize_pricing(groups: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    counts = {"priced": 0, "needs_review": 0, "needs_rate": 0}
    priced_total = 0
    review_total = 0
    priced_items = []
    review_items = []
    for source, rows in groups.items():
        for row in rows:
            pricing = row.get("pricing") or {}
            status_value = str(pricing.get("price_status") or "needs_rate")
            if status_value not in counts:
                counts[status_value] = 0
            counts[status_value] += 1
            amount = pricing.get("amount")
            item = {
                "source": source,
                "job": row.get("job") or row.get("job_name") or row.get("name") or row.get("card_name") or "",
                "amount": amount,
                "amount_display": pricing.get("amount_display"),
                "price_status": status_value,
                "work_keys": pricing.get("work_keys") or [],
                "warnings": pricing.get("warnings") or [],
            }
            if isinstance(amount, int):
                if status_value == "priced":
                    priced_total += amount
                    priced_items.append(item)
                elif status_value == "needs_review":
                    review_total += amount
                    review_items.append(item)
    return {
        "counts": counts,
        "priced_total": priced_total,
        "priced_total_display": f"${priced_total:,.2f}",
        "review_total": review_total,
        "review_total_display": f"${review_total:,.2f}",
        "priced_items": priced_items[:25],
        "review_items": review_items[:25],
        "rate_source": str(BILLING_RATES_PATH),
    }


def normalize_job_name(value: object) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\b\d{3,6}\b", " ", text)
    text = re.sub(r"\b(memphis|collierville|germantown|cordova|bartlett|lakeland|tn|ms|ar)\b", " ", text)
    text = re.sub(r"\b(pool|liner|install|measure|measurement|snap|inlay|steps?|bench|road|rd|drive|dr|lane|ln|cove|cv|court|ct|street|st|avenue|ave)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    for wrong, right in JOB_ALIAS_REPLACEMENTS.items():
        text = re.sub(rf"\b{re.escape(wrong)}\b", right, text)
    return re.sub(r"\s+", " ", text).strip()


def row_job_name(row: dict[str, Any]) -> str:
    return (
        row.get("job")
        or row.get("job_name")
        or row.get("customer")
        or row.get("name")
        or row.get("card_name")
        or row.get("work_order_match")
        or ""
    )


def row_work_text(row: dict[str, Any]) -> str:
    return _pricing_text(
        row.get("work_done"),
        row.get("work_type"),
        row.get("work_order_match"),
        row.get("file_name"),
        row.get("source_note"),
        row.get("manual_review_note"),
        row.get("notes"),
    )


def bill_line_key(row: dict[str, Any]) -> str:
    pricing = row.get("pricing") or _row_pricing(row)
    keys = pricing.get("work_keys") or ["unknown"]
    return f"{normalize_job_name(row_job_name(row))}|{'+'.join(sorted(str(k) for k in keys))}"


def billing_priority(row: dict[str, Any]) -> dict[str, Any]:
    pricing = row.get("pricing") or _row_pricing(row)
    blob = " ".join(str(v or "").lower() for k, v in row.items() if k != "pricing")
    reasons: list[str] = []
    bucket = "ready_to_bill"

    if any(term in blob for term in ["not_done", "not done", "hold", "incomplete"]):
        bucket = "hold"
        reasons.append("row indicates not done/hold/incomplete")
    elif pricing.get("price_status") == "needs_rate" or pricing.get("amount") is None:
        bucket = "needs_rate"
        reasons.append("no confirmed rate inferred")
    elif "duplicate" in blob and not any(term in blob for term in ["duplicate_risk not found", "not found in ocr", "no match in ocr", "no match in latest bill"]):
        bucket = "possible_duplicate"
        reasons.append("duplicate wording needs review")
    elif pricing.get("price_status") == "needs_review" or pricing.get("warnings"):
        bucket = "verify_first"
        reasons.extend(pricing.get("warnings") or ["pricing marked needs_review"])
    elif "confirm not already billed" in blob:
        bucket = "verify_duplicate_first"
        reasons.append("manual queue asks to confirm not already billed")
    elif "verify" in blob:
        bucket = "verify_first"
        reasons.append("source row contains VERIFY marker")

    rank = {
        "ready_to_bill": 1,
        "verify_duplicate_first": 2,
        "verify_first": 3,
        "possible_duplicate": 4,
        "needs_rate": 5,
        "hold": 6,
    }.get(bucket, 9)
    return {"bucket": bucket, "rank": rank, "reasons": reasons}


def make_bill_line(row: dict[str, Any], source: str) -> dict[str, Any]:
    pricing = row.get("pricing") or _row_pricing(row)
    priority = billing_priority({**row, "pricing": pricing})
    return {
        "key": bill_line_key({**row, "pricing": pricing}),
        "source": source,
        "job": row_job_name(row),
        "work_text": _safe_text(row_work_text(row), limit=350),
        "amount": pricing.get("amount"),
        "amount_display": pricing.get("amount_display"),
        "price_status": pricing.get("price_status"),
        "work_keys": pricing.get("work_keys") or [],
        "components": pricing.get("components") or [],
        "priority": priority,
        "duplicate_risk": row.get("duplicate_risk") or "",
        "missing_billing_risk": row.get("missing_billing_risk") or "",
        "blocking_question": row.get("blocking_question") or "",
        "source_note": row.get("source_note") or row.get("manual_review_note") or "",
        "supporting_row": row,
    }


def build_recon_bill_draft(limit: int = 100, include_verify_first: bool = True) -> dict[str, Any]:
    capped_limit = max(1, min(int(limit), 300))
    invoice_rows = add_pricing_to_rows(read_csv_rows(PROCESSED_DIR / "invoice_prep_queue.csv", limit=capped_limit))
    recon_rows = add_pricing_to_rows(read_csv_rows(PROCESSED_DIR / "billing_reconciliation.csv", limit=capped_limit))

    manual_job_keys = {normalize_job_name(row_job_name(row)) for row in invoice_rows if normalize_job_name(row_job_name(row))}
    candidate_lines: list[dict[str, Any]] = []
    for row in invoice_rows:
        candidate_lines.append(make_bill_line(row, "invoice_prep_queue"))
    for row in recon_rows:
        job_key = normalize_job_name(row_job_name(row))
        if job_key in manual_job_keys:
            continue
        candidate_lines.append(make_bill_line(row, "billing_reconciliation"))

    deduped: dict[str, dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    for line in sorted(candidate_lines, key=lambda item: (SOURCE_PRIORITY.get(item["source"], 99), item["priority"]["rank"], item["job"])):
        key = line["key"]
        if key in deduped:
            duplicates.append({"kept": deduped[key], "duplicate": line})
            continue
        deduped[key] = line

    lines = list(deduped.values())
    if not include_verify_first:
        lines = [line for line in lines if line["priority"]["bucket"] == "ready_to_bill"]
    lines.sort(key=lambda item: (item["priority"]["rank"], normalize_job_name(item["job"]), item["work_keys"]))

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    totals: dict[str, int] = defaultdict(int)
    for line in lines:
        bucket = line["priority"]["bucket"]
        buckets[bucket].append(line)
        if isinstance(line.get("amount"), int):
            totals[bucket] += int(line["amount"])

    return {
        "ok": True,
        "mode": "read_only_bill_draft",
        "line_items": lines,
        "buckets": dict(buckets),
        "totals": {key: {"amount": value, "amount_display": f"${value:,.2f}"} for key, value in sorted(totals.items())},
        "summary": {
            "candidate_lines_seen": len(candidate_lines),
            "deduped_lines": len(lines),
            "duplicates_removed": len(duplicates),
            "manual_queue_jobs_preferred": len(manual_job_keys),
        },
        "duplicates": duplicates[:25],
        "rate_table": load_billing_rates(),
        "safety": safety(),
    }


def _safe_text(value: object, limit: int = MAX_CELL_CHARS) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[: max(0, limit - 1)].rstrip() + "..."
    return text


def _mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(DATA_ROOT))
    except ValueError:
        return str(path)


def read_csv_rows(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({str(k): _safe_text(v) for k, v in row.items()})
            if limit and len(rows) >= limit:
                break
    return rows


def csv_summary() -> list[dict[str, Any]]:
    out = []
    for name, file_name in sorted(CSV_SEARCH_FILES.items()):
        path = PROCESSED_DIR / file_name
        header: list[str] = []
        row_count = 0
        if path.exists():
            with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                row_count = sum(1 for _ in reader)
        out.append(
            {
                "name": name,
                "file": file_name,
                "exists": path.exists(),
                "rows": row_count,
                "columns": header,
                "modified_at": _mtime(path),
            }
        )
    return out


def stale_path_warnings() -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for script in sorted(SCRIPTS_DIR.glob("*.py")):
        text = script.read_text(encoding="utf-8", errors="replace")
        if "/Users/stephengodman/data" in text:
            warnings.append(
                {
                    "file": _rel(script),
                    "issue": "hard-coded legacy data root",
                    "legacy_path": str(LEGACY_DATA_ROOT),
                    "canonical_path": str(DATA_ROOT),
                }
            )
    return warnings


def status() -> dict[str, Any]:
    files_by_area = {}
    for label, root in {
        "raw": RAW_DIR,
        "processed": PROCESSED_DIR,
        "outputs": OUTPUTS_DIR,
        "scripts": SCRIPTS_DIR,
        "buildout": BUILDOUT_DIR,
    }.items():
        files_by_area[label] = sum(1 for p in root.rglob("*") if p.is_file()) if root.exists() else 0

    reports = list_reports()
    csvs = csv_summary()
    return {
        "ok": DATA_ROOT.exists(),
        "data_root": str(DATA_ROOT),
        "canonical_data_root": str(DATA_ROOT),
        "billing_rates": {
            "source": str(BILLING_RATES_PATH),
            "exists": BILLING_RATES_PATH.exists(),
            "version": load_billing_rates().get("version"),
            "authority": load_billing_rates().get("authority"),
            "base": load_billing_rates().get("base", {}),
        },
        "legacy_data_root_exists": LEGACY_DATA_ROOT.exists(),
        "directories": {
            "raw": str(RAW_DIR),
            "processed": str(PROCESSED_DIR),
            "outputs": str(OUTPUTS_DIR),
            "scripts": str(SCRIPTS_DIR),
            "buildout": str(BUILDOUT_DIR),
        },
        "files_by_area": files_by_area,
        "reports": {"count": len(reports), "newest_modified_at": max((r["modified_at"] for r in reports if r["modified_at"]), default=None)},
        "processed_indexes": csvs,
        "stale_path_warnings": stale_path_warnings(),
        "safety": safety(read_only=True),
    }


def safety(read_only: bool = True) -> dict[str, Any]:
    return {
        "read_only": read_only,
        "trello_writes": False,
        "google_drive_writes": False,
        "messages_writes": False,
        "photos_writes": False,
        "raw_messages_exposed": False,
        "raw_photos_exposed": False,
        "secrets_returned": False,
    }


def list_reports() -> list[dict[str, Any]]:
    reports = []
    for path in sorted(OUTPUTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        heading = next((line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")), path.stem.replace("_", " ").title())
        reports.append(
            {
                "name": path.name,
                "title": heading,
                "description": REPORT_DESCRIPTIONS.get(path.name, heading),
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "modified_at": _mtime(path),
            }
        )
    return reports


def resolve_report(name: str) -> Path:
    q = (name or "").strip()
    if not q:
        raise ReconDataError("report name is required")
    candidates = {p.name.lower(): p for p in OUTPUTS_DIR.glob("*.md")}
    if q.lower() in candidates:
        return candidates[q.lower()]
    stem = q.lower().replace(" ", "_").removesuffix(".md")
    for path in candidates.values():
        if path.stem.lower() == stem or stem in path.stem.lower() or stem in path.name.lower():
            return path
    raise ReconDataError(f"report not found: {name}")


def read_report(name: str, query: str = "", max_chars: int = 6000) -> dict[str, Any]:
    path = resolve_report(name)
    text = path.read_text(encoding="utf-8", errors="replace")
    q = (query or "").strip().lower()
    if q:
        snippets = snippets_for_text(text, q, max_chars=max_chars)
        returned = "\n\n---\n\n".join(snippets)
    else:
        returned = text[: max(200, min(max_chars, 20000))]
    truncated = len(returned) < len(text) if not q else len(returned) >= max_chars
    return {
        "ok": True,
        "report": path.name,
        "title": next((line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")), path.stem),
        "query": query,
        "text": returned,
        "truncated": truncated,
        "size_bytes": path.stat().st_size,
        "modified_at": _mtime(path),
        "safety": safety(),
    }


def snippets_for_text(text: str, query: str, max_chars: int = 6000) -> list[str]:
    q = query.lower()
    snippets = []
    for match in re.finditer(re.escape(q), text.lower()):
        start = max(0, match.start() - 700)
        end = min(len(text), match.end() + 1200)
        snippets.append(text[start:end].strip())
        if sum(len(s) for s in snippets) >= max_chars:
            break
    return snippets or []


def search_rows(query: str, sources: Iterable[str] | None = None, limit: int = 25) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        raise ReconDataError("query is required")
    source_set = {s.strip() for s in sources or [] if s.strip()}
    results = []
    for source, file_name in sorted(CSV_SEARCH_FILES.items()):
        if source_set and source not in source_set:
            continue
        path = PROCESSED_DIR / file_name
        for row in read_csv_rows(path):
            haystack = " ".join(str(v) for v in row.values()).lower()
            if q in haystack:
                results.append({"source": source, "file": file_name, "row": row})
                if len(results) >= limit:
                    return results
    return results


def search_reports(query: str, limit: int = 10, max_chars_per_result: int = 1200) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        raise ReconDataError("query is required")
    results = []
    for report in list_reports():
        path = Path(report["path"])
        text = path.read_text(encoding="utf-8", errors="replace")
        if q not in text.lower():
            continue
        snippets = snippets_for_text(text, q, max_chars=max_chars_per_result)
        results.append({**report, "snippets": snippets[:2]})
        if len(results) >= limit:
            break
    return results


def search_records(query: str, sources: list[str] | None = None, limit: int = 25, include_reports: bool = True) -> dict[str, Any]:
    row_limit = max(1, min(int(limit), 75))
    rows = search_rows(query, sources=sources, limit=row_limit)
    report_results = search_reports(query, limit=min(10, row_limit)) if include_reports else []
    return {
        "ok": True,
        "query": query,
        "sources": sources or "all",
        "csv_matches": rows,
        "report_matches": report_results,
        "counts": {"csv": len(rows), "reports": len(report_results)},
        "safety": safety(),
    }


def find_job(query: str, limit_per_source: int = 8) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        raise ReconDataError("query is required")
    sources = [
        "work_order_jobs",
        "work_orders",
        "trello_cards",
        "trello_work_order_attachments",
        "events",
        "photo_matches",
        "bills",
        "billing_reconciliation",
        "invoice_prep",
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in search_rows(q, sources=sources, limit=200):
        bucket = result["source"]
        if len(grouped[bucket]) < limit_per_source:
            grouped[bucket].append(result["row"])
    reports = search_reports(q, limit=6)
    priced_packet = {}
    for source, rows in grouped.items():
        if source in {"work_order_jobs", "billing_reconciliation", "invoice_prep", "trello_cards", "trello_work_order_attachments"}:
            priced_packet[source] = add_pricing_to_rows(rows, q)
        else:
            priced_packet[source] = rows
    return {
        "ok": True,
        "query": q,
        "packet": priced_packet,
        "pricing_summary": summarize_pricing(priced_packet),
        "report_matches": reports,
        "summary": {key: len(value) for key, value in grouped.items()},
        "safety": safety(),
    }


def billing_queue(limit: int = 50) -> dict[str, Any]:
    capped_limit = max(1, min(int(limit), 200))
    invoice_rows = read_csv_rows(PROCESSED_DIR / "invoice_prep_queue.csv", limit=capped_limit)
    recon_rows = read_csv_rows(PROCESSED_DIR / "billing_reconciliation.csv", limit=capped_limit)
    priced_invoice_rows = add_pricing_to_rows(invoice_rows)
    priced_recon_rows = add_pricing_to_rows(recon_rows)
    return {
        "ok": True,
        "rate_table": load_billing_rates(),
        "invoice_prep_queue": priced_invoice_rows,
        "billing_reconciliation": priced_recon_rows,
        "pricing_summary": summarize_pricing({"invoice_prep_queue": priced_invoice_rows, "billing_reconciliation": priced_recon_rows}),
        "reports": {
            "invoice_prep": read_report("INVOICE_PREP_QUEUE.md", max_chars=5000),
            "billing_ready": read_report("BILLING_READY_PACKETS.md", max_chars=5000),
            "missing_from_billing": read_report("MISSING_FROM_BILLING.md", max_chars=5000),
        },
        "safety": safety(),
    }


def unbilled_completed_jobs(limit: int = 50) -> dict[str, Any]:
    rows = read_csv_rows(PROCESSED_DIR / "billing_reconciliation.csv")
    candidates = []
    for row in rows:
        blob = " ".join(str(v).lower() for v in row.values())
        if any(term in blob for term in ["missing", "send", "verify first", "needs billing"]) and "duplicate" not in blob:
            candidates.append({**row, "pricing": _row_pricing(row)})
        if len(candidates) >= max(1, min(int(limit), 200)):
            break
    return {
        "ok": True,
        "candidates": candidates,
        "pricing_summary": summarize_pricing({"candidates": candidates}),
        "missing_from_billing_report": read_report("MISSING_FROM_BILLING.md", max_chars=7000),
        "safety": safety(),
    }


def bill_history(query: str, limit: int = 25) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        raise ReconDataError("query is required")
    matches = search_records(q, sources=["bills", "billing_patterns", "billing_reconciliation", "drive_bills"], limit=limit, include_reports=True)
    ocr_matches = []
    for path in sorted((PROCESSED_DIR / "bill_ocr_text").glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if q.lower() in text.lower():
            ocr_matches.append({"file": path.name, "path": str(path), "snippets": snippets_for_text(text, q, max_chars=1500)})
            if len(ocr_matches) >= min(int(limit), 25):
                break
    matches["ocr_text_matches"] = ocr_matches
    matches["safety"] = safety()
    return matches


def photo_job_matches(query: str = "", limit: int = 50) -> dict[str, Any]:
    rows = read_csv_rows(PROCESSED_DIR / "photo_message_matches.csv")
    if query:
        q = query.lower()
        rows = [row for row in rows if q in " ".join(row.values()).lower()]
    rows = rows[: max(1, min(int(limit), 200))]
    return {
        "ok": True,
        "matches": rows,
        "photo_report": read_report("PHOTO_JOB_MATCHES.md", query=query, max_chars=5000) if query else read_report("PHOTO_JOB_MATCHES.md", max_chars=5000),
        "safety": safety(),
    }


def refresh_preview() -> dict[str, Any]:
    scripts = []
    for path in sorted(SCRIPTS_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        writes_local = any(token in text for token in [".write_text(", "write_csv(", ".open('w'", '.open("w"', "writerow", "writerows"])
        side_effects = []
        if "Messages" in text or "imessage" in text.lower():
            side_effects.append("messages_backup_or_read")
        if "urllib.request.urlopen" in text or "https://api.trello.com" in text:
            side_effects.append("network_read")
        if "osascript" in text or "send " in text:
            side_effects.append("may_send_message")
        if "/Users/stephengodman/data" in text:
            side_effects.append("stale_legacy_path")
        scripts.append(
            {
                "script": path.name,
                "path": str(path),
                "writes_local_outputs": writes_local,
                "side_effects": side_effects,
                "v1_action": "do_not_run_from_mcp" if "may_send_message" in side_effects else "dry_run_review_only",
            }
        )
    return {
        "ok": True,
        "mode": "dry_run_preview_only",
        "would_run": [],
        "scripts": scripts,
        "stale_path_warnings": stale_path_warnings(),
        "safety": safety(),
    }
