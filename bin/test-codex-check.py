"""Isolated regression tests for the public health aggregator."""
import json
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch


CHECK = runpy.run_path(str(Path(__file__).with_name("codex-check")))


class JsonCheckTests(unittest.TestCase):
    def run_payload(self, payload, returncode=0):
        result = subprocess.CompletedProcess(
            ["fixture-check"], returncode, json.dumps(payload), ""
        )
        with patch.object(subprocess, "run", return_value=result):
            return CHECK["run_check"](
                "fixture", ["fixture-check"], kind="json", timeout=5
            )

    def test_non_object_json_returns_failed_check(self):
        for payload in ([], [1], None, True, 0, "diagnostic text"):
            with self.subTest(payload=payload):
                result = self.run_payload(payload)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "command did not return a JSON object")
                self.assertNotIn("payload", result)

    def test_object_requires_explicit_ok_and_successful_exit(self):
        for payload, returncode, expected in (
            ({"ok": True}, 0, True),
            ({"ok": False}, 0, False),
            ({}, 0, False),
            ({"ok": 1}, 0, False),
            ({"ok": True}, 1, False),
        ):
            with self.subTest(payload=payload, returncode=returncode):
                self.assertEqual(self.run_payload(payload, returncode)["ok"], expected)

    def test_aggregation_continues_after_non_object_json(self):
        responses = [
            subprocess.CompletedProcess(["fixture-check"], 0, "[]", ""),
            subprocess.CompletedProcess(["fixture-check"], 0, '{"ok": true}', ""),
        ]
        with patch.object(subprocess, "run", side_effect=responses):
            payload, returncode = CHECK["build_payload"](
                "quick", False, ["status", "mcp_doctor"]
            )
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["summary"], {"passed": 1, "failed": 1})
        self.assertTrue(payload["checks"][1]["ok"])


if __name__ == "__main__":
    unittest.main()
