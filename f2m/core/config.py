"""
Configuration engine, XDG path resolution, atomic writes, and precedence for film2media-cli.
"""

from __future__ import annotations

import configparser
import os
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from f2m.core.exceptions import F2MConfigError

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
)

CONFIG_DEFAULTS = {
    "base_url": "https://www.myf2ms.top",
    "mirrors": "https://www.myf2m.info, https://www.myf2ms.top",
    "proxy": "",
    "search_sort": "modified_at:desc",
    "player": "auto",
    "download_dir": "~/Downloads/f2m",
    "user_agent": DEFAULT_UA,
}

CONF_COMMENT = """\
# ── f2m.conf ─ film2media terminal client config ─────────────────
# base_url     : main site URL (auto-updated on domain redirect)
# mirrors      : comma-separated fallback domains
# proxy        : optional proxy for requests/aria2c/player (empty = off)
# search_sort  : quick-search sort (e.g. modified_at:desc)
# player       : auto | mpv | vlc | potplayer
# download_dir : downloads destination
# ─────────────────────────────────────────────────────────────────
"""

VALID_PLAYERS = {"auto", "mpv", "vlc", "potplayer"}


@dataclass
class ConfigurationProfile:
    """Represents the validated runtime configuration profile."""
    base_url: str = "https://www.myf2ms.top"
    mirrors: list[str] = field(
        default_factory=lambda: ["https://www.myf2m.info", "https://www.myf2ms.top"]
    )
    proxy: str = ""
    search_sort: str = "modified_at:desc"
    player: str = "auto"
    download_dir: str = "~/Downloads/f2m"
    user_agent: str = DEFAULT_UA

    @property
    def raw_mirrors(self) -> str:
        return ", ".join(self.mirrors)

    def proxies_dict(self) -> dict[str, str | None]:
        p = self.proxy.strip()
        return {"http": p or None, "https": p or None} if p else {}

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["raw_mirrors"] = self.raw_mirrors
        return d


def validate_key_value(key: str, value: str) -> str:
    """Validate a single configuration key-value pair, raising F2MConfigError on invalid inputs."""
    if key not in CONFIG_DEFAULTS:
        raise F2MConfigError(f"unknown key '{key}' — valid: {', '.join(CONFIG_DEFAULTS)}")

    val = value.strip()
    if key == "base_url":
        if not (val.startswith("http://") or val.startswith("https://")):
            raise F2MConfigError(f"invalid base_url '{val}' — must start with http:// or https://")
        return val.rstrip("/")
    elif key == "player":
        low = val.lower()
        if low not in VALID_PLAYERS:
            raise F2MConfigError(f"invalid player '{val}' — valid: {', '.join(sorted(VALID_PLAYERS))}")
        return low
    elif key == "proxy":
        if val and not (val.startswith("http://") or val.startswith("https://") or val.startswith("socks5://")):
            raise F2MConfigError(f"invalid proxy '{val}' — must start with http://, https://, or socks5://")
        return val
    elif key == "mirrors":
        urls = [u.strip().rstrip("/") for u in val.split(",") if u.strip()]
        for u in urls:
            if not (u.startswith("http://") or u.startswith("https://")):
                raise F2MConfigError(f"invalid mirror URL '{u}' — must start with http:// or https://")
        return ", ".join(urls)
    elif key in ("download_dir", "search_sort", "user_agent"):
        if not val:
            return CONFIG_DEFAULTS[key]
        return val
    return val


def resolve_config_path() -> Path:
    """
    Resolve the active configuration file path according to:
    1. F2M_CONFIG environment variable (if set)
    2. Local ./f2m.conf or ./config.ini in current working directory (portable mode)
    3. User-global XDG / AppData configuration file
    """
    # 1. Custom env var
    env_config = os.environ.get("F2M_CONFIG", "").strip()
    if env_config:
        return Path(env_config).expanduser().resolve()

    # 2. Local working directory file
    cwd = Path.cwd()
    local_conf = cwd / "f2m.conf"
    if local_conf.is_file():
        return local_conf.resolve()
    local_ini = cwd / "config.ini"
    if local_ini.is_file():
        return local_ini.resolve()

    # 3. User-global path
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base = Path(appdata)
        else:
            base = Path.home() / "AppData" / "Roaming"
        return (base / "f2m" / "config.ini").resolve()
    else:
        xdg_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_home and xdg_home.strip():
            base = Path(xdg_home.strip()).expanduser()
        else:
            base = Path.home() / ".config"
        return (base / "f2m" / "config.ini").resolve()


def migrate_legacy_config(target_path: Path) -> bool:
    """
    Non-destructive migration of legacy f2m.conf:
    If target_path does not exist, check recognized legacy locations (script or binary directory).
    If found, copy settings into target_path and preserve original file untouched.
    Returns True if migration occurred, False otherwise.
    """
    if target_path.exists():
        return False

    candidate_dirs: list[Path] = []
    if getattr(sys, "frozen", False):
        candidate_dirs.append(Path(sys.executable).parent)
    # Check directory containing f2m.py
    candidate_dirs.append(Path(__file__).resolve().parent.parent.parent)

    legacy_file: Path | None = None
    for d in candidate_dirs:
        cand = d / "f2m.conf"
        if cand.is_file():
            legacy_file = cand
            break

    if not legacy_file:
        return False

    try:
        content = legacy_file.read_text(encoding="utf-8")
        # Validate that it parses as INI
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(content)
        if not parser.has_section("f2m"):
            return False

        # Atomic write to target_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", dir=target_path.parent, delete=False, encoding="utf-8"
        ) as tf:
            tf.write(content)
            tmp_name = tf.name
        os.replace(tmp_name, target_path)
        sys.stderr.write(
            f"ℹ Migrated legacy configuration from {legacy_file} to {target_path}\n"
        )
        return True
    except Exception as exc:
        sys.stderr.write(f"⚠ Could not migrate legacy config from {legacy_file}: {exc}\n")
        return False


class ConfigManager:
    """
    Authoritative configuration manager implementing layered precedence:
    CLI Overrides > Environment Variables (F2M_*) > Local Working Dir > User XDG Config > Defaults
    """

    def __init__(self, custom_path: Path | None = None, cli_overrides: dict[str, str] | None = None):
        self._custom_path = custom_path
        self._cli_overrides = cli_overrides or {}
        self._cfg: dict[str, str] = {}
        self._file_path = self._resolve_path()
        self.load()

    def _resolve_path(self) -> Path:
        if self._custom_path:
            return self._custom_path.expanduser().resolve()
        return resolve_config_path()

    @property
    def file_path(self) -> Path:
        return self._file_path

    def load(self) -> None:
        """Load configuration applying the 5-tier precedence hierarchy."""
        # 1. Defaults
        self._cfg = dict(CONFIG_DEFAULTS)

        # 2. Check for legacy migration if path doesn't exist
        migrate_legacy_config(self._file_path)

        # 3. Read file if it exists
        if self._file_path.is_file():
            try:
                parser = configparser.ConfigParser(interpolation=None)
                parser.read(self._file_path, encoding="utf-8")
                if parser.has_section("f2m"):
                    for key, val in parser.items("f2m"):
                        if key in CONFIG_DEFAULTS:
                            self._cfg[key] = val.strip()
            except Exception as exc:
                sys.stderr.write(f"⚠ Warning: Could not read config file {self._file_path}: {exc}\n")

        # 4. Environment Variables (F2M_*)
        env_map = {
            "F2M_BASE_URL": "base_url",
            "F2M_MIRRORS": "mirrors",
            "F2M_PROXY": "proxy",
            "F2M_SEARCH_SORT": "search_sort",
            "F2M_PLAYER": "player",
            "F2M_DOWNLOAD_DIR": "download_dir",
            "F2M_USER_AGENT": "user_agent",
        }
        for env_var, cfg_key in env_map.items():
            if env_var in os.environ:
                raw = os.environ[env_var].strip()
                # Empty string explicitly overrides
                self._cfg[cfg_key] = raw

        # 5. CLI Overrides
        for k, v in self._cli_overrides.items():
            if k in CONFIG_DEFAULTS:
                self._cfg[k] = v.strip()

        # Parse mirrors into list format internally
        raw_mirrors = self._cfg.get("mirrors", "")
        self._cfg["_raw_mirrors"] = raw_mirrors
        self._cfg["mirrors"] = [u.strip() for u in raw_mirrors.split(",") if u.strip()]

    def save(self) -> None:
        """Atomically persist current configuration to file_path."""
        content = CONF_COMMENT + "[f2m]\n"
        for key in (
            "base_url", "mirrors", "proxy", "search_sort", "player",
            "download_dir", "user_agent"
        ):
            val = self._cfg["_raw_mirrors"] if key == "mirrors" else self._cfg[key]
            content += f"{key} = {val}\n"

        target_dir = self._file_path.parent
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "w", dir=target_dir, delete=False, encoding="utf-8"
            ) as tf:
                tf.write(content)
                tmp_name = tf.name
            os.replace(tmp_name, self._file_path)
        except OSError as exc:
            sys.stderr.write(f"⚠ Warning: Could not save configuration to {self._file_path}: {exc}\n")

    def get(self, key: str, default: Any = None) -> Any:
        return self._cfg.get(key, default)

    def set(self, key: str, value: str) -> None:
        validated = validate_key_value(key, value)
        if key == "mirrors":
            self._cfg["_raw_mirrors"] = validated
            self._cfg["mirrors"] = [u.strip() for u in validated.split(",") if u.strip()]
        else:
            self._cfg[key] = validated
        self.save()

    def profile(self) -> ConfigurationProfile:
        mirrors = self._cfg.get("mirrors")
        if isinstance(mirrors, str):
            mirrors_list = [u.strip() for u in mirrors.split(",") if u.strip()]
        else:
            mirrors_list = list(mirrors)

        return ConfigurationProfile(
            base_url=self._cfg.get("base_url", CONFIG_DEFAULTS["base_url"]),
            mirrors=mirrors_list,
            proxy=self._cfg.get("proxy", ""),
            search_sort=self._cfg.get("search_sort", CONFIG_DEFAULTS["search_sort"]),
            player=self._cfg.get("player", CONFIG_DEFAULTS["player"]),
            download_dir=self._cfg.get("download_dir", CONFIG_DEFAULTS["download_dir"]),
            user_agent=self._cfg.get("user_agent", CONFIG_DEFAULTS["user_agent"]),
        )
