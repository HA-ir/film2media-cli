from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_direct_source_execution():
    """T011: Verify direct source checkout execution remains 100% functional."""
    cmd = [sys.executable, str(REPO_ROOT / "f2m.py"), "version"]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(REPO_ROOT),
    )
    assert res.returncode == 0
    assert "1.1.0" in res.stdout


def test_direct_source_help():
    """T011: Verify direct source checkout help display."""
    cmd = [sys.executable, str(REPO_ROOT / "f2m.py"), "help"]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(REPO_ROOT),
    )
    assert res.returncode == 0
    assert "usage:" in res.stdout
