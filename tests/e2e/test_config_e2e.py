import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_cli(*args, env=None, cwd=None) -> subprocess.CompletedProcess:
    """Helper to run the CLI via subprocess in deterministic offline test environments."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    cmd = [sys.executable, str(REPO_ROOT / "f2m.py")] + list(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=full_env,
        cwd=cwd or str(REPO_ROOT),
    )


def test_e2e_config_persistence(tmp_path):
    """
    E2E-1: Configuration Persistence Workflow
    Run CLI -> set configuration -> verify user config location -> run CLI again -> verify value.
    """
    fake_home = tmp_path / "user_home"
    fake_home.mkdir()

    env = {"HOME": str(fake_home)}
    # Unset other overriding env vars
    for k in ("XDG_CONFIG_HOME", "F2M_CONFIG", "F2M_DOWNLOAD_DIR"):
        env.pop(k, None)

    # 1. Run f2m config set download_dir ~/Movies
    res = run_cli("config", "set", "download_dir", "~/Movies", env=env)
    assert res.returncode == 0
    assert "download_dir saved" in res.stdout

    # 2. Verify file was written to user XDG path
    xdg_file = fake_home / ".config" / "f2m" / "config.ini"
    assert xdg_file.is_file()
    assert "download_dir = ~/Movies" in xdg_file.read_text(encoding="utf-8")

    # 3. Subsequent CLI invocation loads the persisted value
    res2 = run_cli("config", env=env)
    assert res2.returncode == 0
    assert "~/Movies" in res2.stdout


def test_e2e_permission_safety(tmp_path):
    """
    E2E-2: Permission Safety Workflow (DEF-003 reproduction)
    Execute from a non-writable application/script directory.
    Verify no write attempted beside executable, and user config written successfully.
    """
    fake_home = tmp_path / "user_home"
    fake_home.mkdir()

    # Create temporary read-only application directory
    ro_app_dir = tmp_path / "ro_app"
    ro_app_dir.mkdir()
    shutil.copy(REPO_ROOT / "f2m.py", ro_app_dir / "f2m.py")
    shutil.copy(REPO_ROOT / "pyproject.toml", ro_app_dir / "pyproject.toml")
    shutil.copytree(REPO_ROOT / "f2m", ro_app_dir / "f2m")

    # Make ro_app_dir strictly read-only
    os.chmod(ro_app_dir, 0o555)

    try:
        env = {"HOME": str(fake_home)}
        cmd = [sys.executable, str(ro_app_dir / "f2m.py"), "config", "set", "proxy", "http://127.0.0.1:8080"]
        res = subprocess.run(cmd, capture_output=True, text=True, env=env)

        # Must succeed with exit code 0
        assert res.returncode == 0
        assert "proxy saved" in res.stdout

        # Verify NO file was written beside f2m.py in ro_app_dir
        assert not (ro_app_dir / "f2m.conf").exists()
        assert not (ro_app_dir / "config.ini").exists()

        # Verify written to user home XDG config
        xdg_file = fake_home / ".config" / "f2m" / "config.ini"
        assert xdg_file.is_file()
        assert "proxy = http://127.0.0.1:8080" in xdg_file.read_text(encoding="utf-8")
    finally:
        # Restore permissions for cleanup
        os.chmod(ro_app_dir, 0o777)


def test_e2e_legacy_migration(tmp_path):
    """
    E2E-3: Legacy Migration Workflow
    Create temporary legacy f2m.conf.
    Start CLI -> verify migration to XDG location -> verify original remains untouched -> verify second run idempotent.
    """
    fake_home = tmp_path / "user_home"
    fake_home.mkdir()

    # Create app dir with legacy f2m.conf
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    shutil.copy(REPO_ROOT / "f2m.py", app_dir / "f2m.py")
    shutil.copy(REPO_ROOT / "pyproject.toml", app_dir / "pyproject.toml")
    shutil.copytree(REPO_ROOT / "f2m", app_dir / "f2m")

    legacy_conf = app_dir / "f2m.conf"
    legacy_conf.write_text(
        "[f2m]\nbase_url = https://migrated-site.xyz\ndownload_dir = ~/CustomDownloads\n",
        encoding="utf-8",
    )

    env = {"HOME": str(fake_home)}
    cmd = [sys.executable, str(app_dir / "f2m.py"), "config"]

    # First run: migration happens
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert res.returncode == 0
    assert "https://migrated-site.xyz" in res.stdout

    # Verify XDG file created
    xdg_file = fake_home / ".config" / "f2m" / "config.ini"
    assert xdg_file.is_file()
    xdg_text = xdg_file.read_text(encoding="utf-8")
    assert "base_url = https://migrated-site.xyz" in xdg_text

    # Original legacy file remains untouched
    assert legacy_conf.is_file()

    # Modify XDG file to test idempotency
    xdg_file.write_text("[f2m]\nbase_url = https://user-modified.top\n", encoding="utf-8")

    # Second run: does not overwrite XDG file with legacy values
    res2 = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert res2.returncode == 0
    assert "https://user-modified.top" in res2.stdout


def test_e2e_environment_precedence(tmp_path):
    """
    E2E-4: Environment Precedence Workflow
    Verify F2M_PROXY and F2M_BASE_URL override on-disk configuration.
    """
    fake_home = tmp_path / "user_home"
    fake_home.mkdir()

    # Write persistent config with file values
    xdg_file = fake_home / ".config" / "f2m" / "config.ini"
    xdg_file.parent.mkdir(parents=True, exist_ok=True)
    xdg_file.write_text(
        "[f2m]\nbase_url = https://from-file.top\nproxy = http://file-proxy:8080\n",
        encoding="utf-8",
    )

    # 1. Override with env vars
    env = {
        "HOME": str(fake_home),
        "F2M_BASE_URL": "https://from-env.top",
        "F2M_PROXY": "http://env-proxy:9090",
    }
    res = run_cli("config", env=env)
    assert res.returncode == 0
    assert "https://from-env.top" in res.stdout
    assert "http://env-proxy:9090" in res.stdout

    # 2. Explicit empty proxy disables proxy
    env_empty = {
        "HOME": str(fake_home),
        "F2M_PROXY": "",
    }
    res_empty = run_cli("config", env=env_empty)
    assert res_empty.returncode == 0
    # Proxy line should be empty
    lines = [line.strip() for line in res_empty.stdout.splitlines() if "proxy" in line]
    assert len(lines) == 1
    assert lines[0].endswith("=")
