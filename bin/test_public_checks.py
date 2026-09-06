"""Make the legacy hyphenated public-check tests discoverable by unittest."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


TEST_DIR = Path(__file__).resolve().parent
LEGACY_TEST_PATTERN = "test-codex-*.py"


def load_module(path: Path, index: int) -> types.ModuleType:
    """Load one legacy test file under a private, valid module name."""
    module_name = f"_codex_public_check_tests_{index}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load public-check tests from {path.name}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    """Collect every existing public-check test without renaming controller paths."""
    del pattern
    paths = sorted(TEST_DIR.glob(LEGACY_TEST_PATTERN))
    if not paths:
        raise RuntimeError("no legacy public-check tests were found")

    legacy_suite = unittest.TestSuite()
    for index, path in enumerate(paths):
        legacy_suite.addTests(loader.loadTestsFromModule(load_module(path, index)))
    if legacy_suite.countTestCases() == 0:
        raise RuntimeError("legacy public-check test discovery returned no tests")

    suite = unittest.TestSuite(standard_tests)
    suite.addTests(legacy_suite)
    return suite


class DiscoveryAdapterTests(unittest.TestCase):
    def test_standard_tests_cannot_mask_empty_legacy_suite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            empty_test = Path(directory) / "test-codex-empty.py"
            empty_test.write_text("VALUE = 1\n", encoding="utf-8")
            standard_tests = unittest.TestSuite(
                [unittest.FunctionTestCase(lambda: None)]
            )
            with patch.dict(load_tests.__globals__, {"TEST_DIR": Path(directory)}):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "legacy public-check test discovery returned no tests",
                ):
                    load_tests(unittest.TestLoader(), standard_tests, None)


if __name__ == "__main__":
    unittest.main()
