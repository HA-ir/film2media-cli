# Phase 1: Data Model & Entities

**Feature**: Phase 6 — Downloader Security & Sudo Removal  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Entities & Data Structures

### 1.1 `DownloaderBackend` (Enum)
Represents available external download acceleration and transfer tools.

```python
from enum import Enum, auto

class DownloaderBackend(Enum):
    ARIA2C = auto()
    CURL = auto()
    NONE = auto()
```

- **`ARIA2C`**: Fast, multi-connection, chunk-based downloader with resume capability.
- **`CURL`**: Standard sequential HTTP transfer tool with wide platform availability.
- **`NONE`**: Neither downloader tool is installed on `$PATH`.

---

### 1.2 `DownloadRequest` (Dataclass)
Encapsulates all parameters required to safely prepare and execute a download job.

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class DownloadRequest:
    urls: list[str]
    destination_dir: Path
    subdir: str | None = None
    proxy: str | None = None
    max_connections: int = 16
    max_concurrent_downloads: int = 4
```

- **`urls`**: Non-empty list of validated HTTP/HTTPS download URLs.
- **`destination_dir`**: Canonical absolute Path where files will be stored.
- **`subdir`**: Optional subfolder derived from media title (must be sanitized).
- **`proxy`**: Optional HTTP/HTTPS/SOCKS proxy string.
- **`max_connections`**: Maximum connections per server for `aria2c` (default 16).
- **`max_concurrent_downloads`**: Maximum parallel download jobs for `aria2c` (default 4).

---

### 1.3 `DownloadResult` (Dataclass)
Encapsulates the outcome of a download execution.

```python
@dataclass(frozen=True)
class DownloadResult:
    success: bool
    backend: DownloaderBackend
    exit_code: int
    destination_dir: Path
    downloaded_files: list[Path] = field(default_factory=list)
    error_message: str | None = None
```

- **`success`**: `True` if external process exited with `0` and all expected files completed.
- **`backend`**: Which downloader backend was utilized.
- **`exit_code`**: Return code of the child process.
- **`destination_dir`**: Target directory where files were written.
- **`downloaded_files`**: List of paths to successfully downloaded files.
- **`error_message`**: Formatted error message if execution failed.

---

### 1.4 `StreamRequest` (Dataclass)
Encapsulates streaming media playback parameters.

```python
@dataclass(frozen=True)
class StreamRequest:
    urls: list[str]
    title: str
    player: str = "auto"
    proxy: str | None = None
```

---

### 1.5 `StreamResult` (Dataclass)
Encapsulates the outcome of launching a media player process.

```python
@dataclass(frozen=True)
class StreamResult:
    success: bool
    player_name: str
    pid: int | None = None
    error_message: str | None = None
```

---

## 2. Exceptions Hierarchy

In `f2m/core/exceptions.py`:

```python
class F2MDownloadError(F2MError):
    """Raised when download destination validation, process execution, or file handling fails."""
    exit_code: int = 1
```

- Inherits from `F2MError` (base domain exception).
- Default POSIX exit code: `1` (Operational Error).
- Mapped in `f2m/cli/runner.py` to exit code `1` and structured JSON error payload in `--json` mode.

---

## 3. Validation Rules & State Transitions

### 3.1 Path Resolution & Validation Flow
1. **Input**: Unresolved string path from config (e.g. `~/Downloads/f2m` or `./media`).
2. **Expansion**: `expanduser()` expands `~` to user's `$HOME`.
3. **Canonicalization**: `.resolve()` resolves relative parts and symlinks to real canonical absolute path.
4. **Pre-flight Write Check**:
   - If destination exists: Must satisfy `os.access(dest, os.W_OK)`.
   - If destination does not exist: Traverse upwards to the nearest existing ancestor directory and verify `os.access(ancestor, os.W_OK)`.
   - If unwritable: Raise `F2MDownloadError("Destination directory '{dest}' is not writable")`.
5. **Directory Creation**: `dest.mkdir(parents=True, exist_ok=True, mode=0o755)`.

### 3.2 Filename Sanitization & Traversal Defense
1. **Input**: Untrusted string (URL slug or media title).
2. **Normalization**: `unicodedata.normalize("NFKC", name)`.
3. **Stripping**:
   - Strip directory traversal tokens (`..`).
   - Strip null bytes (`\0`) and control characters (`\x00` - `\x1f`, `\x7f`).
   - Strip path separators (`/`, `\`).
   - Strip reserved characters (`:`, `*`, `?`, `"`, `<`, `>`, `|`).
   - Strip leading dashes (`-`) to prevent CLI flag injection.
   - Strip trailing spaces and dots (`.`).
4. **Fallback**: If empty after sanitization, default to `"f2m_download"`.
5. **Containment Assertion**:
   ```python
   target_file = (destination_dir / sanitized_name).resolve()
   if not target_file.is_relative_to(destination_dir.resolve()):
       raise F2MDownloadError(f"Security violation: path traversal detected for '{sanitized_name}'")
   ```

### 3.3 Atomic Staging Transitions for Curl
```text
[Initiated] ──> Write to `<filename>.part`
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
   [Exit Code 0]        [Non-zero / SIGINT]
         │                     │
         ▼                     ▼
Atomic rename via         Delete `<filename>.part`
`os.replace()` to         Raise `F2MDownloadError`
`<filename>`              or exit with code 130
```
