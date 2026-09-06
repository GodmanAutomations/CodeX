"""Make the legacy hyphenated public-check tests discoverable by unittest."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest


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

    suite = unittest.TestSuite(standard_tests)
    for index, path in enumerate(paths):
        suite.addTests(loader.loadTestsFromModule(load_module(path, index)))
    if suite.countTestCases() == 0:
        raise RuntimeError("legacy public-check test discovery returned no tests")
    return suite
