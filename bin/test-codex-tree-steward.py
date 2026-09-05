#!/usr/bin/env python3
"""Isolated regression tests for CodeX tree-steward path matching."""
from datetime import datetime, timezone
from pathlib import Path
import os
import runpy
import subprocess
import tempfile
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
    def test_inventory_failure_is_not_silently_treated_as_empty(self):
        tracked_files = STEWARD["tracked_files"]
        original_run_git = tracked_files.__globals__["run_git"]

        tracked_files.__globals__["run_git"] = lambda args, text=False: (
            subprocess.CompletedProcess(args, 128, b"", b"fatal: inventory unavailable\n")
        )
        try:
            with self.assertRaisesRegex(RuntimeError, "inventory unavailable"):
                tracked_files()
        finally:
            tracked_files.__globals__["run_git"] = original_run_git

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

    def test_rejects_truncated_or_empty_nul_records(self):
        tracked_files = STEWARD["tracked_files"]
        original_run_git = tracked_files.__globals__["run_git"]

        try:
            for raw_paths in [b"bin/a.py", b"bin/a.py\0\0bin/b.py\0"]:
                with self.subTest(raw_paths=raw_paths):
                    tracked_files.__globals__["run_git"] = lambda args, text=False: (
                        subprocess.CompletedProcess(args, 0, raw_paths, b"")
                    )
                    with self.assertRaises(RuntimeError):
                        tracked_files()
        finally:
            tracked_files.__globals__["run_git"] = original_run_git


class FileCountTests(unittest.TestCase):
    def test_does_not_traverse_directory_symlink_outside_root(self):
        file_count = STEWARD["file_count"]
        original_root = file_count.__globals__["ROOT"]

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            repository = temporary_root / "repository"
            outside_directory = temporary_root / "outside"
            repository.mkdir()
            outside_directory.mkdir()
            (outside_directory / "external.txt").write_text(
                "outside-content", encoding="utf-8"
            )
            (repository / "linked-directory").symlink_to(
                outside_directory, target_is_directory=True
            )

            file_count.__globals__["ROOT"] = repository
            try:
                self.assertIsNone(file_count("linked-directory"))
            finally:
                file_count.__globals__["ROOT"] = original_root


class WriteReceiptsTests(unittest.TestCase):
    def test_runs_in_same_second_keep_distinct_receipt_pairs(self):
        write_receipts = STEWARD["write_receipts"]
        original_receipt_root = write_receipts.__globals__["RECEIPT_ROOT"]
        payload = {
            "generated_at": "fixture",
            "root": "fixture",
            "dirty_count": 0,
            "strict_pass": True,
            "summary": {},
            "entries": [],
            "findings": [],
            "ignored_advisories": [],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            receipt_root = Path(temporary_directory)
            receipt_time = datetime(2026, 9, 5, 12, 18, 43, tzinfo=timezone.utc)
            write_receipts.__globals__["RECEIPT_ROOT"] = receipt_root
            try:
                first = dict(payload)
                second = dict(payload)
                write_receipts(first, receipt_time=receipt_time)
                write_receipts(second, receipt_time=receipt_time)
            finally:
                write_receipts.__globals__["RECEIPT_ROOT"] = original_receipt_root

            self.assertNotEqual(first["receipt_json"], second["receipt_json"])
            self.assertNotEqual(first["receipt_markdown"], second["receipt_markdown"])
            self.assertIn("20260905T121843Z", first["receipt_json"])
            self.assertIn("20260905T121843Z", second["receipt_json"])
            self.assertEqual(len(list(receipt_root.iterdir())), 4)


class ScanContentTests(unittest.TestCase):
    def test_allowed_value_only_exempts_the_assignment_that_contains_it(self):
        scan_content = STEWARD["scan_content"]
        policy = STEWARD["load_policy"]()
        original_root = scan_content.__globals__["ROOT"]
        original_candidates = scan_content.__globals__["content_scan_candidates"]

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            synthetic_value = "notarealsecretvalue" + "usedforpolicydoctor000000"
            (root / "probe.py").write_text(
                "api_key = 'APPLY_PHOTO_CARD_MATCH_PLAN'\n"
                f"api_key = '{synthetic_value}'  "
                "# APPLY_PHOTO_CARD_MATCH_PLAN\n",
                encoding="utf-8",
            )
            scan_content.__globals__["ROOT"] = root
            scan_content.__globals__["content_scan_candidates"] = (
                lambda policy, rows: ["probe.py"]
            )
            try:
                findings = scan_content(policy, [])
            finally:
                scan_content.__globals__["ROOT"] = original_root
                scan_content.__globals__["content_scan_candidates"] = original_candidates

        raw_findings = [
            finding for finding in findings if finding.name == "raw_secret_assignment"
        ]
        self.assertEqual([finding.line for finding in raw_findings], [2])


class ReadTextForScanTests(unittest.TestCase):
    def test_does_not_follow_symlinks_outside_scan_root(self):
        read_text_for_scan = STEWARD["read_text_for_scan"]
        original_root = read_text_for_scan.__globals__["ROOT"]

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            repository = temporary_root / "repository"
            outside_directory = temporary_root / "outside"
            repository.mkdir()
            outside_directory.mkdir()
            regular = repository / "regular.txt"
            outside = outside_directory / "external.txt"
            final_link = repository / "final-link"
            parent_link = repository / "parent-link"
            regular.write_text("ordinary-content", encoding="utf-8")
            outside.write_text("synthetic-sensitive-value", encoding="utf-8")
            final_link.symlink_to(outside)
            parent_link.symlink_to(outside_directory, target_is_directory=True)

            read_text_for_scan.__globals__["ROOT"] = repository
            try:
                self.assertEqual(read_text_for_scan(regular, 1024), "ordinary-content")
                self.assertIsNone(read_text_for_scan(final_link, 1024))
                self.assertIsNone(
                    read_text_for_scan(parent_link / outside.name, 1024)
                )
            finally:
                read_text_for_scan.__globals__["ROOT"] = original_root


if __name__ == "__main__":
    unittest.main()
