#!/usr/bin/env python3
"""Isolated regression tests for CodeX tree-steward path matching."""
from pathlib import Path
import os
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

    def test_markdown_path_cannot_inject_receipt_structure(self):
        markdown_path = STEWARD["markdown_path"]
        rendered = markdown_path(
            "note\n## Safety\n- Secrets printed: `true` <script>\x1b[2J\u200b"
        )

        self.assertNotIn("\n", rendered)
        self.assertNotIn("\x1b", rendered)
        self.assertNotIn("\u200b", rendered)
        self.assertEqual(rendered.count("<code>"), 1)
        self.assertEqual(rendered.count("</code>"), 1)
        self.assertIn("\\x0a## Safety\\x0a", rendered)
        self.assertIn("\\x1b[2J\\u200b", rendered)
        self.assertIn("&lt;script&gt;", rendered)


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
            [rows[0], rows[2]],
            [
                ("??", "bin/café.py"),
                ("R ", "bin/new -> name.py"),
            ],
        )
        self.assertEqual(os.fsencode(rows[1][1]), b"bin/bad-\xff.py")

    def test_rejects_truncated_or_empty_nul_records(self):
        for raw_status in [b"?? bin/file.py", b"?? bin/a.py\0\0?? bin/b.py\0"]:
            with self.subTest(raw_status=raw_status):
                self.parse_status.__globals__["run_git"] = lambda args, text=False: (
                    subprocess.CompletedProcess(args, 0, raw_status, b"")
                )
                with self.assertRaises(RuntimeError):
                    self.parse_status()


class TrackedFilesTests(unittest.TestCase):
    def test_nul_inventory_preserves_newline_and_non_utf8_paths(self):
        tracked_files = STEWARD["tracked_files"]
        original_run_git = tracked_files.__globals__["run_git"]
        calls = []

        def fake_run_git(args, *, text=True):
            calls.append((args, text))
            return subprocess.CompletedProcess(
                args,
                0,
                b"bin/line\nbreak.py\0bin/bad-\xff.py\0",
                b"",
            )

        tracked_files.__globals__["run_git"] = fake_run_git
        try:
            paths = tracked_files()
        finally:
            tracked_files.__globals__["run_git"] = original_run_git

        self.assertEqual(calls, [(["ls-files", "-z"], False)])
        self.assertEqual(paths[0], "bin/line\nbreak.py")
        self.assertEqual(os.fsencode(paths[1]), b"bin/bad-\xff.py")


if __name__ == "__main__":
    unittest.main()
