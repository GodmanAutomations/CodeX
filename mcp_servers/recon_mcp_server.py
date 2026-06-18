#!/usr/bin/env python3
"""Read-only MCP server for Stephen's recon data."""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import recon_data_store as store


mcp = FastMCP("recon")


@mcp.tool()
def recon_status() -> dict[str, Any]:
    """Show recon data-root health, index counts, reports, and stale path warnings."""
    return store.status()


@mcp.tool()
def list_recon_reports() -> dict[str, Any]:
    """List generated recon reports with readable titles and descriptions."""
    return {"ok": True, "reports": store.list_reports(), "safety": store.safety()}


@mcp.tool()
def read_recon_report(report_name: str, query: str = "", max_chars: int = 6000) -> dict[str, Any]:
    """Read a recon report safely, optionally returning only query snippets."""
    return store.read_report(report_name, query=query, max_chars=max_chars)


@mcp.tool()
def search_recon_records(
    query: str,
    sources: list[str] | None = None,
    limit: int = 25,
    include_reports: bool = True,
) -> dict[str, Any]:
    """Search processed recon CSVs and report text for jobs, bills, photos, messages, and Trello snapshots."""
    return store.search_records(query, sources=sources, limit=limit, include_reports=include_reports)


@mcp.tool()
def find_job_recon(query: str, limit_per_source: int = 8) -> dict[str, Any]:
    """Build one consolidated read-only job packet for a customer, card name, address, or bill term."""
    return store.find_job(query, limit_per_source=limit_per_source)


@mcp.tool()
def get_billing_queue(limit: int = 50) -> dict[str, Any]:
    """Return invoice-prep and billing-reconciliation candidates with supporting reports."""
    return store.billing_queue(limit=limit)


@mcp.tool()
def get_recon_billing_rates() -> dict[str, Any]:
    """Return Stephen's local billing rate table used by Recon pricing."""
    return store.load_billing_rates()


@mcp.tool()
def price_recon_job(work_text: str, context_text: str = "") -> dict[str, Any]:
    """Infer Stephen's likely bill amount for a work description using confirmed local rates."""
    return {"ok": True, "pricing": store.infer_billing_amount(work_text, context_text=context_text), "safety": store.safety()}


@mcp.tool()
def draft_recon_bill(limit: int = 100, include_verify_first: bool = True) -> dict[str, Any]:
    """Create a deduped read-only bill draft from Recon evidence and Stephen's local rates."""
    return store.build_recon_bill_draft(limit=limit, include_verify_first=include_verify_first)


@mcp.tool()
def find_unbilled_completed_jobs(limit: int = 50) -> dict[str, Any]:
    """Surface jobs that appear complete or billable but are not clearly billed."""
    return store.unbilled_completed_jobs(limit=limit)


@mcp.tool()
def find_bill_history(query: str, limit: int = 25) -> dict[str, Any]:
    """Search prior bill indexes, OCR text, and billing reports for duplicate-billing checks."""
    return store.bill_history(query, limit=limit)


@mcp.tool()
def get_photo_job_matches(query: str = "", limit: int = 50) -> dict[str, Any]:
    """Return existing photo-to-job matches without exposing raw photo libraries or raw GPS dumps."""
    return store.photo_job_matches(query=query, limit=limit)


@mcp.tool()
def refresh_recon_preview() -> dict[str, Any]:
    """Dry-run only: show what refresh scripts exist and why v1 will not execute them."""
    return store.refresh_preview()


if __name__ == "__main__":
    mcp.run()
