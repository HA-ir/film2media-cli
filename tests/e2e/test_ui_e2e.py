import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_cli(*args, env=None) -> subprocess.CompletedProcess:
    """Helper to run f2m.py via subprocess."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    cmd = [sys.executable, str(REPO_ROOT / "f2m.py")] + list(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=full_env,
        cwd=str(REPO_ROOT),
    )


def test_e2e_ui_json_stream_isolation():
    """T024: Verify f2m search --json contains zero Rich ANSI escape sequences or markup."""
    res = run_cli("search", "Inception", "--json")
    if res.returncode == 0:
        data = json.loads(res.stdout)
        assert isinstance(data, list)
        assert "\033[" not in res.stdout
        assert "│" not in res.stdout
        assert "╭" not in res.stdout
        assert "⚡ F2M" not in res.stdout
    else:
        assert res.returncode in (4, 6)


def test_e2e_ui_plain_stream_isolation():
    """T025: Verify f2m search --plain contains zero Rich formatting or table borders."""
    res = run_cli("search", "Inception", "--plain")
    if res.returncode == 0:
        assert "\033[" not in res.stdout
        assert "│" not in res.stdout
        assert "╭" not in res.stdout
        for line in res.stdout.splitlines():
            if line.strip():
                assert "\t" in line


def test_e2e_ui_no_color_compliance():
    """T026: Verify that NO_COLOR=1 strips all ANSI color codes."""
    env = {"NO_COLOR": "1"}
    res = run_cli("help", env=env)
    assert res.returncode == 0
    assert "\033[" not in res.stdout
    assert "usage:" in res.stdout


def test_e2e_ui_exit_codes_preservation():
    """T027: Verify exit codes remain completely preserved in Phase 5."""
    # 0 for help
    assert run_cli("help").returncode == 0
    # 0 for version
    assert run_cli("version").returncode == 0
    # 2 for syntax conflict
    assert run_cli("search", "Inception", "--json", "--plain").returncode == 2
    # 2 for unknown command
    assert run_cli("unknowncmd123").returncode == 2
    # 3 for invalid config key
    assert run_cli("config", "get", "badkey", "--json").returncode == 3
