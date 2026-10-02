from __future__ import annotations

import re
from pathlib import Path

import pytest

import f2m
from f2m.cli.runner import VERSION as RUNNER_VERSION

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_packaging_and_version_parity():
    """T006 & T007: Verify single authoritative version synchronization across files."""
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"([^"]+)"', pyproject_text)
    assert match is not None, "Version not found in pyproject.toml"
    pyproject_version = match.group(1)

    assert f2m.VERSION == pyproject_version
    assert RUNNER_VERSION == pyproject_version
    assert pyproject_version == "1.1.0"


def test_console_script_entry_point():
    """T005 & T008: Verify f2m:main entry point callable and signature."""
    import inspect

    assert hasattr(f2m, "main"), "f2m module must define main() for console script"
    sig = inspect.signature(f2m.main)
    # Entry point must take 0 mandatory arguments
    assert len(sig.parameters) == 0


def test_package_discovery_configuration():
    """T001 & T002: Verify setuptools discovery configuration in pyproject.toml."""
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '[tool.setuptools.packages.find]' in pyproject_text
    assert 'include = ["f2m*"]' in pyproject_text
    assert 'exclude = ["specs*", "tests*", "assets*"]' in pyproject_text
    assert '[tool.setuptools]' in pyproject_text
    assert 'py-modules = ["f2m"]' in pyproject_text
    assert '[project.scripts]' in pyproject_text
    assert 'f2m = "f2m:main"' in pyproject_text
