# Feature Specification: Phase 6 — Downloader Security & Sudo Removal

**Feature Branch**: `feat/phase-6-downloader-security`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "Phase 6 — Downloader Security / Sudo Removal: Remove the application's dependency on sudo/root privileges for normal downloading, eliminate automated privilege escalation and unverified binary downloads, and make the downloader security model explicit, safe, predictable, and user-owned while preserving existing CLI/UI capabilities."

---

## 1. Executive Summary & Purpose

Across Phases 1 through 5, `film2media-cli` established automated test infrastructure, domain entities with XDG configuration, a BeautifulSoup4 DOM scraper with resilient network transport, a headless CLI engine with POSIX exit codes, and a Rich-based terminal UI with BiDi safety.

Phase 6 resolves the project's most critical remaining security vulnerability: **Unauthorized Privilege Escalation & Unsafe Subprocess Execution in the Downloader Subsystem** (`DEF-001`). Currently in `f2m.py`:
1. **Silent Privilege Escalation (`sudo`)**: `install_aria2c_linux()` checks if `aria2c` is missing and automatically invokes `sudo <pkg_manager> install -y aria2` across system package managers (`apt-get`, `dnf`, `yum`, `pacman`, `apk`, `zypper`) without user consent, triggering unexpected password prompts or running commands as root.
2. **Unverified Remote Binary Execution**: `install_aria2c_windows()` downloads a remote `.zip` archive over HTTP/HTTPS from GitHub without cryptographic hash verification, extracts `aria2c.exe`, and copies it to `app_dir()`. If `f2m` was installed system-wide in `C:\Program Files`, this triggers permission crashes or writes unvetted executables into shared locations.
3. **Unsanitized Path Handling & Destination Assumptions**: `download_dir()` creates directories using `os.makedirs(path, exist_ok=True)` without validating write permissions beforehand. If the destination directory exists but is read-only, `aria2c` or `curl` crashes or fails ungracefully.
4. **Ad-Hoc Download Subprocess Invocations**: Downloader logic is embedded directly in `f2m.py` (`do_download`, `install_aria2c`, `local_aria2c`), mixing UI, process orchestration, and filesystem manipulation.

Phase 6 introduces a secure, decoupled downloader subsystem in `f2m/integrations/downloader.py`:
- **Complete Elimination of `sudo`**: Normal downloads run strictly under the unprivileged user account. The application NEVER invokes `sudo`, su, or elevated package manager commands.
- **Manual Installation Guidance with Instant Fallback**: When `aria2c` is missing, the tool displays clear, platform-specific copy-paste installation instructions (`sudo apt install aria2`, `brew install aria2`, `winget install aria2`), and immediately offers graceful fallback to `curl` (if available) or direct link export (`copy_links`).
- **Elimination of Unverified Binary Downloads**: Automatic extraction of remote binaries from GitHub is completely removed.
- **Defensive Path Validation & Traversal Protection**: Output directories and sanitized filenames are strictly validated to prevent directory traversal (`../`, null bytes, control characters, leading slashes), and destination paths are checked for write permissions before initiating downloads.
- **Atomic & Temporary File Integrity**: Incomplete downloads using `curl` write to temporary `.part` files and rename atomically upon completion, preventing partial files from masquerading as finished media.
- **Full CLI & UI Compatibility**: Phase 4 contracts (`--json`, `--plain`, `--no-color`, exit codes) and Phase 5 Rich presentation remain completely preserved.

---

## 2. Clarifications & Architectural Decisions

### Session 2026-10-02

- Q: How should `f2m` handle missing `aria2c` without using `sudo`? → A: Display manual copy-paste installation commands for the current OS and immediately offer fallback to `curl` or link export without privilege escalation.
- Q: How should output directories and filenames be validated against path traversal? → A: Canonicalize paths via `Path.resolve()`, strip traversal sequences (`..`), null bytes, control characters, and leading dashes, and verify `target.is_relative_to(download_dir)`.
- Q: What behavior occurs when the destination directory is not writable? → A: Perform a pre-flight write permission check (`os.access(dest, os.W_OK)`) and raise `F2MDownloadError` with a clear message and exit code `1` without attempting `chmod`/`chown`.
- Q: How should partial/interrupted `curl` downloads be handled? → A: Download to `.part` files, rename atomically with `os.replace()` on exit code `0`, and clean up `.part` files on failure or `Ctrl+C` (exit code `130`).

#### 1. Downloader Architecture & Decoupling
- **New Module**: `f2m/integrations/downloader.py` encapsulates all download manager discovery, argument construction, process execution, and fallback strategies.
- **Discovery Strategy**:
  - `find_downloader() -> tuple[str | None, str]`: Detects available external download accelerators using `shutil.which`. Searches strictly on system `$PATH`.
  - Prioritizes `aria2c` (multi-connection, resumable).
  - Falls back to `curl` (sequential single-connection, widespread availability).
  - If neither is available, provides direct link export or terminal display.
- **Zero Local Binary Probing in Application Directory**:
  - `local_aria2c()` in `app_dir()` is removed. Binaries must reside on `$PATH` or in standard system directories to prevent local binary hijacking.

#### 2. Sudo Removal & Privilege Escalation Invariants
- **No Automated System Package Management**:
  - All calls to `install_aria2c_linux()` iterating through `LINUX_PKG_MANAGERS` (`apt-get`, `dnf`, `yum`, etc.) with `sudo` are completely eliminated.
  - All calls to `install_aria2c_windows()` downloading remote GitHub zip files into application folders are completely eliminated.
- **User-Facing Guidance Policy**:
  - If `aria2c` is not detected on the system:
    - Interactive mode: Displays an informative Rich notice with platform-specific install commands:
      - Debian/Ubuntu: `sudo apt install aria2`
      - Fedora/RHEL: `sudo dnf install aria2`
      - Arch Linux: `sudo pacman -S aria2`
      - macOS: `brew install aria2`
      - Windows: `winget install aria2`
    - Immediately falls back to `curl` if installed.
    - If `curl` is also missing, falls back to copying/displaying direct download URLs.
  - Zero password prompts are ever triggered by `film2media-cli`.

#### 3. Output Directory Resolution & Path Traversal Defense
- **Path Resolution**:
  - `download_dir` is resolved via `Path(os.path.expanduser(config["download_dir"])).resolve()`.
  - Tilde (`~`) is expanded to the invoking user's home directory.
  - Default: `~/Downloads/f2m`.
- **Pre-Flight Write Permission Checks**:
  - Before spawning `aria2c` or `curl`, the system validates that:
    1. The destination directory exists or can be created by the user.
    2. The destination directory has write permissions (`os.access(dest, os.W_OK)`).
  - If the directory is not writable (e.g., owned by root or mounted read-only), `f2m` raises `F2MDownloadError("Destination directory '{dest}' is not writable")` with POSIX exit code `1` (or exit code `3` if the configured `download_dir` is fundamentally invalid), presenting a clear actionable diagnostic on `stderr` instead of an unhandled traceback.
- **Path Traversal & Filename Sanitization**:
  - Subdirectories and filenames derived from scraped media metadata (e.g. `post.title` or URL slugs) are sanitized:
    - Strips directory traversal tokens (`..`, `/`, `\`).
    - Strips control characters, null bytes (`\0`), and reserved filesystem characters (`:`, `*`, `?`, `"`, `<`, `>`, `|`).
    - Replaces forbidden sequences with an underscore (`_`).
    - Ensures target path resides strictly inside the designated `download_dir`. Any target path attempting to escape `download_dir` via traversal raises `F2MDownloadError`.

#### 4. Safe Subprocess Execution
- **Zero Shell Invocations**:
  - All process invocations (`aria2c`, `curl`, `mpv`, `vlc`) use structured argument lists (`list[str]`) passed directly to `subprocess.run` or `subprocess.Popen`.
  - `shell=True` is strictly prohibited.
- **Environment & Proxy Passing**:
  - Subprocess environments inherit standard user environment (`os.environ`).
  - Proxies configured via `F2M_PROXY` or `config.ini` are passed as explicit CLI flags:
    - `aria2c`: `--all-proxy=<proxy>`
    - `curl`: `--proxy <proxy>`
    - `mpv`: `--http-proxy=<proxy>`
    - `vlc`: `--http-proxy=<proxy>`
- **Signal Handling & Process Interruption**:
  - If the user presses `Ctrl+C` (`SIGINT`), the CLI forwards the interrupt cleanly to child processes (`aria2c` / `curl`), waits for process termination, and exits with POSIX code `130`.

#### 5. Temporary Files & Atomicity
- **`aria2c` Execution**:
  - `aria2c` manages its own resumption state via `.aria2` control files.
  - Runs with `--file-allocation=none`, `--console-log-level=warn`, `--summary-interval=0`, `--download-result=hide`.
- **`curl` Execution**:
  - For each URL, `curl` downloads to a temporary `.part` file:
    `out_part = f"{out}.part"`
  - Once `curl` exits with status `0`, `out_part` is atomically renamed to `out` via `os.replace()`.
  - If `curl` is interrupted or fails with a non-zero code, `out_part` is cleaned up to prevent corrupted files.

#### 6. Codebase Clarification & Source-of-Truth Analysis (34 Points)

Based on direct inspection of the current `master` implementation across `f2m.py`, `f2m/core/`, `f2m/net/`, `f2m/cli/`, and `f2m/ui/`:

1. **Affected Downloader Paths**:
   - `download_dir()` (`f2m.py:530`): Resolves download target without pre-flight write validation.
   - `do_download()` (`f2m.py:536`): Direct process orchestration for `aria2c` and `curl`, in-line fallback, lacks atomic staging for `curl`.
   - `do_stream()` (`f2m.py:576`): Streaming player execution via `subprocess.Popen`.
   - `copy_links()` (`f2m.py:595`): Link file generation in `download_dir()`.
   - `find_aria2c()`, `local_aria2c()`, `install_aria2c()`, `install_aria2c_linux()`, `install_aria2c_windows()` (`f2m.py:419-478`): Privilege escalation via `sudo`, unverified GitHub downloads, local binary probing.
   - `app_dir()` (`f2m.py:413`): Application directory lookup for local binaries.
   - `player_command()`, `find_player()` (`f2m.py:480-523`): Player discovery and command assembly.

2. **Every Current Sudo/Root Usage & Privilege Assumption**:
   - `install_aria2c_linux()` lines 458-472:
     ```python
     sudo = os.geteuid() != 0 and shutil.which("sudo")
     for mgr, args in LINUX_PKG_MANAGERS.items():
         if not shutil.which(mgr):
             continue
         cmd = ([sudo] if sudo else []) + [mgr] + args + ["aria2"]
     ```
   - Silently invokes `sudo <pkg_mgr> install -y aria2` without explicit user permission.
   - Zero other `sudo` invocations exist in the codebase.
   - **Resolution**: Completely eliminate `install_aria2c_linux()` and automated package manager executions.

3. **External Downloader Tools Used**:
   - `aria2c`: Primary download accelerator.
   - `curl`: Fallback single-connection downloader.
   - Media players: `mpv`, `vlc`, `potplayer` (streaming).
   - Clipboard: `clip` on Windows.

4. **Executable Resolution**:
   - Currently uses `shutil.which` plus `local_aria2c()` which checks the application folder (`app_dir()`).
   - Checking `app_dir()` presents a binary hijacking/planting vulnerability.
   - **Resolution**: Strict resolution via `shutil.which` against `$PATH` only. Remove `local_aria2c()`.

5. **Subprocess Calls & Shell Execution**:
   - Current subprocess calls use argument lists (`subprocess.call(cmd)`, `subprocess.Popen(cmd)`).
   - Zero calls currently use `shell=True`.
   - **Resolution**: Maintain strict ban on `shell=True`. Pass validated `list[str]` arguments.

6. **Download Destination Selection**:
   - Configured via `config["download_dir"]` (default `~/Downloads/f2m`).
   - If `subdir` is passed to `do_download(urls, subdir)`: `dest = os.path.join(dest, sanitize(subdir))`.
   - In `copy_links`: `path = os.path.join(download_dir(), sanitize(name_hint) + ".txt")`.

7. **Path Semantics (Relative, Absolute, ~)**:
   - Currently: `path = os.path.expanduser(_cfg["download_dir"])`. Relative paths stay relative to `os.getcwd()`.
   - **Resolution**: Canonicalize using `Path(os.path.expanduser(_cfg["download_dir"])).resolve()`.

8. **Output Directory Creation**:
   - Currently: `os.makedirs(path, exist_ok=True)` without write permission validation.
   - **Resolution**: Pre-flight validation checks `os.access(path, os.W_OK)`. If path does not exist, checks parent directory write permission before creation.

9. **Existing File Handling**:
   - `aria2c`: Manages resumption or appends suffix according to aria2 defaults.
   - `curl`: `curl -o out` overwrites existing files without atomic isolation.
   - **Resolution**: For `curl`, write to `.part` file and atomically rename (`os.replace`) on exit code `0`.

10. **Filename Generation & Sanitization**:
    - Current: `sanitize(name)` replaces `[\\/:*?"<>|]+` with `_`.
    - **Defect**: Does NOT sanitize directory traversal sequences like `..`, leading dashes (`-`), control characters, or null bytes.
    - **Resolution**: Strip `..`, leading dashes (to prevent CLI flag injection in external tools), control characters, and verify `Path.is_relative_to(download_dir)`.

11. **Remote/Untrusted Filename Origin**:
    - Filenames derive from scraped URL slugs (`u.rsplit("/", 1)[-1]`) and media titles (`post.title`), both untrusted remote content.
    - **Resolution**: Treat 100% of scraped filenames as untrusted inputs requiring sanitization.

12. **Path Traversal Risks**:
    - Malicious metadata containing `../../etc/cron.d` could escape download directory.
    - **Resolution**: Sanitize path components and enforce boundary check via `dest_file.resolve().is_relative_to(download_dir.resolve())`.

13. **Symlink Risks**:
    - If `download_dir` points to a symlink or contains symlink subdirectories escaping intended storage.
    - **Resolution**: `Path.resolve()` resolves symlinks to their canonical real paths before boundary containment checking.

14. **Temporary-File Handling**:
    - Currently: `install_aria2c_windows()` creates temporary zip files in `app_dir()`.
    - **Resolution**: Remove unverified Windows binary downloads completely. For `curl` downloads, write to `<filename>.part` in `dest`.

15. **Partial-Download Handling**:
    - `aria2c`: Resumes partial transfers using `.aria2` control files.
    - `curl`: Currently leaves corrupted/partial files at final target.
    - **Resolution**: `curl` downloads to `.part`; incomplete `.part` files are deleted on non-zero exit codes.

16. **Atomic Rename & Finalization**:
    - For `curl`, temporary `.part` file is atomically renamed to destination via `os.replace()` only upon verified exit code `0`.

17. **Ctrl+C & Signal Interruption Behavior**:
    - When `Ctrl+C` (`SIGINT`) is received during a download, child processes are terminated, temporary `.part` files are removed, and the process exits with POSIX code `130`.

18. **File Ownership Expectations**:
    - All files and directories are created under the invoking user's account with current process UID/GID. Zero root ownership.

19. **File & Directory Permission Expectations**:
    - Standard user umask (`0o755` for directories, `0o644` for files). World-writable permissions (`0o777`) are strictly forbidden.

20. **Non-Writable Destination Behavior**:
    - When `os.access(dest, os.W_OK)` is false, raises `F2MDownloadError`.
    - Outputs informative error to `stderr` without unhandled tracebacks. Exits with code `1`.

21. **Absence of Permission Repair (No chmod/chown)**:
    - `film2media-cli` MUST NOT attempt to repair permissions via `chmod` or `chown`. Permission management is the responsibility of the system administrator.

22. **Zero Elevated Privileges Requirement**:
    - No operation in `film2media-cli` genuinely requires elevated privileges. All functionality executes in unprivileged user space.

23. **Privilege & Permission Failure Surfacing**:
    - Interactive mode: Rich-styled error panel/message on `stderr`.
    - Headless/JSON mode: Structured JSON error payload on `stderr`.
    - Plain text: Concise error line on `stderr`.

24. **Interaction with Phase 4 Exit Codes**:
    - Normal success: `0`.
    - Operational/download error: `1` (`F2MDownloadError`).
    - CLI argument error: `2`.
    - Configuration error: `3`.
    - Interruption: `130`.

25. **JSON Error Output Contract**:
    - In `--json` mode, error payloads emit exclusively on `stderr`:
      `{"error": true, "code": "DOWNLOAD_ERROR", "message": "...", "exit_code": 1}`.
    - `stdout` remains 100% clean.

26. **Plain-Mode Output Contract**:
    - In `--plain` mode, link exports emit clean URLs to `stdout`. Diagnostics emit to `stderr`.

27. **stdout/stderr Isolation**:
    - `stdout`: Reserved exclusively for data payloads.
    - `stderr`: Reserved exclusively for progress, logs, notices, warnings, and errors.

28. **Phase 5 Rich UI & Status Behavior**:
    - Manual installation instructions and status panels use Rich `Console(file=sys.stderr)`.
    - Progress spinners run on `stderr` and are disabled in non-interactive/piped environments.

29. **--no-color & NO_COLOR Compliance**:
    - Respected across all output channels; ANSI escapes omitted when active.

30. **Non-Interactive Execution**:
    - When `sys.stdout` or `sys.stdin` is not a TTY, fallback actions execute without interactive prompts.

31. **Security Testing Strategy**:
    - Unit tests covering: path traversal sanitization, permission validation, absence of `sudo` in command lists, absence of unverified remote downloads, temporary file cleanup on interruption.

32. **E2E Testing Strategy**:
    - Subprocess tests for unwritable directories (exit code `1`), missing downloader fallback, and `SIGINT` handling (exit code `130`).

33. **Backward Compatibility Expectations**:
    - All config options (`download_dir`, `proxy`, `player`) remain supported.
    - Interactive menus remain identical in options and flow.

34. **Explicit Phase 7 Exclusions**:
    - Packaging (`pyproject.toml` console scripts / wheel building).
    - Release automation, GitHub Actions CI/CD pipelines, PyPI publishing.

---

## 3. User Scenarios & Testing *(mandatory)*

### User Story 1 - Safe, Unprivileged Download Execution (Priority: P1)
As a standard non-root terminal user, I want `f2m` to download media files into my user directory using `aria2c` or `curl` without ever asking for my `sudo` password or attempting privilege escalation, so that running the CLI is safe, predictable, and cannot compromise system packages.

**Why this priority**: Essential security fix. Resolves `DEF-001` (unauthorized privilege escalation).

**Independent Test**: Execute a download workflow in an environment where `aria2c` is not installed. Verify that the tool displays manual installation instructions, does NOT invoke `sudo`, does NOT download external binaries, and cleanly falls back to `curl` or link export.

**Acceptance Scenarios**:
1. **Given** `aria2c` is not installed on Linux, **When** the user initiates a download, **Then** `f2m` displays copy-paste installation instructions (`sudo apt install aria2`), does NOT spawn `sudo`, and immediately offers fallback to `curl`.
2. **Given** `aria2c` is not installed on Windows, **When** the user initiates a download, **Then** `f2m` displays `winget install aria2`, does NOT download arbitrary unverified `.zip` files from GitHub, and offers fallback to `curl` or link copying.
3. **Given** `aria2c` is installed, **When** downloading media files, **Then** `aria2c` executes under the invoking user's account without privilege modification and places files in the designated download directory.

---

### User Story 2 - Permission Safety & Path Traversal Protection (Priority: P2)
As a user downloading files, I want the CLI to validate destination write permissions before downloading and protect against malicious filenames or directory traversal, so that downloads cannot write to unauthorized filesystem locations or crash with unhandled tracebacks.

**Why this priority**: Prevents arbitrary file write vulnerabilities and unhandled crashes in read-only environments.

**Independent Test**: Attempt to download files into a read-only directory (`chmod 555`). Verify that `f2m` catches the permission error, outputs a clear diagnostic message, and exits cleanly with code `1`. Attempt to download a file with a malicious title containing `../../etc/cron.d`. Verify that the filename is sanitized and confined strictly within `download_dir`.

**Acceptance Scenarios**:
1. **Given** the configured `download_dir` is located in a read-only directory, **When** initiating a download, **Then** `f2m` reports an informative permission error to `stderr` and terminates cleanly without an unhandled traceback.
2. **Given** media metadata containing directory traversal tokens (e.g. `../../evil`), **When** constructing target filenames, **Then** traversal tokens are stripped/sanitized and the final path is guaranteed to remain inside `download_dir`.
3. **Given** a nonexistent nested directory within user permissions, **When** downloading, **Then** the directory is created with standard user permissions (`0o755` / standard umask).

---

### User Story 3 - Atomic Downloads & Interruption Cleanup (Priority: P3)
As a user on an unstable network or one who frequently cancels downloads with `Ctrl+C`, I want partially downloaded files to be safely isolated and cleaned up, so that incomplete files do not masquerade as valid media.

**Why this priority**: Preserves filesystem hygiene and prevents corrupt media playback.

**Independent Test**: Start a multi-file download with `curl` fallback and interrupt it with `SIGINT` halfway through. Verify that the `.part` file is deleted and no zero-byte or corrupt completed files remain on disk.

**Acceptance Scenarios**:
1. **Given** a download using `curl`, **When** the transfer is active, **Then** bytes are written to a `.part` temporary file.
2. **Given** a successful `curl` transfer, **When** the download finishes, **Then** the file is atomically renamed to its final target name.
3. **Given** a user cancellation (`Ctrl+C`), **When** interrupted, **Then** child processes are terminated, temporary `.part` files are removed, and the process exits with POSIX code `130`.

---

### Edge Cases
- **Both `aria2c` and `curl` are missing**: If neither download tool is installed, `f2m` prints installation instructions for `aria2c`, emits direct download links to the terminal/clipboard, and exits cleanly without error.
- **Configured `download_dir` is a file instead of a directory**: Detected during pre-flight validation; reports an error that destination path is a file and exits cleanly.
- **Disk full during download**: `aria2c` or `curl` exit codes are captured; `f2m` reports the error cleanly to `stderr`.
- **Trailing slashes, spaces, and Unicode normalization in filenames**: Filenames are normalized via `unicodedata.normalize("NFKC", ...)` and stripped of leading/trailing spaces or periods to prevent Windows filesystem quirks.

---

## 4. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST encapsulate all external process execution and download operations in a dedicated module `f2m/integrations/downloader.py`.
- **FR-002**: System MUST NEVER invoke `sudo`, `su`, or any privileged package manager commands (`apt-get`, `dnf`, `yum`, `pacman`, `apk`, `zypper`).
- **FR-003**: System MUST NEVER automatically download, extract, or execute unverified remote executable binaries.
- **FR-004**: System MUST discover external tools (`aria2c`, `curl`, `mpv`, `vlc`, `potplayer`) strictly via system `$PATH` lookup using `shutil.which`.
- **FR-005**: System MUST provide platform-specific manual installation commands when `aria2c` is not found, immediately offering graceful fallback to `curl` or link export.
- **FR-006**: System MUST resolve `download_dir` safely, expanding `~` to the invoking user's home directory.
- **FR-007**: System MUST validate destination directory existence and write permissions (`os.access(W_OK)`) prior to spawning download subprocesses.
- **FR-008**: System MUST sanitize all target filenames and subdirectories, replacing directory traversal tokens (`..`, `/`, `\`), control characters, and reserved symbols with an underscore (`_`).
- **FR-009**: System MUST verify that resolved download file paths reside strictly within the designated `download_dir`, rejecting any path that escapes the boundary.
- **FR-010**: System MUST execute external subprocesses using explicit argument lists without `shell=True`.
- **FR-011**: System MUST write in-progress `curl` downloads to temporary `.part` files, renaming atomically via `os.replace` only upon complete success.
- **FR-012**: System MUST clean up temporary `.part` files if a `curl` download fails or is interrupted by the user (`Ctrl+C`).
- **FR-013**: System MUST cleanly terminate child download processes and exit with POSIX code `130` upon user interruption (`SIGINT`).
- **FR-014**: System MUST route download diagnostic messages and status notices exclusively to `stderr` in headless/scripted modes.
- **FR-015**: System MUST preserve all Phase 4 CLI contracts (`--json`, `--plain`, `--no-color`, exit codes) and Phase 5 Rich presentation.
- **FR-016**: System MUST introduce `F2MDownloadError` in `f2m/core/exceptions.py` for all download-related permission and execution failures.

---

### Key Entities

- **`DownloaderType`**: Enum representing available download backends (`ARIA2C`, `CURL`, `NONE`).
- **`DownloadRequest`**: Dataclass encapsulating media URL, sanitized target filename, destination directory, proxy configuration, and referer.
- **`DownloadResult`**: Dataclass encapsulating execution success, exit code, downloaded file path, and error message.
- **`F2MDownloadError`**: Exception raised when download preparation, permissions, or process execution fails.

---

## 5. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 invocations of `sudo` or remote binary downloads anywhere in the codebase.
- **SC-002**: 100% of download attempts into read-only directories are caught prior to process execution and produce actionable diagnostics without tracebacks.
- **SC-003**: 100% of malicious path traversal attempts (`../../`) are sanitized and confined strictly within `download_dir`.
- **SC-004**: 100% of subprocess invocations use structured argument lists without `shell=True`.
- **SC-005**: All 85 existing unit and E2E regression tests from Phases 1–5 continue to pass with zero regressions.
- **SC-006**: Interrupted `curl` downloads leave 0 lingering `.part` temporary files on disk.

---

## 6. Assumptions & Scope Exclusions

### Assumptions
- `aria2c` and `curl` binaries installed on `$PATH` by the system package manager or user are trustworthy.
- Standard operating system filesystem semantics (POSIX and Windows NTFS) support atomic file replacement (`os.replace`) on the same filesystem volume.

### Scope Exclusions
- **Packaging & PyPI Distribution**: Python wheel building, entry points (`console_scripts`), and release CI pipelines are strictly deferred to **Phase 7**.
- **Scraper / Network Modifications**: Scraper DOM extraction and HTTP client retry/mirror failover remain untouched.
- **Terminal UI Layout**: Rich presentation components from Phase 5 remain presentation-only.

---

## 7. Backward Compatibility Invariants

1. **Download Configuration**:
   - `download_dir`, `proxy`, and `player` in `config.ini` and `F2M_*` environment variables remain 100% supported.
2. **Interactive Selection Flow**:
   - The interactive download, stream, and link copy choices in `after_selection()` remain completely intact.
3. **CLI Arguments & Exit Codes**:
   - All Phase 4 commands and exit codes (`0`, `1`, `2`, `3`, `4`, `5`, `6`, `130`) remain invariant.
