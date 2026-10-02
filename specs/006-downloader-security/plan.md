# Implementation Plan: Phase 6 — Downloader Security & Sudo Removal

**Branch**: `006-downloader-security` | **Date**: 2026-10-02 | **Spec**: [specs/006-downloader-security/spec.md](spec.md)

**Input**: Feature specification from `/specs/006-downloader-security/spec.md`

---

## Summary

Phase 6 eliminates the project's critical privilege escalation vulnerability (`DEF-001`) by completely removing automated `sudo` executions and unverified remote binary downloads. It decouples the downloader and process execution logic from `f2m.py` into a secure, modular `f2m.integrations.downloader` subsystem. The new subsystem introduces defensive path canonicalization, pre-flight write permission validation, path traversal defense, strict `$PATH`-only executable discovery via `shutil.which`, atomic temporary file handling (`.part`) for `curl` downloads, and clean POSIX signal/interruption handling, while strictly preserving Phase 4 CLI contracts and Phase 5 Rich UI presentation.

---

## Technical Context

**Language/Version**: Python 3.8+ (Linux, macOS, Windows)  
**Primary Dependencies**: Standard library (`subprocess`, `shutil`, `pathlib`, `unicodedata`, `os`), `beautifulsoup4>=4.11.0` (existing), `rich>=13.0.0` (existing)  
**Storage**: Local filesystem (`download_dir` defaulting to `~/Downloads/f2m`)  
**Testing**: `pytest>=7.0.0` (unit and E2E subprocess suites)  
**Target Platform**: Linux, macOS, Windows  
**Project Type**: CLI media client & download manager  
**Performance Goals**: Instant pre-flight checks (<10ms), zero overhead on process spawning  
**Constraints**: Zero `sudo` invocations, zero `shell=True`, 100% path traversal containment, zero lingering `.part` temporary files on interruption, full preservation of 85 existing regression tests  
**Scale/Scope**: Modular refactor of downloader paths, addition of `f2m/integrations/downloader.py`, removal of legacy installer code, unit & E2E tests  

---

## Constitution Check

*GATE: Evaluated against all 10 core principles of `.specify/memory/constitution.md` (v1.0.0).*

1. **Principle I (Professional CLI UX)**: PASS. Provides clean manual installation instructions on `stderr` instead of abrupt password prompts. Signal handling (`Ctrl+C`) exits cleanly with POSIX code `130` without raw Python stack traces.
2. **Principle II (Reliability Over Superficial Visual Changes)**: PASS. Directly addresses root-cause vulnerability `DEF-001` and adds pre-flight write checks to prevent unhandled crashes in read-only environments.
3. **Principle III (Backward Compatibility)**: PASS. Existing configuration values (`download_dir`, `proxy`, `player`) and interactive user choices (Download, Stream, Copy links) remain 100% compatible.
4. **Principle IV (Testability & Multi-Layered Testing)**: PASS. Multi-layered testing planned: comprehensive unit tests for sanitization/containment/permissions and subprocess E2E tests for exit codes and stream isolation.
5. **Principle V (Documentation as Implementation)**: PASS. Bilingual documentation updates planned for `README.md` and `README.fa.md` covering the security model, download directories, and manual installation guidance.
6. **Principle VI (Incremental Delivery & Branch Discipline)**: PASS. Isolated strictly to Phase 6 on feature branch `006-downloader-security`. Zero bundling of Phase 7 packaging or CI/CD.
7. **Principle VII (PR Ownership & Merge Control)**: PASS. Automated agents prepare the branch and tests, but do not push to master or merge. PR review and merge remain human-owned.
8. **Principle VIII (End-to-End Acceptance Gate)**: PASS. E2E tests and regression suite are mandatory gates before declaring completion.
9. **Principle IX (Scope Discipline & Proportional Refactoring)**: PASS. Scraper, DOM parser, CLI parser, and UI presentation remain completely untouched. Scoped strictly to downloader subsystem.
10. **Principle X (Honest & Verifiable Claims)**: PASS. All claims verifiable through concrete pytest executions.

---

## Project Structure

### Documentation (this feature)

```text
specs/006-downloader-security/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Phase 0 decisions & rationales
├── data-model.md        # Phase 1 entities & validation rules
├── quickstart.md        # Phase 1 runnable validation guide
├── contracts/           # Phase 1 interface contracts
│   └── downloader-contract.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16 passing)
└── tasks.md             # Phase 2 task breakdown (/speckit-tasks)
```

### Source Code (repository root)

```text
f2m/
├── core/
│   ├── exceptions.py         # Add F2MDownloadError(F2MError)
│   └── models.py             # Existing domain models
├── integrations/             # NEW PACKAGE: external process & tool integrations
│   ├── __init__.py           # Package init
│   └── downloader.py         # Secure downloader & process execution subsystem
├── cli/
│   ├── models.py             # Existing CLI models
│   ├── parser.py             # Existing CLI parser
│   ├── formatters.py         # Existing stream formatters
│   └── runner.py             # Central CLI runner (maps F2MDownloadError -> 1)
├── ui/
│   ├── views.py              # Existing Rich UI presentation
│   └── console.py            # Existing console singletons
└── net/
    └── client.py             # Existing network client

f2m.py                        # Legacy script: remove sudo/installer methods;
                              # delegate do_download, do_stream, copy_links,
                              # and download_dir to f2m.integrations.downloader

tests/
├── unit/
│   ├── test_downloader_security.py # NEW: Path sanitization, traversal defense,
│   │                               # pre-flight write check, $PATH discovery,
│   │                               # absence of sudo, atomic .part staging
│   └── ... (existing 7 unit test files)
└── e2e/
    ├── test_downloader_e2e.py      # NEW: Subprocess tests for unwritable dir,
    │                               # missing downloader fallback, and exit code 130
    └── ... (existing 5 e2e test files)

README.md                     # Bilingual documentation updates (English)
README.fa.md                  # Bilingual documentation updates (Persian)
```

**Structure Decision**: A dedicated `f2m/integrations/downloader.py` module decouples external process management and filesystem security from both `f2m.py` and the CLI layer. This ensures that download security logic is independently testable, reusable across interactive and headless modes, and adheres to the architectural separation mandate of the constitution.

---

## Detailed Implementation Modules

### 1. `f2m/core/exceptions.py`
- Add `F2MDownloadError(F2MError)` with class attribute `exit_code: int = 1`.
- Used for destination unwritable, path traversal attempts, missing download tools, or child process failures.

### 2. `f2m/integrations/downloader.py` (New Module)
- **Data Entities**: `DownloaderBackend` enum, `DownloadRequest`, `DownloadResult`, `StreamRequest`, `StreamResult`.
- **Discovery**:
  - `find_downloader() -> tuple[DownloaderBackend, str | None]`: Probes `shutil.which("aria2c")`, then `shutil.which("curl")`. Strictly on `$PATH`.
  - `get_install_instructions(system: str | None = None) -> str`: Returns OS-tailored manual install command.
- **Path Resolution & Sanitization**:
  - `resolve_destination(raw_dir: str, subdir: str | None = None) -> Path`: Expands `~`, canonicalizes via `.resolve()`, checks `os.access(W_OK)`, creates directory with `0o755`.
  - `sanitize_filename(name: str) -> str`: Normalizes NFKC, strips `..`, null bytes, control characters, `/`, `\`, `:?*<>"|`, leading dashes (`-`), and trailing dots/spaces.
  - `assert_path_contained(target_path: Path, base_dir: Path) -> None`: Asserts `target_path.resolve().is_relative_to(base_dir.resolve())`.
- **Execution**:
  - `execute_download(request: DownloadRequest) -> DownloadResult`:
    - Zero `shell=True`.
    - If `aria2c`: runs with `--file-allocation=none`, `-d <dir>`, `--all-proxy` (if proxy configured).
    - If `curl`: loops over URLs, writes to `<dest>/<filename>.part`, atomically renames via `os.replace` on exit code 0, unlinks `.part` on failure.
    - Handles `KeyboardInterrupt`: terminates active child processes, cleans `.part` files, and raises `KeyboardInterrupt`.
  - `execute_stream(request: StreamRequest) -> StreamResult`:
    - Discovers `mpv`/`vlc`/`potplayer` via `shutil.which` and well-known paths.
    - Spawns player via `subprocess.Popen` with argument list.
  - `export_links(urls: list[str], destination_dir: Path, filename_hint: str) -> Path`:
    - Writes links cleanly to `<destination_dir>/<sanitized_hint>.txt`.
    - Optional Windows clipboard copy via `clip` (unprivileged).

### 3. `f2m/cli/runner.py`
- Verify that `F2MDownloadError` maps to exit code `1` and emits structured JSON error payload on `stderr` when in `--json` mode.

### 4. `f2m.py`
- Remove: `LINUX_PKG_MANAGERS`, `ARIA2_WIN_URL`, `ARIA2_VERSION`, `app_dir()`, `local_aria2c()`, `install_aria2c_linux()`, `install_aria2c_windows()`, `install_aria2c()`, `find_aria2c()`.
- Refactor `download_dir()` to call `downloader.resolve_destination(_cfg["download_dir"])`.
- Refactor `do_download()` to call `downloader.execute_download()`.
- Refactor `do_stream()` to call `downloader.execute_stream()`.
- Refactor `copy_links()` to call `downloader.export_links()`.
- Refactor `sanitize()` to delegate to `downloader.sanitize_filename()`.

### 5. Automated Tests
- `tests/unit/test_downloader_security.py`:
  - `test_sanitize_filename_traversal`: Ensures `../../etc/passwd` cannot escape.
  - `test_sanitize_filename_leading_dashes`: Ensures leading dashes are stripped to prevent CLI option injection.
  - `test_sanitize_filename_control_characters`: Ensures null bytes and control chars are removed.
  - `test_resolve_destination_success`: Verifies `~` expansion and canonical directory creation.
  - `test_resolve_destination_read_only_failure`: Verifies unwritable directory raises `F2MDownloadError`.
  - `test_path_containment_enforcement`: Verifies escaping paths trigger `F2MDownloadError`.
  - `test_find_downloader_discovery`: Verifies discovery strictly on `$PATH` without checking application directory.
  - `test_absence_of_sudo_in_commands`: Asserts zero `sudo` or package manager strings in generated command lists.
  - `test_curl_atomic_part_success`: Mocks curl, verifies `.part` renamed to target via `os.replace`.
  - `test_curl_atomic_part_failure_cleanup`: Mocks failing curl, verifies `.part` unlinked.
- `tests/e2e/test_downloader_e2e.py`:
  - `test_e2e_download_unwritable_destination`: Configures read-only directory, asserts exit code `1` and clean error on `stderr`.
  - `test_e2e_missing_aria2c_guidance`: Shadows `aria2c`, asserts manual install instructions printed on `stderr` without `sudo`.
  - `test_e2e_stream_isolation_preserved`: Ensures download diagnostics route strictly to `stderr`.

---

## Complexity Tracking

| Issue / Decision | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Dedicated `f2m/integrations/downloader.py` | Encapsulates process orchestration and security boundaries away from UI script | Keeping it in `f2m.py` perpetuates monolithic coupling and prevents clean unit testing |
| Pre-flight `os.access(W_OK)` check | Prevents unhandled tracebacks and partial file operations in read-only environments | Catching `PermissionError` inside subprocesses is messy and leaks backend-specific errors |
| Atomic `.part` staging for `curl` | Prevents corrupt or truncated files from masquerading as completed media | Directly downloading to destination leaves corrupt files upon interruption |
