# ⚡ f2m — Film2Media Terminal Client

Search, browse, download and stream movies & series from Film2Media — right inside your terminal.

> 🇮🇷 نسخه‌ی فارسی: [README.fa.md](README.fa.md)

---

## 📸 Screenshots

![Main menu](assets/screenshot-1.png)
![Search results](assets/screenshot-2.png)
![Quality selection](assets/screenshot-3.png)

---

## ✨ Features

- 🔍 **Instant search** — search by English or Persian title, with IMDb rating and dub/hardsub badges
- 🗂 **Browse** — movies, series, genres and Top-250 lists
- ⬇ **Download** — multi-connection downloads with aria2c (fallback: curl)
- 🤖 **Auto aria2c** — if aria2c is missing, f2m installs it for you (package manager on Linux, official binary on Windows)
- ▶ **Stream** — watch instantly in mpv, VLC or PotPlayer without downloading
- 🌐 **Auto domain update** — when the site moves to a new domain, f2m detects it and updates itself
- 🧩 **Single file** — pure Python 3.8+, zero dependencies

---

## 📦 Install

### Option A — Ready binaries (no Python needed)

Grab `f2m-windows-x64.exe` or `f2m-linux-x64` from the
[**Releases**](https://github.com/lombalo/film2media-cli/releases) page and run it.

### Option B — From source

Requires Python 3.8+:

```bash
python f2m.py
```

Optional companions:

- **aria2c** — fast downloads
- **mpv** or **VLC** — streaming

---

## 🚀 Usage

Run without arguments for the interactive menu:

```bash
f2m
```

Or use direct subcommands:

| Command | Description |
|---|---|
| `f2m search <query>` | Search movies & series (interactive picker by default) |
| `f2m url <post-url>` | Open or inspect a post page directly |
| `f2m categories` | Browse categories & genres |
| `f2m config` | Show active configuration |
| `f2m config get <key>` | Get a specific configuration value |
| `f2m config set <key> <val>` | Save a configuration key |
| `f2m test` | Connectivity and mirror check |
| `f2m version` | Show application version |
| `f2m help` | Show usage assistance |

Inside interactive menus you can select items like `1`, ranges like `1,3,5-8`, or `all`.

### 🤖 Machine-Readable & Automation Modes

f2m provides first-class support for scripting and Unix pipelines with strict stream separation (data to `stdout`, diagnostics/spinners to `stderr`):

**1. Machine-Readable JSON (`--json`)**
Outputs valid, unadorned JSON directly to `stdout` without spinner or ANSI contamination:
```bash
# Pipe search results directly to jq
f2m search "Inception" --json | jq '.[0].title'

# Inspect complete post structure (versions, qualities, direct links)
f2m url "https://www.myf2ms.top/movies/inception-2010/" --json | jq .

# Dump full configuration as JSON
f2m config --json | jq .base_url
```

**2. Unix Pipeline Integration (`--plain`)**
Outputs clean, unformatted tab- or newline-delimited text on `stdout`:
```bash
# Feed media direct links straight to aria2c
f2m url "https://www.myf2ms.top/movies/inception-2010/" --plain | aria2c -i -

# Filter search results with awk
f2m search "Inception" --plain | awk -F'\t' '{print $2, $3, $5}'

# Extract a single configuration value
BASE_URL=$(f2m config get base_url --plain)
```

**Global Options:**
- `--json`: Machine-readable JSON output on `stdout` (enforces non-interactive mode).
- `--plain`: Tab- or newline-delimited unadorned output on `stdout` (enforces non-interactive mode).
- `--no-color`: Disable all ANSI terminal colors (honors `NO_COLOR`).
- `--config <path>`: Override configuration file path.
- `-h, --help`: Display help screen.
- `-V, --version`: Display version.

### 🔢 Exit Codes

Scripts can inspect deterministic POSIX exit codes:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Operational runtime error |
| `2` | Invalid CLI invocation, syntax error, or conflicting flags |
| `3` | Configuration error (`F2MConfigError`) |
| `4` | Network timeout, DNS failure, or mirror exhaustion (`F2MNetworkError`) |
| `5` | Upstream HTML/JSON parsing failure (`F2MParseError`) |
| `6` | Resource not found (empty search results, HTTP 404) |
| `130` | Process interrupted by user (`SIGINT` / `Ctrl+C`) |

---

## ⚙️ Configuration

Configuration is stored in standard user directories (XDG compliant):
- **Linux / macOS**: `~/.config/f2m/config.ini` (or `$XDG_CONFIG_HOME/f2m/config.ini`)
- **Windows**: `%APPDATA%\f2m\config.ini`
- **Portable mode**: If `./f2m.conf` exists in your current directory, it takes precedence.
- **Legacy migration**: If you previously used an `f2m.conf` adjacent to the executable, it is automatically and non-destructively migrated on first run.

**View configuration:**
```bash
f2m config
```

**Edit a configuration key:**
```bash
f2m config set <key> <value>
# Example: change domain
f2m config set base_url https://www.new-domain.tld
# Example: set proxy
f2m config set proxy http://127.0.0.1:8080
```

Supported keys:

| Key | Description |
|---|---|
| `base_url` | Primary site URL |
| `mirrors` | Fallback domains (comma-separated) |
| `proxy` | Proxy for requests & downloads (e.g. `http://127.0.0.1:8080`, empty = off) |
| `player` | Preferred player: `auto` / `mpv` / `vlc` / `potplayer` |
| `download_dir` | Downloads destination folder |
| `search_sort` | Sort order for quick search |
| `user_agent` | HTTP User-Agent string |

**Environment Variable Overrides:**
You can temporarily override any setting without editing files:
`F2M_BASE_URL`, `F2M_MIRRORS`, `F2M_PROXY`, `F2M_PLAYER`, `F2M_DOWNLOAD_DIR`, `F2M_SEARCH_SORT`, `F2M_USER_AGENT`, or specify a custom config file path with `F2M_CONFIG`.

Precedence: `Environment Variables (F2M_*) > Local ./f2m.conf > User XDG Config > Defaults`.

---

## 🌐 Network & Scraper Architecture

- **DOM Scraper**: Built with `beautifulsoup4` using Python's standard `html.parser` for resilient, tree-based HTML extraction that gracefully tolerates upstream attribute reordering and whitespace variations.
- **Resilient HTTP Client**:
  - **Bounded Retries**: Automatically retries transient network errors (timeouts, HTTP 429, 502, 503, 504) up to 2 times with exponential backoff.
  - **Mirror Failover**: Systematically falls back across configured `mirrors` when the primary base URL fails.
  - **Session-Transient Redirects**: Domain redirects are remembered in-memory for the running session and never modify on-disk configuration automatically.
  - **Proxy Support**: Supports HTTP, HTTPS, and SOCKS5 proxies.

---

## 🛠 Development & Testing

Set up the development environment and run automated tests:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run offline automated test suite
pytest
```

---

## 🛠 Troubleshooting

- **Nothing found** → run `f2m test`
- **Cannot connect** → the domain may be filtered; set a proxy or the new `base_url`
- **No player found** → install mpv or VLC, or copy links manually

---

## ⚠️ Disclaimer

This tool only indexes publicly available links and is provided for personal use.
Users are responsible for complying with the laws of their region.

---

## 📄 License

MIT — see [LICENSE](LICENSE)
