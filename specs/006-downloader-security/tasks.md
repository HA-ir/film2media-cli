# Tasks: Phase 6 — Downloader Security & Sudo Removal

**Input**: Design documents from `specs/006-downloader-security/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/downloader-contract.md`, `quickstart.md`)  
**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/downloader-contract.md`  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project structure initialization, error hierarchy setup, and CLI dispatcher integration.

- [X] T001 Create integrations package directory and init file in `f2m/integrations/__init__.py`
- [X] T002 [P] Define `F2MDownloadError(F2MError)` with `exit_code = 1` in `f2m/core/exceptions.py`
- [X] T003 Ensure CLI runner maps `F2MDownloadError` to POSIX exit code `1` and formats structured `JsonErrorPayload` on `sys.stderr` in `f2m/cli/runner.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, enums, and safe subprocess execution primitives that all downloader stories depend on.

- [X] T004 [P] Implement `DownloaderBackend` enum (`ARIA2C`, `CURL`, `NONE`) and `DownloadRequest`, `DownloadResult`, `StreamRequest`, `StreamResult` dataclasses in `f2m/integrations/downloader.py`
- [X] T005 Implement safe subprocess argument execution helper `run_subprocess` (strictly `list[str]` arguments, zero `shell=True`, environment inheritance) in `f2m/integrations/downloader.py`

**Checkpoint**: Core data structures and execution primitives are ready. User story implementations can proceed.

---

## Phase 3: User Story 1 - Safe, Unprivileged Download Execution (Priority: P1) 🎯 MVP

**Goal**: Eliminate all automated `sudo` executions, package manager invocations, and unverified remote binary downloads. Restrict tool resolution to system `$PATH` via `shutil.which`. Provide platform-specific manual installation guidance with immediate fallback to `curl` or link export.

**Independent Test**: Execute download workflow in an environment where `aria2c` is missing. Verify that copy-paste manual installation commands are displayed on `stderr`, `sudo` is never invoked, no remote binaries are fetched, and downloads cleanly fall back to `curl` or link export.

### Tests for User Story 1 ⚠️

- [X] T006 [P] [US1] Unit test verifying executable discovery strictly on `$PATH` via `shutil.which` and rejecting relative/application directory probing in `tests/unit/test_downloader_security.py`
- [X] T007 [P] [US1] Unit test verifying zero `sudo`, `su`, or package manager commands in generated subprocess command lists in `tests/unit/test_downloader_security.py`
- [X] T008 [P] [US1] Unit test verifying platform-specific manual install instructions for Debian, Fedora, Arch, Alpine, macOS, and Windows in `tests/unit/test_downloader_security.py`
- [X] T009 [P] [US1] Integration test verifying fallback cascade: `aria2c` missing → `curl` fallback → plain links fallback in `tests/unit/test_downloader_security.py`

### Implementation for User Story 1

- [X] T010 [US1] Implement `find_downloader() -> tuple[DownloaderBackend, str | None]` searching strictly on `$PATH` in `f2m/integrations/downloader.py`
- [X] T011 [US1] Implement `get_install_instructions(system: str | None = None) -> str` generating platform-aware copy-paste install commands in `f2m/integrations/downloader.py`
- [X] T012 [US1] Delete `install_aria2c_linux()`, `install_aria2c_windows()`, `install_aria2c()`, `local_aria2c()`, `app_dir()`, `LINUX_PKG_MANAGERS`, and `ARIA2_WIN_URL` from `f2m.py`
- [X] T013 [US1] Update `do_download()` in `f2m.py` to use `find_downloader()` and display manual installation guidance without `sudo`
- [X] T014 [US1] Connect Rich UI guidance panel for missing downloader on `sys.stderr` preserving `--no-color` and `NO_COLOR` compliance in `f2m.py`

**Checkpoint**: User Story 1 complete. System executes downloads 100% unprivileged without `sudo` or remote binary downloads.

---

## Phase 4: User Story 2 - Permission Safety & Path Traversal Protection (Priority: P2)

**Goal**: Validate destination write permissions before downloading, sanitize filenames and subdirectories against path traversal and CLI option injection, ensure path containment within `download_dir`, and create directories with standard user permissions (`0o755`).

**Independent Test**: Attempt download to a read-only directory (`chmod 555`) and verify clean `F2MDownloadError` with exit code `1` and no stack trace. Attempt download with a malicious title (`../../etc/cron.d`) and verify the path is sanitized and strictly confined within `download_dir`.

### Tests for User Story 2 ⚠️

- [X] T015 [P] [US2] Unit test verifying filename sanitization (Unicode NFKC normalization, stripping `..`, null bytes, control characters, `/`, `\`, `:?*<>"|`, leading dashes `-`, trailing dots/spaces) in `tests/unit/test_downloader_security.py`
- [X] T016 [P] [US2] Unit test verifying path containment check `assert_path_contained()` raising `F2MDownloadError` on directory escape in `tests/unit/test_downloader_security.py`
- [X] T017 [P] [US2] Unit test verifying pre-flight write permission validation and clean `F2MDownloadError` for unwritable directories in `tests/unit/test_downloader_security.py`
- [X] T018 [P] [US2] Unit test verifying canonical expansion of `~` and relative paths via `Path.resolve()` in `tests/unit/test_downloader_security.py`
- [X] T019 [P] [US2] Integration test verifying nested output directory creation with standard user permissions (`0o755`) in `tests/unit/test_downloader_security.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `sanitize_filename(name: str) -> str` with traversal and CLI option injection protection in `f2m/integrations/downloader.py`
- [X] T021 [US2] Implement `resolve_destination(raw_dir: str, subdir: str | None = None) -> Path` with pre-flight `os.access(W_OK)` validation and parent-directory checking in `f2m/integrations/downloader.py`
- [X] T022 [US2] Implement `assert_path_contained(target_path: Path, base_dir: Path) -> None` enforcing `target_path.resolve().is_relative_to(base_dir.resolve())` in `f2m/integrations/downloader.py`
- [X] T023 [US2] Implement safe link file generation `export_links(urls: list[str], destination_dir: Path, filename_hint: str) -> Path` in `f2m/integrations/downloader.py`
- [X] T024 [US2] Refactor `download_dir()`, `copy_links()`, and `sanitize()` in `f2m.py` to delegate to `f2m.integrations.downloader`

**Checkpoint**: User Story 2 complete. All output destinations and filenames are strictly validated, sanitized, and confined.

---

## Phase 5: User Story 3 - Atomic Downloads & Interruption Cleanup (Priority: P3)

**Goal**: Implement temporary `.part` file staging for `curl` downloads, atomic finalization via `os.replace()` upon exit code `0`, and signal handling (`SIGINT` / `Ctrl+C`) terminating child processes, unlinking `.part` files, and exiting with POSIX code `130`.

**Independent Test**: Start a `curl` download and interrupt with `SIGINT`. Verify that child processes are terminated, temporary `.part` files are deleted, no corrupt files masquerade as complete media, and the process exits with code `130`.

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] Unit test verifying `curl` download stages to `.part` file and atomically renames via `os.replace` on exit code `0` in `tests/unit/test_downloader_security.py`
- [X] T026 [P] [US3] Unit test verifying failed `curl` download deletes temporary `.part` file and raises `F2MDownloadError` in `tests/unit/test_downloader_security.py`
- [X] T027 [P] [US3] Unit test verifying `SIGINT` interruption terminates child process, removes lingering `.part` file, and raises `KeyboardInterrupt` in `tests/unit/test_downloader_security.py`
- [X] T028 [P] [US3] Unit test verifying streaming player command assembly for `mpv`, `vlc`, and `potplayer` with proxy support in `tests/unit/test_downloader_security.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `execute_download(request: DownloadRequest) -> DownloadResult` with `.part` staging, atomic rename, and failure cleanup in `f2m/integrations/downloader.py`
- [X] T030 [US3] Implement `execute_stream(request: StreamRequest) -> StreamResult` with unprivileged `subprocess.Popen` in `f2m/integrations/downloader.py`
- [X] T031 [US3] Update `do_download()` and `do_stream()` in `f2m.py` to use `execute_download()` and `execute_stream()` with clean signal handling and `130` exit code propagation

**Checkpoint**: User Story 3 complete. Media downloads are atomic, resilient, and leave zero temporary artifacts upon interruption.

---

## Phase 6: End-to-End Testing & Verification

**Purpose**: Black-box subprocess verification across all Phase 6 user-facing features, stream isolation, exit codes, and regression safety.

- [X] T032 [P] E2E test verifying unwritable download directory exits with code `1` and clean diagnostic on `stderr` without tracebacks in `tests/e2e/test_downloader_e2e.py`
- [X] T033 [P] E2E test verifying missing `aria2c` displays manual installation guidance on `stderr` and does NOT invoke `sudo` in `tests/e2e/test_downloader_e2e.py`
- [X] T034 [P] E2E test verifying `SIGINT` during download cleans temporary `.part` files and exits with code `130` in `tests/e2e/test_downloader_e2e.py`
- [X] T035 [P] E2E test verifying stream isolation: `stdout` clean in `--json` and `--plain` modes while downloader logs route strictly to `stderr` in `tests/e2e/test_downloader_e2e.py`
- [X] T036 Run the entire test suite (`pytest tests/unit tests/e2e`) verifying all 85+ regression tests pass with 0 regressions

---

## Phase 7: Documentation & Security Review

**Purpose**: Synchronized bilingual documentation and final security audit.

- [X] T037 [P] Update English documentation in `README.md` documenting unprivileged download execution, `download_dir` resolution, manual `aria2c` installation commands, and permission error handling
- [X] T038 [P] Update Persian documentation in `README.fa.md` maintaining exact parity with English updates
- [X] T039 Execute manual verification scenarios from `specs/006-downloader-security/quickstart.md`
- [X] T040 Final read-only security review verifying zero occurrences of `sudo`, `install_aria2c_linux`, `install_aria2c_windows`, `local_aria2c`, or `shell=True` across the codebase

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1: Setup 
   └── Phase 2: Foundational 
          ├── Phase 3: User Story 1 (P1 - Unprivileged Execution) [MVP]
          ├── Phase 4: User Story 2 (P2 - Permission & Traversal Safety)
          └── Phase 5: User Story 3 (P3 - Atomic Downloads & Signal Cleanup)
                 └── Phase 6: E2E Testing & Regression Gate
                        └── Phase 7: Documentation & Security Review
```

### Parallel Execution Opportunities

- **Phase 1**: T002 (`exceptions.py`) can run in parallel with T001 (`__init__.py`).
- **Phase 2**: T004 (data models) and T005 (subprocess helper) can run in parallel.
- **Phase 3 (US1)**: Test tasks T006, T007, T008, T009 can be written in parallel before implementation tasks T010–T014.
- **Phase 4 (US2)**: Test tasks T015, T016, T017, T018 can be written in parallel before implementation tasks T020–T024.
- **Phase 5 (US3)**: Test tasks T025, T026, T027, T028 can be written in parallel before implementation tasks T029–T031.
- **Phase 6 (E2E)**: E2E test tasks T032, T033, T034, T035 can be written in parallel.
- **Phase 7 (Docs)**: Documentation tasks T037 (English) and T038 (Persian) can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1 - Sudo Removal & Manual Install Guidance).
3. **Validate MVP**: Ensure `sudo` is never invoked, `aria2c` is discovered strictly on `$PATH`, and manual installation commands are presented.

### Incremental Delivery
1. Foundation & US1: Unprivileged execution eliminates `DEF-001`.
2. Add US2: Pre-flight write checks and path traversal sanitization prevent filesystem vulnerabilities and unhandled crashes.
3. Add US3: `.part` atomic staging and `SIGINT` cleanup prevent media file corruption.
4. E2E verification: Confirm stream isolation, exit codes, and regression safety across all 85+ tests.
5. Documentation & Review: Finalize bilingual documentation and verify zero security regressions.
