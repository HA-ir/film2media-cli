import os
from pathlib import Path
import pytest
from f2m.core.config import (
    ConfigManager,
    resolve_config_path,
    validate_key_value,
    CONFIG_DEFAULTS,
)
from f2m.core.exceptions import F2MConfigError


def test_resolve_config_path_default(monkeypatch, tmp_path):
    if os.name == "nt":
        pytest.skip("Test specifically covers POSIX XDG path resolution")
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("F2M_CONFIG", raising=False)
    monkeypatch.setattr(os, "name", "posix")

    path = resolve_config_path()
    assert path == (fake_home / ".config" / "f2m" / "config.ini").resolve()


def test_resolve_config_path_custom_xdg(monkeypatch, tmp_path):
    if os.name == "nt":
        pytest.skip("Test specifically covers POSIX XDG path resolution")
    custom_xdg = tmp_path / "custom_xdg"
    custom_xdg.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_xdg))
    monkeypatch.delenv("F2M_CONFIG", raising=False)
    monkeypatch.setattr(os, "name", "posix")

    path = resolve_config_path()
    assert path == (custom_xdg / "f2m" / "config.ini").resolve()


def test_resolve_config_path_f2m_config_env(monkeypatch, tmp_path):
    custom_file = tmp_path / "my_custom.ini"
    monkeypatch.setenv("F2M_CONFIG", str(custom_file))

    path = resolve_config_path()
    assert path == custom_file.resolve()


def test_config_precedence(tmp_path, monkeypatch):
    # 1. Config file on disk
    config_file = tmp_path / "test_config.ini"
    config_file.write_text(
        "[f2m]\nproxy = http://from-file:8080\nplayer = vlc\n", encoding="utf-8"
    )

    # 2. Environment variable overrides file
    monkeypatch.setenv("F2M_PROXY", "http://from-env:9090")

    # 3. CLI override overrides environment
    cli_overrides = {"proxy": "http://from-cli:1000"}

    cm = ConfigManager(custom_path=config_file, cli_overrides=cli_overrides)
    assert cm.get("proxy") == "http://from-cli:1000"
    assert cm.get("player") == "vlc"  # from file
    assert cm.get("base_url") == CONFIG_DEFAULTS["base_url"]  # from defaults


def test_explicit_empty_env_var_overrides(tmp_path, monkeypatch):
    config_file = tmp_path / "test_config.ini"
    config_file.write_text("[f2m]\nproxy = http://from-file:8080\n", encoding="utf-8")

    # Explicit empty proxy in env should disable proxy
    monkeypatch.setenv("F2M_PROXY", "")
    cm = ConfigManager(custom_path=config_file)
    assert cm.get("proxy") == ""


def test_validation():
    # Valid
    assert validate_key_value("player", "MPV") == "mpv"
    assert validate_key_value("base_url", "https://newsite.top/") == "https://newsite.top"
    assert validate_key_value("proxy", "http://127.0.0.1:8080") == "http://127.0.0.1:8080"

    # Invalid
    with pytest.raises(F2MConfigError, match="invalid player"):
        validate_key_value("player", "unknown_player")

    with pytest.raises(F2MConfigError, match="invalid base_url"):
        validate_key_value("base_url", "ftp://badurl.com")

    with pytest.raises(F2MConfigError, match="unknown key"):
        validate_key_value("nonexistent_key", "value")


def test_atomic_save_and_reload(tmp_path):
    config_file = tmp_path / "test_save.ini"
    cm = ConfigManager(custom_path=config_file)
    cm.set("download_dir", "~/MyDownloads")
    cm.set("player", "mpv")

    assert config_file.is_file()
    content = config_file.read_text(encoding="utf-8")
    assert "download_dir = ~/MyDownloads" in content
    assert "player = mpv" in content

    # Reload
    cm2 = ConfigManager(custom_path=config_file)
    assert cm2.get("download_dir") == "~/MyDownloads"
    assert cm2.get("player") == "mpv"
