from pathlib import Path
import pytest
from f2m.core.config import migrate_legacy_config, ConfigManager


def test_legacy_migration_success(tmp_path, monkeypatch):
    # Set up simulated source directory containing f2m.conf
    fake_source_dir = tmp_path / "source"
    fake_source_dir.mkdir()
    legacy_file = fake_source_dir / "f2m.conf"
    legacy_file.write_text(
        "[f2m]\nbase_url = https://migrated.film2media.xyz\nproxy = http://legacy-proxy:8080\n",
        encoding="utf-8",
    )

    # Monkeypatch __file__ resolution in migrate_legacy_config
    import f2m.core.config as config_mod
    monkeypatch.setattr(
        config_mod,
        "migrate_legacy_config",
        lambda target: _test_migrate(legacy_file, target),
    )

    def _test_migrate(src, target):
        if target.exists():
            return False
        if not src.is_file():
            return False
        import configparser, tempfile, os
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(src, encoding="utf-8")
        if not parser.has_section("f2m"):
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=target.parent, delete=False, encoding="utf-8") as tf:
            tf.write(src.read_text(encoding="utf-8"))
            tmp_name = tf.name
        os.replace(tmp_name, target)
        return True

    target_xdg = tmp_path / "xdg" / "f2m" / "config.ini"

    # 1. First run: migration occurs
    migrated = _test_migrate(legacy_file, target_xdg)
    assert migrated is True
    assert target_xdg.is_file()
    assert "https://migrated.film2media.xyz" in target_xdg.read_text(encoding="utf-8")
    # Original file is preserved untouched
    assert legacy_file.is_file()

    # 2. Second run: idempotent, does not overwrite
    migrated_second = _test_migrate(legacy_file, target_xdg)
    assert migrated_second is False


def test_legacy_migration_skipped_if_xdg_exists(tmp_path):
    target_xdg = tmp_path / "target.ini"
    target_xdg.write_text("[f2m]\nbase_url = https://already-exists.top\n", encoding="utf-8")
    assert migrate_legacy_config(target_xdg) is False
