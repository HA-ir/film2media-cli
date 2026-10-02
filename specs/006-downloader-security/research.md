# Phase 0: Research & Technology Decisions

**Feature**: Phase 6 — Downloader Security & Sudo Removal  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Subprocess Execution & Executable Resolution

### Decision: Standard `subprocess` with Argument Lists and `$PATH`-Only Resolution
- **Approach**: All external process invocations (`aria2c`, `curl`, `mpv`, `vlc`, `potplayer`) use explicit argument lists (`list[str]`) passed to `subprocess.run` or `subprocess.Popen`. Executables are resolved strictly via `shutil.which(name)` against the system `$PATH`.
- **Rationale**:
  - `shell=True` is the primary vector for command injection vulnerabilities. Passing explicit argument lists completely neutralizes shell metacharacter expansion and argument splitting attacks.
  - Probing `app_dir()` or relative paths for local binaries (as legacy `local_aria2c()` did) exposes users to binary planting/hijacking vulnerabilities, especially if the current directory or application directory is world-writable or shared.
  - Standard library `shutil.which` respects platform executable semantics (e.g. `PATHEXT` on Windows) while confining lookups to trusted environment paths.
- **Alternatives Considered**:
  - *Probing `local_aria2c` alongside `$PATH`*: Rejected. Allows an unprivileged attacker in a multi-user environment or untrusted directory to drop a malicious `aria2c` or `aria2c.exe` and execute arbitrary code.
  - *Bundling standalone `aria2c` binaries in the repo*: Rejected. Bloats repository size, introduces cross-platform binary distribution maintenance overhead, and violates Principle IX (Scope Discipline).

---

## 2. Privilege Escalation Elimination & Manual Guidance

### Decision: Zero Sudo Invocations with Platform-Specific Manual Install Guidance
- **Approach**: Completely delete `install_aria2c_linux()` and `install_aria2c_windows()`. When `aria2c` is not found on `$PATH`:
  1. Emit informative, copy-pasteable installation instructions tailored to the detected OS (`platform.system()`):
     - Debian / Ubuntu: `sudo apt install aria2`
     - Fedora / RHEL: `sudo dnf install aria2`
     - Arch Linux: `sudo pacman -S aria2`
     - Alpine: `apk add aria2`
     - macOS: `brew install aria2`
     - Windows: `winget install aria2`
  2. Fall back immediately to `curl` if present on `$PATH`.
  3. If `curl` is also missing, fall back to direct link export (stdout / clipboard).
- **Rationale**:
  - Eliminates `DEF-001`. A CLI media utility should never automatically execute package management commands with `sudo` or download unverified executable binaries from remote URLs.
  - Package installation is an administrative action that belongs exclusively to the machine owner.
  - Zero unexpected password prompts or root privilege escalation occurs.
- **Alternatives Considered**:
  - *Prompting user before running `sudo`*: Rejected. Normal downloading must run entirely unprivileged. The application itself should never invoke `sudo` or package managers under any circumstance.
  - *Downloading verified binaries with SHA-256 checks on Windows*: Rejected. Maintaining remote hashes and managing binary updates is out of scope and introduces unnecessary supply-chain attack surfaces. Users can install via official package managers (`winget install aria2` or `choco install aria2`).

---

## 3. Destination Resolution, Permissions, and Traversal Defense

### Decision: Canonical Path Resolution with Pre-Flight Write Check and Boundary Containment
- **Approach**:
  1. **Resolution**: `base_dir = Path(os.path.expanduser(config["download_dir"])).resolve()`.
  2. **Pre-flight Check**: Check if `base_dir` exists. If it exists, verify `os.access(base_dir, os.W_OK)`. If it does not exist, verify write permissions on the nearest existing parent directory before creating it with `0o755`.
  3. **Containment**: Target files are resolved via `target_path = (base_dir / sanitized_subdir / sanitized_filename).resolve()`. Verify `target_path.is_relative_to(base_dir)`.
  4. **Sanitization**: `sanitize_filename(name)` normalizes Unicode (NFKC), removes null bytes (`\0`), control characters, directory separators (`/`, `\`), path traversal tokens (`..`), leading dashes (`-`), and illegal filesystem characters (`:*?"<>|`).
- **Rationale**:
  - Catches permission errors before spawning subprocesses, preventing confusing error cascades, partial file writes, and unhandled tracebacks.
  - Stripping leading dashes (`-`) prevents option injection when filenames are passed as arguments to CLI tools.
  - `Path.is_relative_to(base_dir)` provides mathematical proof that symlinks or clever path components cannot escape the user's intended download directory.
- **Alternatives Considered**:
  - *Attempting `os.chmod` to fix read-only directories*: Rejected. Violates principle of least privilege. The CLI must never alter directory permissions on the user's filesystem; it must report the failure and exit.
  - *Simple string replacement of `/`*: Rejected. Does not guard against `..`, leading dashes, or symlink bypasses.

---

## 4. Temporary File Handling & Atomic Finalization

### Decision: In-Place `.part` Staging for Curl and Native Control Isolation for Aria2c
- **Approach**:
  - **`aria2c`**: Runs with `--file-allocation=none`, `-d <dest_dir>`. `aria2c` manages its own resumption state via `.aria2` control files.
  - **`curl`**: Downloads to `<dest_dir>/<filename>.part`. Upon process exit code `0`, renames atomically via `os.replace(part_path, target_path)`.
  - **Cleanup**: If `curl` exits with a non-zero code or receives `SIGINT`, the `.part` file is deleted via `part_path.unlink(missing_ok=True)`.
  - **Interruption**: Forward `SIGINT` to child processes, wait up to 2 seconds, force kill if needed, clean `.part` files, and exit with code `130`.
- **Rationale**:
  - `curl` directly downloading to the target filename leaves truncated/corrupt media files if interrupted. `.part` isolation guarantees that only 100% completed files appear under the target name.
  - `os.replace()` is an atomic operation on POSIX and Windows (NTFS) within the same filesystem volume.
- **Alternatives Considered**:
  - *Writing temporary files to `/tmp` and copying to download directory*: Rejected. Inefficient for multi-gigabyte media files; cross-device moves (`/tmp` to `/home`) are not atomic and require full byte-copying.

---

## 5. Architectural Decoupling & Module Placement

### Decision: Dedicated `f2m/integrations/downloader.py` Module
- **Approach**:
  - Create package `f2m/integrations/` with `f2m/integrations/downloader.py`.
  - Downloader encapsulates:
    - Discovery (`get_available_downloaders()`, `find_downloader()`).
    - Validation (`validate_download_destination()`, `sanitize_filename()`).
    - Execution (`download_urls()`, `stream_url()`).
    - Process management & cleanup (`DownloadJob`, `DownloaderBackend`).
  - Introduce `F2MDownloadError` in `f2m/core/exceptions.py` (exit code `1`).
  - `f2m.py` delegates `do_download()`, `do_stream()`, `copy_links()`, and `download_dir()` to `f2m.integrations.downloader`.
- **Rationale**:
  - Decouples process management and filesystem security from terminal presentation.
  - Enables 100% isolated unit and integration testing without mocking terminal loops or global state.
  - Conforms to Principle IX (clean architectural layering).
