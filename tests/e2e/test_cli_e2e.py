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


def test_e2e_cli_json_search_validity():
    """T030: Verify f2m search <query> --json produces valid JSON on stdout."""
    res = run_cli("search", "Inception", "--json")
    # In live or mocked environment, stdout must be valid JSON if exit code is 0
    if res.returncode == 0:
        data = json.loads(res.stdout)
        assert isinstance(data, list)
        assert "\033[" not in res.stdout
        assert "\r" not in res.stdout
    else:
        # If offline/unreachable, exit code is 4 or 6, and stderr has JSON error
        assert res.returncode in (4, 6)
        if res.returncode == 6:
            assert res.stdout.strip() == "[]"
        else:
            assert res.stdout == ""
            err_data = json.loads(res.stderr)
            assert err_data["error"] is True


def test_e2e_cli_plain_search_structure():
    """T030: Verify f2m search <query> --plain produces TSV on stdout."""
    res = run_cli("search", "Inception", "--plain")
    if res.returncode == 0:
        lines = [line for line in res.stdout.splitlines() if line.strip()]
        assert len(lines) > 0
        for line in lines:
            parts = line.split("\t")
            assert len(parts) >= 4
            assert parts[0] in ("movie", "series")
        assert "\033[" not in res.stdout


def test_e2e_cli_mutual_exclusivity_rejection():
    """T033: Verify combining --json and --plain yields exit code 2."""
    res = run_cli("search", "Inception", "--json", "--plain")
    assert res.returncode == 2
    assert res.stdout == ""
    assert "Cannot combine --json and --plain" in res.stderr


def test_e2e_cli_config_json_and_plain():
    """T032: Verify config inspection in JSON and plain modes."""
    # JSON
    res_json = run_cli("config", "--json")
    assert res_json.returncode == 0
    data = json.loads(res_json.stdout)
    assert "base_url" in data
    assert "mirrors" in data
    assert "player" in data

    # Plain
    res_plain = run_cli("config", "--plain")
    assert res_plain.returncode == 0
    assert "base_url=" in res_plain.stdout
    assert "\033[" not in res_plain.stdout


def test_e2e_cli_config_get_and_set(tmp_path):
    """T032: Verify config get and config set roundtrip."""
    fake_config = tmp_path / "custom.ini"
    env = {"F2M_CONFIG": str(fake_config)}

    # Set key in JSON mode
    res_set = run_cli("config", "set", "proxy", "http://127.0.0.1:8888", "--json", env=env)
    assert res_set.returncode == 0
    set_data = json.loads(res_set.stdout)
    assert set_data["success"] is True
    assert set_data["key"] == "proxy"
    assert set_data["value"] == "http://127.0.0.1:8888"

    # Get key in Plain mode
    res_get = run_cli("config", "get", "proxy", "--plain", env=env)
    assert res_get.returncode == 0
    assert res_get.stdout.strip() == "http://127.0.0.1:8888"


def test_e2e_cli_missing_and_unknown_args():
    """T033: Verify missing required arguments and unknown commands yield exit code 2."""
    # Missing URL
    res_url = run_cli("url")
    assert res_url.returncode == 2
    assert "usage: f2m url" in res_url.stderr

    # Missing config key
    res_cfg = run_cli("config", "get")
    assert res_cfg.returncode == 2
    assert "usage: f2m config get" in res_cfg.stderr

    # Unknown command
    res_unk = run_cli("invalidcommandxyz")
    assert res_unk.returncode == 2
    assert "unknown command 'invalidcommandxyz'" in res_unk.stderr


def test_e2e_cli_stream_isolation():
    """T034: Verify stdout contains only clean data while progress/diagnostics are isolated."""
    res = run_cli("version")
    assert res.returncode == 0
    assert res.stdout.strip() == "f2m 1.1.0"
    assert res.stderr == ""

    # JSON error on invalid key
    res_err = run_cli("config", "get", "nonexistent_key_xyz", "--json")
    assert res_err.returncode == 3
    assert res_err.stdout == ""  # stdout MUST be empty on failure!
    err_data = json.loads(res_err.stderr)
    assert err_data["error"] is True
    assert err_data["code"] == "CONFIG_ERROR"
    assert err_data["exit_code"] == 3


def test_e2e_cli_backward_compatibility():
    """T035: Verify help, version, and legacy invocations."""
    res_help = run_cli("help")
    assert res_help.returncode == 0
    assert "usage:" in res_help.stdout

    res_h = run_cli("-h")
    assert res_h.returncode == 0
    assert "usage:" in res_h.stdout

    res_version = run_cli("--version")
    assert res_version.returncode == 0
    assert "f2m 1.1.0" in res_version.stdout
