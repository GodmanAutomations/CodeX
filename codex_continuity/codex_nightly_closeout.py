#!/usr/bin/env python3
"""Temporal-backed nightly closeout for the CodeX continuity vault."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from codex_continuity_vault import CodeXContinuityVault, DEFAULT_DB_PATH


LOCAL_TZ = ZoneInfo("America/Chicago")
DEFAULT_TEMPORAL_ADDRESS = "localhost:7233"
DEFAULT_TASK_QUEUE = "codex-continuity-closeout"
DEFAULT_WORKFLOW_ID = "codex-nightly-closeout"


def _loop_line(loop: dict[str, Any]) -> str:
    next_move = loop.get("next_move", "").strip()
    suffix = f" Next: {next_move}" if next_move else ""
    return f"{loop.get('text', '').strip()}{suffix}".strip()


def summarize_open_loops(open_loops: list[dict[str, Any]], *, now: datetime | None = None) -> tuple[str, list[str]]:
    close_time = now or datetime.now(LOCAL_TZ)
    today = close_time.astimezone(LOCAL_TZ).date().isoformat()
    todays = [
        loop for loop in open_loops
        if str(loop.get("created_at", "")).startswith(today)
        or str(loop.get("updated_at", "")).startswith(today)
    ]
    carried = [loop for loop in open_loops if loop not in todays]
    note_loops = [_loop_line(loop) for loop in todays + carried if _loop_line(loop)]

    if not open_loops:
        return (
            f"Nightly closeout for {today}: no open loops are recorded in the CodeX continuity vault.",
            [],
        )

    lines = [
        f"Nightly closeout for {today}: {len(open_loops)} open loop(s) remain in the CodeX continuity vault.",
        f"Updated today: {len(todays)}.",
        f"Carried forward: {len(carried)}.",
    ]
    if note_loops:
        lines.extend(["", "Open loops at close:", *(f"- {item}" for item in note_loops)])
    return "\n".join(lines), note_loops


def execute_closeout(
    *,
    db_path: Path | str = DEFAULT_DB_PATH,
    dry_run: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    vault = CodeXContinuityVault(db_path)
    open_loops = vault.list_open_loops(status="open", limit=100)
    summary, loop_lines = summarize_open_loops(open_loops, now=now)
    note = vault.write_tomorrow_note(
        title="CodeX Nightly Closeout",
        summary=summary,
        open_loops=loop_lines,
        mode_at_close="green" if not open_loops else "amber",
        next_clean_move=(
            "Start with codex_inner_weather, then handle the first open loop."
            if open_loops
            else "Run the startup pack and take the next real task Stephen names."
        ),
    )
    vacuum = vault.vacuum()
    return {
        "ok": True,
        "dry_run": dry_run,
        "db_path": str(Path(db_path).expanduser()),
        "open_loop_count": len(open_loops),
        "tomorrow_note": note,
        "vacuum": vacuum,
        "status": vault.status(),
    }


def next_closeout_delay_seconds(now: datetime) -> float:
    local_now = now.astimezone(LOCAL_TZ)
    target = local_now.replace(hour=23, minute=59, second=0, microsecond=0)
    if target <= local_now:
        target += timedelta(days=1)
    return max(0.0, (target.astimezone(timezone.utc) - local_now.astimezone(timezone.utc)).total_seconds())


@activity.defn(name="codex_nightly_closeout")
def codex_nightly_closeout_activity() -> dict[str, Any]:
    return execute_closeout()


@workflow.defn
class CodexNightlyCloseoutWorkflow:
    @workflow.run
    async def run(self) -> None:
        while True:
            await workflow.sleep(next_closeout_delay_seconds(workflow.now()))
            await workflow.execute_activity(
                codex_nightly_closeout_activity,
                schedule_to_close_timeout=timedelta(minutes=5),
            )
            await workflow.sleep(60)


async def run_worker(address: str, task_queue: str) -> None:
    client = await Client.connect(address)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[CodexNightlyCloseoutWorkflow],
        activities=[codex_nightly_closeout_activity],
    )
    await worker.run()


async def start_workflow(address: str, task_queue: str, workflow_id: str) -> str:
    client = await Client.connect(address)
    await client.start_workflow(
        CodexNightlyCloseoutWorkflow.run,
        id=workflow_id,
        task_queue=task_queue,
    )
    return workflow_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or host CodeX nightly closeout.")
    parser.add_argument("--dry-run", action="store_true", help="Execute closeout locally without a Temporal server.")
    parser.add_argument("--run-worker", action="store_true", help="Run the Temporal worker.")
    parser.add_argument("--start-workflow", action="store_true", help="Start the long-lived nightly workflow.")
    parser.add_argument("--temporal-address", default=DEFAULT_TEMPORAL_ADDRESS)
    parser.add_argument("--task-queue", default=DEFAULT_TASK_QUEUE)
    parser.add_argument("--workflow-id", default=DEFAULT_WORKFLOW_ID)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps(execute_closeout(db_path=args.db_path, dry_run=True), indent=2, sort_keys=True))
        return 0

    if args.start_workflow:
        workflow_id = asyncio.run(start_workflow(args.temporal_address, args.task_queue, args.workflow_id))
        print(json.dumps({"started_workflow_id": workflow_id, "task_queue": args.task_queue}, indent=2))
        return 0

    if args.run_worker:
        asyncio.run(run_worker(args.temporal_address, args.task_queue))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
