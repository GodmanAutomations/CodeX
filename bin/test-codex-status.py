"""Isolated regression tests for the public CodeX status dashboard."""
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch


STATUS = runpy.run_path(str(Path(__file__).with_name("codex-status")))


class JsonCommandTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
