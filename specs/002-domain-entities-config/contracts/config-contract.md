# Phase 2 Configuration Engine Contract

**Feature**: Phase 2 — Domain Entities & XDG Configuration Engine  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. File Format & INI Grammar

The configuration file retains 100% backward compatibility with `f2m.conf`:

```ini
# ── f2m config ─ film2media terminal client config ─────────────────
# base_url     : main site URL (auto-updated on domain redirect)
# mirrors      : comma-separated fallback domains
# proxy        : optional proxy for requests/aria2c/player (empty = off)
# search_sort  : quick-search sort (e.g. modified_at:desc)
# player       : auto | mpv | vlc | potplayer
# download_dir : downloads destination
# user_agent   : HTTP User-Agent header
# ─────────────────────────────────────────────────────────────────
[f2m]
base_url = https://www.myf2ms.top
mirrors = https://www.myf2m.info, https://www.myf2ms.top
proxy = 
search_sort = modified_at:desc
player = auto
download_dir = ~/Downloads/f2m
user_agent = Mozilla/5.0 ...
```

---

## 2. File Location Resolution Rules

1. **Custom Flag / Env Override**:
   - If `F2M_CONFIG` is set: use `Path(os.environ["F2M_CONFIG"]).expanduser()`.
2. **Local Portable Mode**:
   - If `./f2m.conf` exists in current working directory: use `./f2m.conf`.
   - Else if `./config.ini` exists in current working directory: use `./config.ini`.
3. **Platform User Configuration Path**:
   - **POSIX (Linux, macOS, BSD)**:
     - If `$XDG_CONFIG_HOME` is set: `$XDG_CONFIG_HOME/f2m/config.ini`.
     - Else: `~/.config/f2m/config.ini`.
   - **Windows**:
     - If `%APPDATA%` is set: `%APPDATA%\f2m\config.ini`.
     - Else: `~\\AppData\\Roaming\\f2m\\config.ini`.

---

## 3. Environment Variable Mapping

| Environment Variable | Target Config Key | Type Conversion |
|---|---|---|
| `F2M_CONFIG` | *(file path override)* | String (Path) |
| `F2M_BASE_URL` | `base_url` | String (strips trailing `/`) |
| `F2M_MIRRORS` | `mirrors` | Comma-separated string → `list[str]` |
| `F2M_PROXY` | `proxy` | String (empty string disables proxy) |
| `F2M_PLAYER` | `player` | String (`auto`, `mpv`, `vlc`, `potplayer`) |
| `F2M_DOWNLOAD_DIR` | `download_dir` | String (expands `~`) |
| `F2M_SEARCH_SORT` | `search_sort` | String |
| `F2M_USER_AGENT` | `user_agent` | String |

---

## 4. Key Validation Rules

| Key | Valid Values | Invalid Value Behavior |
|---|---|---|
| `base_url` | Must start with `http://` or `https://` | Raises `F2MConfigError` |
| `mirrors` | List of `http://` or `https://` URLs | Drops malformed URLs; raises if empty |
| `player` | Case-insensitive: `auto`, `mpv`, `vlc`, `potplayer` | Raises `F2MConfigError` |
| `proxy` | Empty or starts with `http://`, `https://`, `socks5://` | Raises `F2MConfigError` |
| `download_dir` | Non-empty path string | Defaults to `~/Downloads/f2m` if empty |
| `search_sort` | Non-empty string | Defaults to `modified_at:desc` if empty |
| `user_agent` | Non-empty string | Defaults to `DEFAULT_UA` if empty |

---

## 5. CLI Commands Contract

- `f2m config`:
  Prints the 7 configuration keys to stdout formatted in two columns:
  `   <key.ljust(13)> = <value>`
- `f2m config set <KEY> <VALUE>`:
  Validates `<KEY>` and `<VALUE>`. If valid, persists to the active configuration file atomically and prints:
  `✔ <key> saved`
  If invalid key or value, outputs `✖ <error>` and exits with code `1`.
