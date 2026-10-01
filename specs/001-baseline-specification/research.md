# Research & Technical Decisions: film2media-cli Modernization

**Feature**: `001-baseline-specification`  
**Date**: 2026-10-01  
**Status**: Completed  

---

## 1. Runtime & Dependency Strategy

### Decision
Adopt a curated, minimal dependency set:
- **`rich`**: For modern, resilient terminal rendering, tables, progress indicators, ANSI/VT escape sequences, `NO_COLOR` support, and Unicode visual cell width calculation.
- **`beautifulsoup4`** (with standard `html.parser`): For robust, DOM-tolerant HTML scraping that replaces brittle regexes.
- **`pytest` & `pytest-mock`**: For development and automated testing only.
- **`pyinstaller`**: In CI build pipelines to compile zero-dependency, standalone single-file executables (`f2m-linux-x64`, `f2m-windows-x64.exe`) for end users.

### Rationale
- Parsing Persian/Arabic text in terminal grids requires accurate Unicode display width calculation. Standard Python `len()` counts code points, not terminal cells, leading to ragged table borders and wrapping. `rich` has built-in cell-width measurement and East Asian/Arabic width awareness.
- Upstream markup on media portals regularly fluctuates (attribute order, extra tags, class changes). Tree-based DOM parsing (`beautifulsoup4`) gracefully handles malformed HTML where regexes fail completely.
- Packaging with PyInstaller preserves the original promise of a single, zero-dependency download for end users who do not have Python installed.

### Alternatives Considered
- *Strict Stdlib Only (`html.parser` + custom ANSI)*: Rejected because building and maintaining custom cross-platform terminal abstraction, Unicode cell measurement, and signal-safe alternate screen restoration introduces significant complexity and defect surface.
- *Heavy TUI Framework (`textual`)*: Rejected because `film2media-cli` is primarily a CLI command tool with interactive menus, not a persistent desktop-like TUI application with mouse windows.

---

## 2. Configuration & State Management

### Decision
Migrate from local `./f2m.conf` to XDG Base Directory specification:
- **Linux / macOS**: `~/.config/f2m/config.ini` (respects `$XDG_CONFIG_HOME`)
- **Windows**: `%APPDATA%\f2m\config.ini`
- **Portable Override**: If `./f2m.conf` or `./config.ini` exists in the current working directory, load it with highest precedence (after CLI flags).
- **Auto-Migration**: If the standard user config path does not exist but a legacy `f2m.conf` is found adjacent to the script or binary, automatically copy its settings into the standard user path on first run and notify the user.

### Rationale
- Storing configuration files next to executable binaries (`os.path.dirname(sys.executable)`) crashes with `PermissionError` whenever the application is installed in system paths like `/usr/local/bin` or `C:\Program Files`.
- Supporting a local working-directory config preserves portable execution (e.g. running from a flash drive).

### Alternatives Considered
- *Strict XDG without legacy migration*: Rejected because existing users upgrading from v1.1.0 would lose their saved mirrors, download directories, and proxy settings.
- *Strict local-only file*: Rejected due to fatal permission issues on multi-user and package-managed systems.

---

## 3. Network Resilience & Domain Redirection

### Decision
- Decouple HTTP transport into `f2m.net.client.HttpClient` with configurable timeouts, exponential backoff retries, and ordered fallback across configured mirrors.
- **Domain Redirects**: When an HTTP redirect occurs to a new domain or mirror, use the new domain **transiently for the active session**. Never silently write changes to disk. In interactive mode, prompt the user if they wish to persist the new domain to `config.ini`. In headless mode, never mutate configuration without an explicit command (`f2m config set base_url <url>`).

### Rationale
- The existing code (`maybe_update_domain`) wrote permanently to disk on any redirect containing `"f2m"`. This created severe security hazards (accidental hijacking or poisoned landing pages) and file-lock/concurrency issues.

### Alternatives Considered
- *Strict regex auto-update*: Rejected because domain names can shift unpredictably to new TLDs during ISP filtering waves.
- *No mirror failover*: Rejected because Iranian media sites frequently experience regional DNS or IP blocking.

---

## 4. Download & External Process Orchestration

### Decision
- **aria2c Management**:
  - Check for system `aria2c` via `shutil.which`.
  - Check local user directory `~/.local/bin/aria2c` (Linux/macOS) or `%LOCALAPPDATA%\f2m\aria2c.exe` (Windows).
  - If missing: **Never invoke `sudo`** and **never download unverified binaries**. Display clear, platform-specific copy-paste install commands (`sudo apt install aria2`, `brew install aria2`, `winget install aria2`), and immediately fall back to sequential `curl` downloads or link file export.
- **Player Management**:
  - Validate player binary existence (`mpv`, `vlc`, `potplayer`) before spawning.
  - Spawn detached process but inspect return code during startup window; capture and surface `stderr` if the process exits immediately with an error (e.g. missing codec, bad proxy).

### Rationale
- Running `sudo <pkg_manager> install` under the hood without interactive confirmation is a critical security vulnerability and violates basic Unix CLI etiquette.
- Providing copy-paste instructions and graceful fallback respects user autonomy and host system integrity.

---

## 5. Non-Interactive CLI & TTY Auto-Detection

### Decision
- Implement POSIX-compliant CLI argument parsing (`f2m/cli/parser.py`).
- **TTY Auto-Detection**:
  - `f2m search <query>`: If attached to a TTY and no headless flags are passed, launch the interactive selection workflow (preserving 100% legacy v1.1.0 muscle memory).
  - If output is piped (`|`) or redirected (`>`), or if `--json`, `--plain`, or `--quiet` is passed, run headlessly: output data to `stdout` and logs/diagnostics to `stderr`.
- Introduce `f2m resolve <url> [--quality <q>] [--stdout]` for direct scriptable link extraction.
- Enforce standard exit codes: `0` (Success), `1` (Runtime/Network error), `2` (CLI argument syntax error), `130` (Interrupted by user `SIGINT`).

### Rationale
- Allows scripting, cron jobs, and piping into external tools (like `jq` or custom download scripts) while keeping the interactive user journey seamless.
