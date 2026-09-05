#!/usr/bin/env python3
"""Isolated regression tests for CodeX tree-steward path matching."""
from pathlib import Path
import runpy
import subprocess
import unittest


STEWARD = runpy.run_path(str(Path(__file__).with_name("codex-tree-steward")))


class MatchPatternTests(unittest.TestCase):
    def test_recursive_directory_pattern_respects_path_boundary(self):
        match_pattern = STEWARD["match_pattern"]

        self.assertTrue(match_pattern("mcp_servers", "mcp_servers/**"))
        self.assertTrue(match_pattern("mcp_servers/probe.py", "mcp_servers/**"))
        self.assertFalse(
            match_pattern("mcp_servers_evil/probe.py", "mcp_servers/**")
        )


class ParseStatusTests(unittest.TestCase):
    def setUp(self):
        parse_status = STEWARD["parse_status"]
        self.parse_status = parse_status
        self.original_run_git = parse_status.__globals__["run_git"]

    def tearDown(self):
        self.parse_status.__globals__["run_git"] = self.original_run_git

    def test_nul_status_preserves_paths_and_rename_destination(self):
        calls = []

        def fake_run_git(args, *, text=True):
            calls.append((args, text))
            return subprocess.CompletedProcess(
                args,
                0,
                b"?? bin/caf\xc3\xa9.py\0?? bin/bad-\xff.py\0"
                b"R  bin/new -> name.py\0bin/old.py\0",
                b"",
            )

        self.parse_status.__globals__["run_git"] = fake_run_git
        rows = self.parse_status()

        self.assertEqual(
            calls,
            [(["status", "--porcelain=v1", "-z", "--untracked-files=all"], False)],
        )
        self.assertEqual(
            rows,
            [
                ("??", "bin/café.py"),
                ("??", "bin/bad-\\udcff.py"),
                ("R ", "bin/new -> name.py"),
            ],
        )

    def test_rejects_truncated_or_empty_nul_records(self):
        for raw_status in [b"?? bin/file.py", b"?? bin/a.py\0\0?? bin/b.py\0"]:
            with self.subTest(raw_status=raw_status):
                self.parse_status.__globals__["run_git"] = lambda args, text=False: (
                    subprocess.CompletedProcess(args, 0, raw_status, b"")
                )
                with self.assertRaises(RuntimeError):
                    self.parse_status()


if __name__ == "__main__":
    unittest.main()
