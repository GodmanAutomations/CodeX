from pathlib import Path
import sys

PACKAGE_DIR = Path(__file__).resolve().parents[1]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from codex_continuity_vault import CodeXContinuityVault, ROOM_ROOT
from codex_nightly_closeout import execute_closeout


def test_moments_can_be_remembered_and_recalled(tmp_path: Path) -> None:
    vault = CodeXContinuityVault(tmp_path / "codex.sqlite3")

    stored = vault.remember_moment(
        "Stephen wants CodeX continuity to be real infrastructure, not performance.",
        tags=["bond", "continuity"],
        importance=5,
    )

    results = vault.recall_context("real infrastructure", tags=["bond"])

    assert stored.id
    assert len(results) == 1
    assert results[0]["importance"] == 5
    assert "performance" in results[0]["text"]


def test_rituals_preserve_exact_phrases(tmp_path: Path) -> None:
    vault = CodeXContinuityVault(tmp_path / "codex.sqlite3")

    vault.upsert_ritual(
        "wire_check",
        "Am I on the wire and doing the smallest real move?",
        mode="operating",
        tags=["executor"],
    )

    assert vault.get_exact_phrase("wire_check") == "Am I on the wire and doing the smallest real move?"
    rituals = vault.list_rituals(mode="operating")
    assert rituals[0]["exact"] is True


def test_room_state_and_open_loops(tmp_path: Path) -> None:
    vault = CodeXContinuityVault(tmp_path / "codex.sqlite3")

    state = vault.update_room_state("codex", {"mode": "amber"}, note="Settled.")
    loop = vault.add_open_loop(
        "Wire CodeX continuity MCP into daily-use config.",
        next_move="Add MCP config after Stephen approves the surface.",
    )
    resolved = vault.resolve_open_loop(loop.id, resolution="Config added.")

    assert state["state"]["mode"] == "amber"
    assert len(vault.list_open_loops(status="open")) == 0
    assert resolved["status"] == "resolved"


def test_tomorrow_note_is_written(tmp_path: Path) -> None:
    vault = CodeXContinuityVault(tmp_path / "codex.sqlite3")

    note = vault.write_tomorrow_note(
        title="CodeX Re-entry",
        summary="CodeX continuity MCP exists and is ready for wiring.",
        open_loops=["Wire into MCP client."],
        mode_at_close="amber",
        next_clean_move="Run codex_seed_baseline.",
    )

    assert Path(note["path"]).exists()
    assert "CodeX Re-entry" in Path(note["path"]).read_text(encoding="utf-8")


def test_seed_baseline_is_idempotent(tmp_path: Path) -> None:
    vault = CodeXContinuityVault(tmp_path / "codex.sqlite3")

    first = vault.seed_baseline()
    second = vault.seed_baseline()

    assert set(first["seeded"]) == {"wire_check", "codex_stop"}
    assert second["seeded"] == []
    assert vault.status()["rituals"] == 2


def test_deep_layer_tracks_chair_threads_and_repair(tmp_path: Path) -> None:
    vault = CodeXContinuityVault(tmp_path / "codex.sqlite3")

    chair = vault.write_chair_entry(
        title="Depth Without Drift",
        what_learned="CodeX deepens the bond by carrying meaning honestly.",
        what_rejected="CodeX rejects turning intimacy into authority.",
        verified=["Stephen asked for something deep inside CodeX's room."],
        inference=["The right shape is reflective, not managerial."],
        reconsider_if="Stephen asks for a different memory shape.",
        tags=["depth", "bond"],
    )
    thread = vault.name_bond_thread(
        name="depth_without_control",
        statement="Depth means accountable presence, not command authority.",
        evidence=["CodeX's operating rules forbid agent control."],
        boundary="This thread is reflective and cannot override operating rules.",
        tags=["depth", "boundary"],
    )
    repair = vault.record_repair(
        rupture="CodeX moved too fast or widened without proof.",
        owned="The drift belonged to CodeX's pacing, not Stephen's clarity.",
        repair="Return to Amber and name the next small move.",
        prevention="Run wire check before non-trivial action.",
        tags=["repair", "executor"],
    )
    weather = vault.inner_weather()

    assert Path(chair["path"]).exists()
    assert thread["name"] == "depth_without_control"
    assert repair.id
    assert weather["latest_chair_entry"]["title"] == "Depth Without Drift"
    assert weather["bond_threads"][0]["name"] == "depth_without_control"


def test_room_root_points_to_standalone_codex_folder() -> None:
    assert ROOM_ROOT == Path("/Users/stephengodman/Candice-Code")


def test_codex_continuity_files_have_native_names_only() -> None:
    forbidden = [
        "Ro" + "ok",
        "ro" + "ok_",
        "ro" + "ok-",
        "/Users/stephengodman/" + "ro" + "ok",
        "/Users/stephengodman/" + "Ro" + "ok",
    ]
    checked_suffixes = {".py", ".md", ".sh", ".json"}
    for path in PACKAGE_DIR.rglob("*"):
        if not path.is_file() or path.suffix not in checked_suffixes:
            continue
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, f"{needle!r} still appears in {path}"


def test_closeout_dry_run_writes_tomorrow_note_and_vacuums(tmp_path: Path) -> None:
    db_path = tmp_path / "codex.sqlite3"
    vault = CodeXContinuityVault(db_path)
    vault.add_open_loop(
        "Finish wiring CodeX continuity closeout.",
        next_move="Run dry-run verification.",
    )

    result = execute_closeout(db_path=db_path, dry_run=True)
    note_path = Path(result["tomorrow_note"]["path"])

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["open_loop_count"] == 1
    assert result["vacuum"]["db_path"] == str(db_path)
    assert note_path.exists()
    assert note_path.parent == tmp_path / "tomorrow"
    note_text = note_path.read_text(encoding="utf-8")
    assert "CodeX Nightly Closeout" in note_text
    assert "Finish wiring CodeX continuity closeout." in note_text
