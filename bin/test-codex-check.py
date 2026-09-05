"""Isolated regression tests for the public health aggregator."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


CHECK = runpy.run_path(str(Path(__file__).with_name("codex-check")))
SAFE_JSON = '{"ok":true,"safety":{"git_writes":false}}'


class JsonCheckTests(unittest.TestCase):
    def run_payload(self, payload, returncode=0):
        result = subprocess.CompletedProcess(
            ["fixture-check"], returncode, json.dumps(payload), ""
        )
        with patch.object(CHECK["PROCESS_RUNNER"], "run", return_value=result):
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
            ({"ok": True, "safety": {"git_writes": False}}, 0, True),
            ({"ok": False}, 0, False),
            ({}, 0, False),
            ({"ok": 1}, 0, False),
            ({"ok": True, "safety": {"git_writes": False}}, 1, False),
        ):
            with self.subTest(payload=payload, returncode=returncode):
                self.assertEqual(self.run_payload(payload, returncode)["ok"], expected)

    def test_explicit_child_error_fails_closed_without_forwarding_diagnostics(self):
        marker = "synthetic-child-diagnostic"
        result = self.run_payload(
            {
                "ok": True,
                "error": {"detail": marker},
                "safety": {"git_writes": False},
            }
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "child reported an error")
        self.assertTrue(result["payload"]["error_present"])
        self.assertNotIn(marker, json.dumps(result))

    def test_aggregation_continues_after_non_object_json(self):
        responses = [
            subprocess.CompletedProcess(["fixture-check"], 0, "[]", ""),
            subprocess.CompletedProcess(["fixture-check"], 0, SAFE_JSON, ""),
        ]
        with patch.object(CHECK["PROCESS_RUNNER"], "run", side_effect=responses):
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
        with patch.object(CHECK["PROCESS_RUNNER"], "run") as run:
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
                with patch.object(CHECK["PROCESS_RUNNER"], "run") as run:
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
            subprocess.CompletedProcess(["fixture-check"], 0, SAFE_JSON, ""),
        ]
        with patch.object(CHECK["PROCESS_RUNNER"], "run", side_effect=responses):
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
            subprocess.CompletedProcess(["fixture-check"], 0, SAFE_JSON, ""),
        ]
        with patch.object(CHECK["PROCESS_RUNNER"], "run", side_effect=responses):
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

    def test_safety_field_is_required_and_nonempty(self):
        for payload in ({"ok": True}, {"ok": True, "safety": {}}):
            with self.subTest(payload=payload):
                result = self.run_payload(payload)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "child returned invalid safety data")

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
                with patch.object(CHECK["PROCESS_RUNNER"], "run", return_value=response):
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
                with patch.object(CHECK["PROCESS_RUNNER"], "run", return_value=response):
                    result = CHECK["run_check"](
                        "fixture", ["fixture-check"], kind="json", timeout=5
                    )
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "command did not return valid JSON")
                self.assertNotIn("payload", result)

    def test_aggregation_continues_after_json_recursion_limit(self):
        responses = [
            subprocess.CompletedProcess(["fixture-check"], 0, SAFE_JSON, ""),
            subprocess.CompletedProcess(["fixture-check"], 0, SAFE_JSON, ""),
        ]
        parsed_payloads = [
            RecursionError("maximum JSON nesting exceeded"),
            {"ok": True, "safety": {"git_writes": False}},
        ]
        with patch.object(CHECK["PROCESS_RUNNER"], "run", side_effect=responses):
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
            subprocess.CompletedProcess(["fixture-check"], 0, SAFE_JSON, ""),
        ]
        with patch.object(CHECK["PROCESS_RUNNER"], "run", side_effect=responses):
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
                with patch.object(CHECK["PROCESS_RUNNER"], "run", return_value=response):
                    result = CHECK["run_check"](
                        "fixture", ["fixture-check"], kind="json", timeout=5
                    )
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "command did not return valid JSON")
                self.assertNotIn(marker, json.dumps(result))
                self.assertNotIn("stdout_tail", result)
                self.assertNotIn("stderr_tail", result)

    def test_json_payload_must_come_from_stdout(self):
        marker = '{"ok":true,"safety":{"git_writes":false}}'
        response = subprocess.CompletedProcess(["fixture-check"], 0, "", marker)
        with patch.object(CHECK["PROCESS_RUNNER"], "run", return_value=response):
            result = CHECK["run_check"](
                "fixture", ["fixture-check"], kind="json", timeout=5
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "command did not return valid JSON")
        self.assertNotIn(marker, json.dumps(result))
        self.assertNotIn("payload", result)
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
            subprocess.CompletedProcess(["fixture-check"], 0, SAFE_JSON, ""),
        ]
        with patch.object(CHECK["PROCESS_RUNNER"], "run", side_effect=responses):
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

    def test_aggregation_continues_after_oversized_json_output(self):
        marker = "synthetic-oversized-diagnostic"
        responses = [
            subprocess.CompletedProcess(
                ["fixture-check"],
                0,
                json.dumps(
                    {
                        "ok": True,
                        "safety": {"git_writes": False},
                        "padding": marker + "x" * 1_000_001,
                    }
                ),
                "",
            ),
            subprocess.CompletedProcess(["fixture-check"], 0, SAFE_JSON, ""),
        ]
        with patch.object(CHECK["PROCESS_RUNNER"], "run", side_effect=responses):
            payload, returncode = CHECK["build_payload"](
                "quick", False, ["status", "mcp_doctor"]
            )
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["summary"], {"passed": 1, "failed": 1})
        self.assertTrue(payload["checks"][1]["ok"])
        result = payload["checks"][0]
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "command returned oversized JSON")
        self.assertNotIn(marker, json.dumps(payload))
        self.assertNotIn("payload", result)

    def test_real_child_is_stopped_at_output_limit(self):
        result = CHECK["run_check"](
            "oversized",
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(b'x' * 1000001)",
            ],
            kind="json",
            timeout=5,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["returncode"], 125)
        self.assertEqual(result["error"], "command returned oversized JSON")
        self.assertNotIn("stdout_tail", result)
        self.assertNotIn("stderr_tail", result)

    def test_real_child_is_stopped_when_stderr_exceeds_output_limit(self):
        marker = "synthetic-oversized-stderr-diagnostic"
        with tempfile.TemporaryDirectory() as directory:
            descendant_pid_path = Path(directory) / "descendant.pid"
            survival_path = Path(directory) / "descendant-survived"
            descendant_script = (
                "import pathlib, sys, time\n"
                "time.sleep(0.5)\n"
                "pathlib.Path(sys.argv[1]).write_text('survived')\n"
                "time.sleep(60)\n"
            )
            result = CHECK["run_check"](
                "oversized-stderr",
                [
                    sys.executable,
                    "-c",
                    (
                        "import pathlib, subprocess, sys, time; "
                        "descendant = subprocess.Popen("
                        "[sys.executable, '-c', sys.argv[2], sys.argv[3]]); "
                        "pathlib.Path(sys.argv[1]).write_text(str(descendant.pid)); "
                        "sys.stderr.buffer.write("
                        "b'synthetic-oversized-' + "
                        "b'stderr-diagnostic' + b'x' * 1000001); "
                        "sys.stderr.buffer.flush(); time.sleep(60)"
                    ),
                    str(descendant_pid_path),
                    descendant_script,
                    str(survival_path),
                ],
                kind="json",
                timeout=5,
            )
            descendant_pid = int(descendant_pid_path.read_text())
            time.sleep(0.75)
            try:
                self.assertFalse(result["ok"])
                self.assertEqual(result["returncode"], 125)
                self.assertEqual(result["error"], "command returned oversized JSON")
                self.assertNotIn(marker, json.dumps(result))
                self.assertNotIn("stdout_tail", result)
                self.assertNotIn("stderr_tail", result)
                self.assertFalse(survival_path.exists())
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    process_state = subprocess.run(
                        ["ps", "-o", "stat=", "-p", str(descendant_pid)],
                        check=False,
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    if not process_state or process_state.startswith("Z"):
                        break
                    time.sleep(0.05)
                else:
                    self.fail("descendant remained alive after process-group cleanup")
            finally:
                try:
                    os.kill(descendant_pid, 9)
                except ProcessLookupError:
                    pass

    def test_json_timeout_does_not_forward_child_diagnostics(self):
        marker = "synthetic-child-diagnostic"
        for output in (marker, marker.encode()):
            with self.subTest(output_type=type(output).__name__):
                timeout = subprocess.TimeoutExpired(
                    ["fixture-check"], 5, output=output, stderr=output
                )
                responses = [
                    timeout,
                    subprocess.CompletedProcess(["fixture-check"], 0, SAFE_JSON, ""),
                ]
                with patch.object(CHECK["PROCESS_RUNNER"], "run", side_effect=responses):
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
        with patch.object(CHECK["PROCESS_RUNNER"], "run", side_effect=timeout):
            result = CHECK["run_check"](
                "fixture", ["fixture-check"], kind="exit-only", timeout=5
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["returncode"], 124)
        self.assertEqual(result["stdout_tail"], "synthetic stdout")
        self.assertEqual(result["stderr_tail"], "synthetic stderr")

    def test_successful_exit_only_does_not_forward_diagnostics(self):
        marker = "synthetic-success-diagnostic"
        response = subprocess.CompletedProcess(
            ["fixture-check"], 0, marker, marker
        )
        with patch.object(CHECK["PROCESS_RUNNER"], "run", return_value=response):
            result = CHECK["run_check"](
                "fixture", ["fixture-check"], kind="exit-only", timeout=5
            )
        self.assertTrue(result["ok"])
        self.assertNotIn(marker, json.dumps(result))
        self.assertNotIn("stdout_tail", result)
        self.assertNotIn("stderr_tail", result)


if __name__ == "__main__":
    unittest.main()
