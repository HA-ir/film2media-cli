# Contract: Downloader Security & Execution Subsystem

**Feature**: Phase 6 — Downloader Security & Sudo Removal  
**Date**: 2026-10-02  
**Status**: Authoritative Contract  

---

## 1. Downloader Python Module Contract (`f2m.integrations.downloader`)

### 1.1 Discovery & Environment
```python
def find_downloader() -> tuple[DownloaderBackend, str | None]:
    """
    Discovers available download managers strictly on system $PATH.
    Returns (DownloaderBackend.ARIA2C, path) if aria2c is found.
    Returns (DownloaderBackend.CURL, path) if curl is found.
    Returns (DownloaderBackend.NONE, None) if neither is found.
    NEVER checks local application directories or relative paths.
    """
```

```python
def get_install_command(platform_name: str | None = None) -> str:
    """
    Returns platform-specific manual copy-paste installation command:
    - Linux (Debian/Ubuntu): 'sudo apt install aria2'
    - Linux (Fedora/RHEL):   'sudo dnf install aria2'
    - Linux (Arch):          'sudo pacman -S aria2'
    - Linux (Alpine):        'apk add aria2'
    - macOS (Darwin):        'brew install aria2'
    - Windows:               'winget install aria2'
    """
```

---

### 1.2 Path Resolution & Traversal Defense
```python
def resolve_destination(raw_dir: str, subdir: str | None = None) -> Path:
    """
    Resolves canonical download path and validates write permissions.
    - Expands ~ via os.path.expanduser.
    - Canonicalizes via Path.resolve().
    - Validates write permissions via os.access(..., os.W_OK).
    - If non-existent, verifies nearest ancestor write permission before mkdir.
    - Sanitizes optional subdir.
    - Raises F2MDownloadError if directory is not writable.
    """
```

```python
def sanitize_filename(name: str) -> str:
    """
    Sanitizes untrusted filenames from URLs or media metadata.
    - NFKC Unicode normalization.
    - Strips directory traversal tokens (..).
    - Strips null bytes (\0), control characters, / and \\.
    - Strips illegal Windows characters (:*?"<>|).
    - Strips leading dashes (-) to prevent CLI flag injection.
    - Strips leading/trailing spaces and dots.
    - Guarantees non-empty return value (defaults to 'f2m_download').
    """
```

```python
def assert_path_contained(target_path: Path, base_dir: Path) -> None:
    """
    Validates that target_path strictly resides within base_dir.
    Raises F2MDownloadError if target escapes base_dir.
    """
```

---

### 1.3 Subprocess Execution Invariants

```python
def execute_download(request: DownloadRequest) -> DownloadResult:
    """
    Executes download job using available backend without privilege escalation.
    - Zero shell=True calls.
    - aria2c: Runs with --file-allocation=none, -d <dir>, --all-proxy (if proxy set).
    - curl: Downloads each URL to <dest>/<file>.part.
            Atomically replaces <dest>/<file> upon exit code 0.
            Cleans up <dest>/<file>.part upon failure or interruption.
    - Handles KeyboardInterrupt cleanly: kills child process, cleans .part, raises KeyboardInterrupt.
    """
```

```python
def execute_stream(request: StreamRequest) -> StreamResult:
    """
    Spawns media player (mpv/vlc/potplayer) using subprocess.Popen.
    - Zero shell=True calls.
    - stdout and stderr redirected to subprocess.DEVNULL.
    """
```

---

## 2. Command Line Contract & Stream Isolation

### 2.1 Privilege Invariant
- Under NO circumstance does `f2m` spawn `sudo`, `su`, or invoke package managers (`apt`, `dnf`, `yum`, `pacman`, `apk`, `zypper`).
- The application executes strictly under the effective user ID (`os.geteuid()`) of the invoking shell.

### 2.2 Stream Separation
1. **`stdout`**:
   - In interactive mode: Rich UI elements, styled tables, selection menus.
   - In `--json` mode: Strictly clean JSON payload.
   - In `--plain` mode: Tab-separated values or raw URLs.
   - Zero progress bars, status notices, or warning messages on `stdout` in machine-readable modes.
2. **`stderr`**:
   - Reserved for diagnostics, status messages, spinners, notices, and errors.
   - In `--json` mode: Structured JSON error payloads emit to `stderr`.

---

## 3. Exit Code Contract

All Phase 4 exit codes are strictly preserved:
- `0`: Success (download completed, links exported, stream launched).
- `1`: Operational error (`F2MDownloadError`, destination unwritable, child process failure).
- `2`: Invalid CLI invocation / argument conflict.
- `3`: Configuration error (`F2MConfigError`, e.g. invalid syntax in `config.ini`).
- `4`: Network error / mirror exhaustion (`F2MNetworkError`).
- `5`: Upstream parsing failure (`F2MParseError`).
- `6`: Resource not found.
- `130`: Interrupted by user (`SIGINT` / `Ctrl+C`).
