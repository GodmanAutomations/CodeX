"""Isolated regression tests for the public health aggregator."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
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

    def test_duplicate_only_names_return_usage_error_without_running_checks(self):
        only, only_error = CHECK["parse_only"]("status,mcp_doctor,status,status")
        self.assertEqual(only, ["status", "mcp_doctor", "status", "status"])
        self.assertEqual(
            only_error, "--only included duplicate check name(s): status"
        )
        with patch.object(subprocess, "run") as run:
            payload, returncode = CHECK["build_payload"](
                "quick", False, only, only_error
            )
        self.assertEqual(returncode, 2)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["checks"], [])
        self.assertEqual(payload["summary"], {"passed": 0, "failed": 0})
        run.assert_not_called()

    def test_empty_only_name_returns_usage_error_without_running_checks(self):
        for raw in ("status,", ",status", "status,,mcp_doctor", "status, ,mcp_doctor"):
            with self.subTest(raw=raw):
                only, only_error = CHECK["parse_only"](raw)
                self.assertEqual(only_error, "--only included an empty check name")
                with patch.object(subprocess, "run") as run:
                    payload, returncode = CHECK["build_payload"](
                        "quick", False, only, only_error
                    )
                self.assertEqual(returncode, 2)
                self.assertFalse(payload["ok"])
                self.assertEqual(payload["checks"], [])
                self.assertEqual(payload["summary"], {"passed": 0, "failed": 0})
                run.assert_not_called()

    def test_missing_executable_returns_failed_check(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [str(Path(directory) / "missing-check")]
            for kind in ("json", "exit-only"):
                with self.subTest(kind=kind):
                    result = CHECK["run_check"](
                        "missing", command, kind=kind, timeout=5
                    )
                    self.assertFalse(result["ok"])
                    self.assertEqual(result["returncode"], 127)
                    self.assertEqual(result["command"], command)
                    self.assertTrue(result["error"])
                    self.assertNotIn("payload", result)
                    if kind == "exit-only":
                        self.assertEqual(result["stdout_tail"], "")
                    else:
                        self.assertNotIn("stdout_tail", result)

    def test_aggregation_continues_after_launch_failure(self):
        responses = [
            FileNotFoundError(2, "No such file or directory", "fixture-check"),
            subprocess.CompletedProcess(["fixture-check"], 0, '{"ok": true}', ""),
        ]
        with patch.object(subprocess, "run", side_effect=responses):
            payload, returncode = CHECK["build_payload"](
                "quick", False, ["status", "mcp_doctor"]
            )
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["summary"], {"passed": 1, "failed": 1})
        self.assertEqual(payload["checks"][0]["returncode"], 127)
        self.assertTrue(payload["checks"][1]["ok"])

    def test_safety_summary_only_retains_known_boolean_fields(self):
        known = {
            "git_writes": False,
            "file_deletes": True,
            "secrets_printed": False,
            "trello_writes": False,
            "secrets_returned": False,
            "pi5_writes": False,
        }
        marker = "synthetic-child-diagnostic"
        result = self.run_payload({"ok": True, "safety": {**known, marker: False}})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "child returned invalid safety data")
        self.assertEqual(result["payload"]["safety"], known)
        self.assertNotIn(marker, json.dumps(result))
        for value in (0, 1, "false", None, [], {}):
            with self.subTest(value=value):
                result = self.run_payload({"ok": True, "safety": {"git_writes": value}})
                self.assertEqual(result["payload"]["safety"], {})

    def test_known_child_safety_actions_fail_the_check_and_profile(self):
        known_keys = (
            "file_deletes",
            "git_writes",
            "pi5_writes",
            "secrets_printed",
            "secrets_returned",
            "trello_writes",
        )
        for key in known_keys:
            with self.subTest(key=key):
                result = self.run_payload({"ok": True, "safety": {key: True}})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "child reported an unsafe operation")
                self.assertTrue(result["payload"]["safety"][key])

        responses = [
            subprocess.CompletedProcess(
                ["fixture-check"],
                0,
                '{"ok": true, "safety": {"secrets_printed": true}}',
                "",
            ),
            subprocess.CompletedProcess(["fixture-check"], 0, '{"ok": true}', ""),
        ]
        with patch.object(subprocess, "run", side_effect=responses):
            payload, returncode = CHECK["build_payload"](
                "quick", False, ["status", "mcp_doctor"]
            )
        self.assertEqual(returncode, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["summary"], {"passed": 1, "failed": 1})

    def test_known_child_safety_actions_require_boolean_values(self):
        invalid_values = (0, 1, "false", "true", None, [], {})
        for key in sorted(CHECK["CHILD_SAFETY_KEYS"]):
            for value in invalid_values:
                with self.subTest(key=key, value=value):
                    result = self.run_payload({"ok": True, "safety": {key: value}})
                    self.assertFalse(result["ok"])
                    self.assertEqual(
                        result["error"], "child returned invalid safety data"
                    )
                    self.assertEqual(result["payload"]["safety"], {})

    def test_safety_field_requires_an_object(self):
        for value in (None, [], "safe", True, 0):
            with self.subTest(value=value):
                result = self.run_payload({"ok": True, "safety": value})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "child returned invalid safety data")
                self.assertNotIn("safety", result["payload"])

    def test_duplicate_json_object_members_fail_closed(self):
        outputs = (
            '{"ok":true,"safety":{"secrets_printed":true,"secrets_printed":false}}',
            '{"ok":true,"safety":{"secrets_printed":true},"safety":{}}',
        )
        for output in outputs:
            with self.subTest(output=output):
                response = subprocess.CompletedProcess(
                    ["fixture-check"], 0, output, ""
                )
                with patch.object(subprocess, "run", return_value=response):
                    result = CHECK["run_check"](
                        "fixture", ["fixture-check"], kind="json", timeout=5
                    )
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "command did not return valid JSON")
                self.assertNotIn("payload", result)

    def test_nonstandard_json_constants_fail_closed(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                response = subprocess.CompletedProcess(
                    ["fixture-check"],
                    0,
                    f'{{"ok":true,"metric":{constant}}}',
                    "",
                )
                with patch.object(subprocess, "run", return_value=response):
                    result = CHECK["run_check"](
                        "fixture", ["fixture-check"], kind="json", timeout=5
                    )
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "command did not return valid JSON")
                self.assertNotIn("payload", result)

    def test_aggregation_continues_after_json_recursion_limit(self):
        responses = [
            subprocess.CompletedProcess(["fixture-check"], 0, '{"ok":true}', ""),
            subprocess.CompletedProcess(["fixture-check"], 0, '{"ok":true}', ""),
        ]
        parsed_payloads = [RecursionError("maximum JSON nesting exceeded"), {"ok": True}]
        with patch.object(subprocess, "run", side_effect=responses):
            with patch.object(CHECK["json"], "loads", side_effect=parsed_payloads):
                payload, returncode = CHECK["build_payload"](
                    "quick", False, ["status", "mcp_doctor"]
                )
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["summary"], {"passed": 1, "failed": 1})
        self.assertTrue(payload["checks"][1]["ok"])
        result = payload["checks"][0]
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "command did not return valid JSON")
        self.assertNotIn("payload", result)

    def test_invalid_child_text_returns_failed_check(self):
        for stream in ("stdout", "stderr"):
            for kind in ("json", "exit-only"):
                with self.subTest(stream=stream, kind=kind):
                    result = CHECK["run_check"](
                        "invalid-text",
                        [sys.executable, "-c",
                         f"import sys; sys.{stream}.buffer.write(b'\\xff')"],
                        kind=kind,
                        timeout=5,
                    )
                    self.assertFalse(result["ok"])
                    self.assertEqual(result["returncode"], 1)
                    self.assertEqual(result["error"], "command output could not be decoded")
                    if kind == "exit-only":
                        self.assertEqual(result["stdout_tail"], "")
                    else:
                        self.assertNotIn("stdout_tail", result)
                    self.assertNotIn("stderr_tail", result)

    def test_aggregation_continues_after_invalid_child_text(self):
        responses = [
            UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
            subprocess.CompletedProcess(["fixture-check"], 0, '{"ok": true}', ""),
        ]
        with patch.object(subprocess, "run", side_effect=responses):
            payload, returncode = CHECK["build_payload"](
                "quick", False, ["status", "mcp_doctor"]
            )
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["summary"], {"passed": 1, "failed": 1})
        self.assertTrue(payload["checks"][1]["ok"])

    def test_invalid_json_does_not_forward_child_diagnostics(self):
        marker = "synthetic-child-diagnostic"
        for stdout, stderr in ((marker, ""), ("", marker), (marker, marker)):
            with self.subTest(stdout=bool(stdout), stderr=bool(stderr)):
                response = subprocess.CompletedProcess(["fixture-check"], 0, stdout, stderr)
                with patch.object(subprocess, "run", return_value=response):
                    result = CHECK["run_check"](
                        "fixture", ["fixture-check"], kind="json", timeout=5
                    )
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "command did not return valid JSON")
                self.assertNotIn(marker, json.dumps(result))
                self.assertNotIn("stdout_tail", result)
                self.assertNotIn("stderr_tail", result)

    @unittest.skipUnless(hasattr(sys, "get_int_max_str_digits"), "requires integer limit")
    def test_aggregation_continues_after_oversized_json_integer(self):
        original_limit = sys.get_int_max_str_digits()
        sys.set_int_max_str_digits(4300)
        self.addCleanup(sys.set_int_max_str_digits, original_limit)
        responses = [
            subprocess.CompletedProcess(
                ["fixture-check"], 0, '{"ok":true,"value":' + "9" * 4301 + "}", ""
            ),
            subprocess.CompletedProcess(["fixture-check"], 0, '{"ok":true}', ""),
        ]
        with patch.object(subprocess, "run", side_effect=responses):
            payload, returncode = CHECK["build_payload"](
                "quick", False, ["status", "mcp_doctor"]
            )
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["summary"], {"passed": 1, "failed": 1})
        self.assertTrue(payload["checks"][1]["ok"])
        result = payload["checks"][0]
        self.assertEqual(result["error"], "command did not return valid JSON")
        self.assertNotIn("payload", result)
        self.assertNotIn("9" * 100, json.dumps(payload))

    def test_json_timeout_does_not_forward_child_diagnostics(self):
        marker = "synthetic-child-diagnostic"
        for output in (marker, marker.encode()):
            with self.subTest(output_type=type(output).__name__):
                timeout = subprocess.TimeoutExpired(
                    ["fixture-check"], 5, output=output, stderr=output
                )
                responses = [
                    timeout,
                    subprocess.CompletedProcess(["fixture-check"], 0, '{"ok": true}', ""),
                ]
                with patch.object(subprocess, "run", side_effect=responses):
                    payload, returncode = CHECK["build_payload"](
                        "quick", False, ["status", "mcp_doctor"]
                    )
                self.assertEqual(returncode, 1)
                self.assertEqual(payload["summary"], {"passed": 1, "failed": 1})
                self.assertTrue(payload["checks"][1]["ok"])
                result = payload["checks"][0]
                self.assertEqual(result["returncode"], 124)
                self.assertEqual(result["error"], "timed out after 30s")
                self.assertNotIn(marker, json.dumps(payload))
                self.assertNotIn("stdout_tail", result)
                self.assertNotIn("stderr_tail", result)

    def test_exit_only_timeout_preserves_diagnostics(self):
        timeout = subprocess.TimeoutExpired(
            ["fixture-check"], 5, output=b"synthetic stdout", stderr=b"synthetic stderr"
        )
        with patch.object(subprocess, "run", side_effect=timeout):
            result = CHECK["run_check"](
                "fixture", ["fixture-check"], kind="exit-only", timeout=5
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["returncode"], 124)
        self.assertEqual(result["stdout_tail"], "synthetic stdout")
        self.assertEqual(result["stderr_tail"], "synthetic stderr")


if __name__ == "__main__":
    unittest.main()
