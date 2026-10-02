from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_ci_workflow_structure():
    """T015: Verify CI workflow triggers, matrix, and permissions."""
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), "ci.yml must exist"
    content = ci_path.read_text(encoding="utf-8")

    # Triggers
    assert "branches: [master]" in content
    assert "pull_request:" in content

    # Least privilege
    assert "permissions:\n  contents: read" in content

    # Matrix
    assert 'python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]' in content
    assert "macos-latest" in content
    assert "windows-latest" in content

    # Smoke test gate
    assert "build-and-smoke-test:" in content
    assert "twine check --strict" in content


def test_release_workflow_structure():
    """T023: Verify release workflow triggers, least-privilege, and checksums."""
    release_path = REPO_ROOT / ".github" / "workflows" / "release.yml"
    assert release_path.exists(), "release.yml must exist"
    content = release_path.read_text(encoding="utf-8")

    # Must only trigger on tags
    assert 'tags: ["v*"]' in content
    assert "pull_request:" not in content

    # Scoped permissions
    assert "permissions:\n  contents: read" in content
    assert "permissions:\n      contents: write" in content

    # Checksums
    assert "sha256sum" in content
    assert "softprops/action-gh-release" in content
