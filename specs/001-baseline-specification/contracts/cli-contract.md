# CLI Interface Contract: film2media-cli

**Feature**: `001-baseline-specification`  
**Date**: 2026-10-01  
**Status**: Completed  

---

## 1. Command Line Grammar

```text
f2m [GLOBAL_OPTIONS] [SUBCOMMAND] [SUBCOMMAND_OPTIONS] [ARGUMENTS...]
```

When invoked without subcommands:
- In a terminal (TTY): Launches the main interactive menu (`main_menu`).
- Non-interactive (redirected stdin/stdout): Prints short usage instructions and exits with code `0`.

---

## 2. Global Options

| Option | Short | Environment Variable | Description |
|---|---|---|---|
| `--help` | `-h` | - | Display help documentation and command reference |
| `--version` | `-v` | - | Print application version string |
| `--config <PATH>` | `-c` | `F2M_CONFIG` | Path to custom configuration file |
| `--proxy <URL>` | - | `F2M_PROXY` | Explicit proxy URL (HTTP/HTTPS/SOCKS5) |
| `--no-color` | - | `NO_COLOR` | Disable ANSI color sequences |
| `--quiet` | `-q` | `F2M_QUIET` | Suppress diagnostic output and spinners; output data only |

---

## 3. Subcommands

### 3.1 `search`
Search for movies and series on Film2Media.

```text
f2m search <QUERY> [OPTIONS]
```

**Options**:
- `--format <text|json>` (default: `text`): Output format.
- `--plain`: Disable table borders and styling for plain text piping.
- `--limit <N>`: Maximum results to display.

**Behavior**:
- **TTY attached & no formatting flags**: Automatically opens the interactive selection screen (100% backward compatible with v1.1.0).
- **Piped stdout OR `--format json` / `--plain`**: Emits search results non-interactively to `stdout` without clearing the screen, and exits with code `0`.

**JSON Output Schema**:
```json
[
  {
    "kind": "movie",
    "title": "Inception",
    "title_fa": "تلقین",
    "year": "2010",
    "rating": "8.8",
    "url": "https://www.myf2ms.top/movies/inception-2010/",
    "is_dub": true,
    "is_hardsub": false
  }
]
```

---

### 3.2 `resolve` / `url`
Extract direct media download links from a post URL, or open directly in interactive mode.

```text
f2m resolve <POST_URL> [OPTIONS]
f2m url <POST_URL> [OPTIONS]
```

**Backward Compatibility Note**:
`f2m url <POST_URL>` is maintained as a legacy-compatible command alias. When executed in a terminal (TTY) without headless flags, both `f2m url` and `f2m resolve` open the interactive quality/episode selection screen directly for the target post.

**Options**:
- `--season <N>`: Season number (for series).
- `--quality <LABEL>`: Quality regex or substring filter (e.g. `1080p`, `720p`).
- `--episode <RANGE>`: Episode selection (e.g. `1`, `1-5`, `all`).
- `--version <dub|hardsub>`: Audio/subtitle version preference.
- `--format <urls|json>` (default: `urls`): `urls` outputs direct HTTP links one per line; `json` outputs structured metadata.

**Behavior**:
- In non-interactive/piped mode or when explicit format flags are provided: runs 100% headlessly. Logs and progress indicators route to `stderr`; links route directly to `stdout`.
- In an interactive TTY without format flags: opens the interactive selection screen for the post.

---

### 3.3 `categories`
Browse or list categories, sections, and genres.

```text
f2m categories [OPTIONS]
```

**Options**:
- `--format <text|json>`: Output format.

**Behavior**:
- If attached to TTY, opens the interactive category browser.
- If non-interactive, lists categories and genres in structured format.

---

### 3.4 `config`
Inspect or update user configuration settings.

```text
f2m config [show]
f2m config set <KEY> <VALUE>
f2m config path
```

**Valid Keys**:
- `base_url`: Primary domain URL.
- `mirrors`: Comma-separated list of fallback URLs.
- `proxy`: Proxy string.
- `player`: `auto`, `mpv`, `vlc`, `potplayer`.
- `download_dir`: Destination directory.
- `search_sort`: Sort order (`modified_at:desc`, `created_at:desc`, etc.).

---

### 3.5 `test`
Run connectivity and domain diagnostics.

```text
f2m test [OPTIONS]
```

**Behavior**:
Tests reachability of `base_url` and mirrors; validates response time, SSL certificates, proxy routing, and parsing health. Emits a diagnostic summary and exits `0` on success or `1` on failure.

---

## 4. Exit Codes

| Exit Code | Meaning | Example Condition |
|---|---|---|
| `0` | Success | Command completed successfully |
| `1` | Runtime / Operational Error | All mirrors unreachable, scraping failed, network timeout |
| `2` | Syntax / Argument Error | Invalid flag, missing required argument, invalid config key |
| `130` | Interrupted by User | `Ctrl+C` (`SIGINT`) pressed during execution |
