# Phase 2 Research & Architectural Decisions

**Feature**: Phase 2 — Domain Entities & XDG Configuration Engine  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Domain Entities Architecture

### Decision
Extract domain entities into `f2m/core/models.py` as pure Python dataclasses. Provide alias mappings for full backward compatibility with legacy `f2m.py`:
- `MediaPost` aliased as `Post = MediaPost`
- `MediaVersion` aliased as `Version = MediaVersion`
- Retain `Card`, `SearchResult`, `Season`, `Quality`, and `Episode` with identical field access semantics.
- Add `to_dict()` and `from_dict()` helper methods to all models for serialization/deserialization.

### Rationale
- `f2m.py` currently defines these classes directly in the middle of procedural scraping and CLI code (lines 453–515).
- Downstream tests in Phase 1 (`test_legacy_baseline.py`) instantiate `Card`, `Post`, `Season`, `Version`, `Quality`, and `Episode` and expect exact attribute names (`post.title`, `post.is_series`, `post.seasons`, `season.versions`, `version.qualities`, `quality.episodes`, etc.).
- Aliasing `Post = MediaPost` and `Version = MediaVersion` allows clean naming in the new core domain while ensuring existing code and tests continue to work without a single breaking change.

### Alternatives Considered
- *Pydantic / attrs*: Rejected. Adds heavy external runtime dependencies, which violates Constitution Principle IX (Scope Discipline & Minimal Dependencies) and contradicts our decision to keep runtime lightweight and stdlib-focused in early phases.
- *Leaving models in `f2m.py`*: Rejected. Blocks future modularization (Phase 3 scraper and Phase 4 CLI depend on decoupled entities).

---

## 2. Configuration Precedence & Resolution

### Decision
Implement a single authoritative configuration resolver in `f2m/core/config.py` following this strict 5-layer hierarchy:
1. **CLI Overrides**: Explicit dictionary passed programmatically (e.g. `cli_overrides={"proxy": "..."}`; reserved for Phase 4 CLI flags).
2. **Environment Variables**: `F2M_BASE_URL`, `F2M_MIRRORS`, `F2M_PROXY`, `F2M_PLAYER`, `F2M_DOWNLOAD_DIR`, `F2M_SEARCH_SORT`, `F2M_USER_AGENT`.
3. **Local Working Directory File**: `./f2m.conf` or `./config.ini` in `os.getcwd()` (portable flash drive / container mode).
4. **User-Global XDG Configuration File**: `$XDG_CONFIG_HOME/f2m/config.ini` (default `~/.config/f2m/config.ini` on POSIX) or `%APPDATA%\f2m\config.ini` on Windows.
5. **Built-in Defaults**: Hardcoded `CONFIG_DEFAULTS` dictionary.

### Rationale
- Allows containerized environments and automated tests to override settings via environment variables without mutating files on disk.
- Preserves local portable usage for users running from local project checkouts.
- Adheres to standard 12-factor application design.

### Alternatives Considered
- *JSON or YAML configuration*: Rejected. `f2m.conf` has historically used INI format (`[f2m]`). Using INI (`configparser`) maintains 100% backward compatibility with existing user configuration files.

---

## 3. Legacy Migration Invariants

### Decision
Implement a non-destructive migration routine:
- **Locations checked**:
  - `os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "f2m.conf")` (frozen binary)
  - `os.path.join(os.path.dirname(os.path.abspath(__file__)), "f2m.conf")` (source package)
- **Condition**: Triggers ONLY when target user XDG configuration file does not exist AND a legacy file is present.
- **Action**: Copies settings into `~/.config/f2m/config.ini`. Emits an informational message: `"Migrated legacy config from <old_path> to <new_path>"`.
- **Preservation**: The legacy file is **never deleted or moved**.
- **Idempotency**: Once the XDG file exists, migration is permanently skipped.

### Rationale
- Prevents data loss for users who spent time configuring proxies or custom download directories in v1.1.0.
- Keeping the original file intact guarantees non-destructive safety if the user runs both older and newer versions side-by-side.

---

## 4. Permission Safety & Root Cause Resolution (DEF-003)

### Decision
- Legacy code root cause: `f2m.py:233-288` resolved `CONF_PATH` next to the executable and called `ensure_config()` which immediately tried to `save_config()` on startup. In `/usr/local/bin` (or on root-owned multi-user systems), this raised `PermissionError: [Errno 13] Permission denied`.
- Fix: The application **never** attempts to write to the application script directory or executable directory.
- Writes target exclusively the user-owned configuration file (`~/.config/f2m/config.ini` or explicit path).
- If the user's home directory is completely read-only (e.g. live CD or restricted sandbox), `save_config()` catches `OSError`/`PermissionError`, logs a warning to `stderr`, and degrades to in-memory configuration without crashing.

---

## 5. Atomic Write Implementation

### Decision
Use `tempfile.NamedTemporaryFile` in the target directory followed by `os.replace`:
```python
target_dir = os.path.dirname(config_path)
os.makedirs(target_dir, exist_ok=True)
with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, encoding="utf-8") as tf:
    tmp_path = tf.name
    # write ini content
os.replace(tmp_path, config_path)
```
### Rationale
- `os.replace` is atomic on POSIX filesystems and Windows (Python 3.3+).
- Writing the temporary file in the *same* directory guarantees it resides on the same filesystem/volume, which is required for atomic rename across mount points.
- Prevents half-written or corrupted configuration files if the user triggers `Ctrl+C` or a power interruption occurs during a save.
