"""Isolated regression tests for the public CodeX status dashboard."""
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch


STATUS = runpy.run_path(str(Path(__file__).with_name("codex-status")))


class JsonCommandTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
