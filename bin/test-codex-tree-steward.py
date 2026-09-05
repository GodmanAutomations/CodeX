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
    def test_nul_status_preserves_unicode_and_rename_destination(self):
        parse_status = STEWARD["parse_status"]
        calls = []

        def fake_run_git(args):
            calls.append(args)
            return subprocess.CompletedProcess(
                args,
                0,
                "?? bin/café.py\0R  bin/new -> name.py\0bin/old.py\0",
                "",
            )

        original_run_git = parse_status.__globals__["run_git"]
        parse_status.__globals__["run_git"] = fake_run_git
        try:
            rows = parse_status()
        finally:
            parse_status.__globals__["run_git"] = original_run_git

        self.assertEqual(
            calls,
            [["status", "--porcelain=v1", "-z", "--untracked-files=all"]],
        )
        self.assertEqual(
            rows,
            [("??", "bin/café.py"), ("R ", "bin/new -> name.py")],
        )


if __name__ == "__main__":
    unittest.main()
