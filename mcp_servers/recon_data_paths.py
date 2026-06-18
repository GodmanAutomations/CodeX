"""Canonical paths for Stephen's recon data MCP."""
from __future__ import annotations

import os
from pathlib import Path


CODEX_ROOT = Path("/Users/stephengodman/CodeX")
DEFAULT_DATA_ROOT = Path("/Users/stephengodman/GodmanAutomations/data")
DATA_ROOT = Path(os.getenv("RECON_DATA_ROOT", str(DEFAULT_DATA_ROOT))).expanduser()

RAW_DIR = DATA_ROOT / "raw"
PROCESSED_DIR = DATA_ROOT / "processed"
OUTPUTS_DIR = DATA_ROOT / "outputs"
SCRIPTS_DIR = DATA_ROOT / "scripts"
BUILDOUT_DIR = DATA_ROOT / "recon_system_buildout"

LEGACY_DATA_ROOT = Path("/Users/stephengodman/data")
BILLING_RATES_PATH = Path(os.getenv("RECON_BILLING_RATES", str(CODEX_ROOT / "config" / "stephen-billing-rates.json"))).expanduser()
