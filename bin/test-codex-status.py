"""Isolated regression tests for the public CodeX status dashboard."""
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch


STATUS = runpy.run_path(str(Path(__file__).with_name("codex-status")))


class JsonCommandTests(unittest.TestCase):
    def test_tool_count_tolerates_server_disappearing_during_probe(self):
        class DisappearingServer:
            def exists(self):
                return True

            def read_text(self, **_kwargs):
                raise FileNotFoundError("server disappeared during probe")

        with patch.dict(
            STATUS["count_trello_tools"].__globals__,
            {"TRELLO_SERVER": DisappearingServer()},
        ):
            self.assertEqual(STATUS["count_trello_tools"](), 0)

    def test_latest_files_skips_entry_that_disappears_during_scan(self):
        class StableFile:
            name = "stable.md"

            def is_file(self):
                return True

            def stat(self):
                return type("Stat", (), {"st_mtime": 10})()

            def __str__(self):
                return "/fixture/stable.md"

        class VanishedFile:
            name = "vanished.md"

            def is_file(self):
                return True

            def stat(self):
                raise FileNotFoundError("vanished during scan")

            def __str__(self):
                return "/fixture/vanished.md"

        class Folder:
            def exists(self):
                return True

            def iterdir(self):
                return iter([VanishedFile(), StableFile()])

        self.assertEqual(
            STATUS["latest_files"](Folder()),
            [{"name": "stable.md", "path": "/fixture/stable.md"}],
        )

    def test_text_output_escapes_terminal_controls(self):
        marker = "note\x1b]0;probe\x07\x9b\u202e.md"
        status = {
            "app_only": True,
            "codex_app_running": True,
            "onepassword_app_running": True,
            "environment": {},
            "trello_mcp": {"credential_source": marker},
            "tree": {"strict_blockers": marker},
            "pi": {"status": marker},
            "latest_work_notes": [{"name": marker}],
            "latest_tree_receipts": [{"name": marker}],
            "latest_handoffs": [{"name": marker}],
        }

        rendered = STATUS["format_status"](status)

        self.assertNotIn("\x1b", rendered)
        self.assertNotIn("\x07", rendered)
        self.assertNotIn("\x9b", rendered)
        self.assertNotIn("\u202e", rendered)
        self.assertIn(r"note\x1b]0;probe\x07\x9b\u202e.md", rendered)

    def test_json_payload_must_come_from_stdout(self):
        response = subprocess.CompletedProcess(
            ["fixture"],
            0,
            "",
            '{"ok": true, "strict_pass": true}',
        )
        with patch.dict(
            STATUS["json_command"].__globals__,
            {"run": lambda *_args, **_kwargs: response},
        ):
            result = STATUS["json_command"](["fixture"])

        self.assertFalse(result["ok"])
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["error"], "command did not return JSON on stdout")
        self.assertNotIn("strict_pass", result)

    def test_process_probe_errors_report_not_running(self):
        for error in (
            subprocess.TimeoutExpired(["pgrep"], 3),
            OSError("pgrep unavailable"),
        ):
            with self.subTest(error=type(error).__name__):
                with patch.dict(
                    STATUS["process_running"].__globals__,
                    {"run": lambda *_args, **_kwargs: (_ for _ in ()).throw(error)},
                ):
                    self.assertFalse(STATUS["process_running"]("fixture"))

    def test_non_object_json_returns_failed_status_without_crashing(self):
        response = subprocess.CompletedProcess(["fixture"], 0, "[]", "")
        with patch.dict(
            STATUS["json_command"].__globals__,
            {"run": lambda *_args, **_kwargs: response},
        ):
            result = STATUS["json_command"](["fixture"])

        self.assertEqual(
            result,
            {
                "ok": False,
                "error": "command did not return a JSON object",
                "returncode": 0,
            },
        )

    def test_duplicate_json_object_members_fail_closed(self):
        response = subprocess.CompletedProcess(
            ["fixture"],
            0,
            '{"ok": false, "ok": true}',
            "",
        )
        with patch.dict(
            STATUS["json_command"].__globals__,
            {"run": lambda *_args, **_kwargs: response},
        ):
            result = STATUS["json_command"](["fixture"])

        self.assertFalse(result["ok"])
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["error"], "command did not return valid JSON")

    def test_nonzero_exit_cannot_report_healthy_status(self):
        response = subprocess.CompletedProcess(
            ["fixture"],
            1,
            '{"ok": true, "status": "healthy", "returncode": 0}',
            "",
        )
        with patch.dict(
            STATUS["json_command"].__globals__,
            {"run": lambda *_args, **_kwargs: response},
        ):
            result = STATUS["json_command"](["fixture"])

        self.assertFalse(result["ok"])
        self.assertEqual(result["returncode"], 1)

    def test_tree_health_preserves_json_command_failure(self):
        failed_payload = {
            "ok": False,
            "strict_pass": True,
            "returncode": 1,
        }
        with patch.dict(
            STATUS["tree_health"].__globals__,
            {
                "TREE_STEWARD": Path(__file__),
                "json_command": lambda *_args, **_kwargs: failed_payload,
            },
        ):
            result = STATUS["tree_health"]()

        self.assertFalse(result["ok"])
        self.assertTrue(result["strict_pass"])

    def test_tree_health_rejects_malformed_collection_fields(self):
        malformed_payloads = (
            {"findings": 1, "ignored_advisories": []},
            {"findings": [], "ignored_advisories": None},
        )
        for malformed in malformed_payloads:
            with self.subTest(malformed=malformed):
                payload = {"ok": True, "strict_pass": True, **malformed}
                with patch.dict(
                    STATUS["tree_health"].__globals__,
                    {
                        "TREE_STEWARD": Path(__file__),
                        "json_command": lambda *_args, **_kwargs: payload,
                    },
                ):
                    result = STATUS["tree_health"]()

                self.assertFalse(result["ok"])
                self.assertEqual(result["findings_count"], 0)
                self.assertEqual(result["ignored_advisories_count"], 0)
                self.assertEqual(
                    result["error"],
                    "tree steward returned invalid collection data",
                )

    def test_malformed_op_resolution_fails_closed_without_crashing(self):
        for malformed in ([], None, {"status": []}):
            with self.subTest(malformed=malformed):
                with patch.dict(
                    STATUS["build_status"].__globals__,
                    {
                        "json_command": lambda *_args, **_kwargs: {
                            "ok": True,
                            "op_resolution": malformed,
                        },
                        "tree_health": lambda: {"ok": True},
                        "launchctl_present": lambda _name: False,
                        "any_process_running": lambda _patterns: False,
                        "process_running": lambda _pattern: False,
                        "count_trello_tools": lambda: 0,
                        "latest_files": lambda *_args, **_kwargs: [],
                    },
                ):
                    result = STATUS["build_status"](include_pi=False)

                self.assertFalse(result["ok"])
                self.assertEqual(
                    result["trello_mcp"],
                    {
                        "ok": False,
                        "credential_source": None,
                        "op_attempted": False,
                        "tool_count": 0,
                    },
                )


if __name__ == "__main__":
    unittest.main()
