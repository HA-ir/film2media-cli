# Implementation Plan: film2media-cli Modernization

**Branch**: `001-baseline-specification` | **Date**: 2026-10-01 | **Spec**: [specs/001-baseline-specification/spec.md](spec.md)

**Input**: Feature specification from `specs/001-baseline-specification/spec.md`

---

## Important Governance Notice
> **CRITICAL RULE**: **Only the repository owner may merge a PR.**  
> Automated agents, tools, or bots are strictly prohibited from merging pull requests, enabling auto-merge, or pushing directly to protected/default branches (`master`, `main`). Agents may prepare branches, commits, tests, documentation, and draft PRs, but MUST stop and wait for human review, verification, and explicit merge.

---

## Summary

Transform `film2media-cli` from a monolithic, procedural, single-file script (`f2m.py`, ~1,400 LOC) into a professional, modular, secure, and reliable terminal application. The technical approach introduces a decoupled package architecture (`f2m`), a comprehensive offline test harness with recorded HTML/JSON fixtures, a resilient DOM-based scraping engine, an XDG-compliant configuration system with legacy auto-migration, a headless CLI engine with POSIX exit codes, a flicker-free interactive terminal UX with visual cell-width alignment for Persian text, and secure external tool orchestration that eliminates unauthorized `sudo` executions.

Delivery is strictly partitioned into seven small, independently reviewable, and testable phases to prevent oversized pull requests.

---

## Technical Context

**Language/Version**: Python 3.8+ (cross-platform Linux, macOS, Windows).

**Primary Dependencies**:
- Runtime: `rich` (terminal UI, tables, Unicode/RTL cell width, progress indicators), `beautifulsoup4` with standard `html.parser` (resilient tree scraping).
- Development / Testing: `pytest`, `pytest-cov`, `pytest-mock`, `ruff`.
- Packaging: `pyinstaller` (for compiling standalone zero-dependency single-file binaries).

**Storage**: INI configuration files stored in standard XDG / AppData user directories (`~/.config/f2m/config.ini`, `%APPDATA%\f2m\config.ini`) with working-directory portable override (`./f2m.conf`).

**Testing**: `pytest` running fast offline unit tests, mock scraper fixtures, CLI contract tests, and subprocess PTY interaction tests.

**Target Platform**: Linux (Ubuntu, Debian, Fedora, Arch, Alpine), macOS (Intel & Apple Silicon), Windows 10/11.

**Project Type**: Command-Line Interface (CLI) application with both non-interactive scriptable modes and full-screen interactive TUI menus.

**Performance Goals**: Non-interactive commands (`search`, `resolve`) complete in under 3 seconds on standard connections; interactive menu transitions render without perceptible flicker (<50ms).

**Constraints**: Strict backward compatibility with existing command syntax (`f2m search <q>`, `f2m url <url>`); zero `sudo` or silent remote binary downloads; zero terminal corruption on `Ctrl+C`.

**Scale/Scope**: ~1,400 lines of legacy procedural Python refactored into a cohesive, decoupled package of ~2,500 lines across 7 discrete PR phases.

---

## Constitution Check

*GATE: All 10 mandatory principles from `.specify/memory/constitution.md` evaluated.*

| Principle | Compliance Status | Implementation Strategy in Plan |
|---|---|---|
| **I. Professional CLI UX** | **PASS** | Phase 5 introduces `rich` terminal design system, Unicode visual cell width calculation for Persian, breadcrumbs, and clean signal handling. |
| **II. Reliability Over Aesthetics** | **PASS** | Phase 3 replaces fragile regexes with DOM-based tree parsing, structured retries, and session-transient domain failover. |
| **III. Backward Compatibility** | **PASS** | Phase 4 preserves legacy `f2m search <query>` interactive TTY launching while adding headless flags; Phase 2 preserves legacy `f2m.conf`. |
| **IV. Testability & Multi-Layered Testing** | **PASS** | Phase 1 establishes `pytest` harness and golden fixtures BEFORE any application logic is refactored. |
| **V. Documentation as Implementation** | **PASS** | Every phase includes documentation deliverables; Phase 7 enforces strict bilingual parity (`README.md` and `README.fa.md`). |
| **VI. Incremental Delivery & Branch Discipline** | **PASS** | 7 discrete, single-topic phases. Each phase is implemented on its own branch and submitted as an isolated PR. |
| **VII. PR Ownership & Merge Control** | **PASS** | Explicitly stated: Only the human repository owner may merge PRs. Agents halt after PR creation. |
| **VIII. End-to-End Acceptance Gate** | **PASS** | Every phase specifies both automated test criteria and realistic E2E verification scenarios. |
| **IX. Scope Discipline & Proportional Refactor** | **PASS** | No speculative features or unrelated rewrites; external dependencies strictly minimized to `rich` and `beautifulsoup4`. |
| **X. Honest & Verifiable Claims** | **PASS** | Clear separation between automated test passes and manual PTY verification; documented environment constraints. |

---

## Project Structure

```text
film2media-cli/
├── f2m/                           # Modern Application Package
│   ├── __init__.py                # Package version and metadata
│   ├── __main__.py                # python -m f2m entry point
│   ├── cli/                       # Command-line interface & argument parsing
│   │   ├── __init__.py
│   │   ├── parser.py              # Posix-compliant argument parser
│   │   └── commands/              # Subcommand handlers
│   │       ├── __init__.py
│   │       ├── search.py          # search command (TTY / headless)
│   │       ├── resolve.py         # resolve direct links command
│   │       ├── categories.py      # categories and genres command
│   │       ├── config.py          # config view/edit command
│   │       └── test.py            # connectivity & diagnostics command
│   ├── core/                      # Core business logic & models
│   │   ├── __init__.py
│   │   ├── models.py              # MediaPost, Season, Quality, Episode dataclasses
│   │   ├── config.py              # XDG configuration manager & migration
│   │   └── exceptions.py          # Standardized exception hierarchy
│   ├── net/                       # Network transport & scraping
│   │   ├── __init__.py
│   │   ├── client.py              # HTTP client, retries, mirrors, proxies
│   │   └── scraper.py             # DOM-based HTML & quick-search parser
│   ├── ui/                        # Terminal user interface & rendering
│   │   ├── __init__.py
│   │   ├── theme.py               # Color palette, symbols, NO_COLOR support
│   │   ├── screen.py              # Signal handler & alternate buffer cleanup
│   │   ├── text.py                # Unicode visual cell width & RTL formatting
│   │   └── views/                 # Reusable screens, menus, and spinners
│   └── integrations/              # External process orchestrators
│       ├── __init__.py
│       ├── downloader.py          # aria2c & curl runner without sudo
│       └── player.py              # mpv, vlc, potplayer streaming runner
├── tests/                         # Automated test suite
│   ├── conftest.py                # Shared fixtures and mock servers
│   ├── fixtures/                  # Offline HTML and JSON recordings
│   │   ├── homepage.html
│   │   ├── quick_search.json
│   │   ├── search_results.html
│   │   ├── movie_post.html
│   │   └── series_post.html
│   ├── unit/                      # Fast unit tests
│   │   ├── test_models.py
│   │   ├── test_config.py
│   │   ├── test_scraper.py
│   │   └── test_text.py
│   ├── contract/                  # CLI contract & exit code tests
│   │   └── test_cli.py
│   └── e2e/                       # Realistic workflow tests
│       ├── test_search_headless.py
│       ├── test_signal_handling.py
│       └── test_download_fallback.py
├── f2m.py                         # Backward-compatible root entry wrapper
├── pyproject.toml                 # Package definition & tool config
├── README.md                      # English documentation
└── README.fa.md                   # Persian documentation
```

---

## Phased Delivery Plan (7 Reviewable Pull Requests)

### Phase 1: Test Infrastructure & Fixture Safety Net
- **Objective**: Establish automated testing foundation and record golden fixtures before refactoring application logic.
- **Exact Scope**:
  - Configure `pyproject.toml` with `pytest`, `pytest-cov`, `pytest-mock`, and `ruff`.
  - Create `tests/fixtures/` with offline HTML and JSON samples representing all Film2Media page structures (home, search, movie post, multi-season series post).
  - Write baseline tests against legacy `f2m.py` extraction logic (`parse_listing`, `parse_post`, `clean_title`, `parse_filename`, `parse_selection`) to establish regression benchmarks.
  - Leave `f2m.py` code untouched.
- **Files Affected**: `pyproject.toml`, `tests/conftest.py`, `tests/fixtures/*`, `tests/unit/test_legacy_baseline.py`.
- **Dependencies**: None.
- **Tests Required**: 100% pass on golden parsing fixtures against legacy routines.
- **E2E Scenarios Required**: Run `pytest` and verify tests pass offline without internet connectivity.
- **Documentation Required**: Add testing and developer setup instructions in bilingual READMEs (`README.md` and `README.fa.md`).
- **Migration/Compatibility**: Zero impact on end-user runtime behavior.
- **Acceptance Criteria**: `pytest` passes with 0 failures; complete fixture suite in place.
- **Explicit Non-Goals**: No changes to `f2m.py`, no UI changes, no feature implementations.

---

### Phase 2: Domain Entities & XDG Configuration Engine
- **Objective**: Extract typed data models and replace unsafe binary-directory configuration with standard XDG/AppData configuration management.
- **Exact Scope**:
  - Implement `f2m/core/models.py` (`SearchResult`, `MediaPost`, `Season`, `MediaVersion`, `Quality`, `Episode`, `ConfigurationProfile`).
  - Implement `f2m/core/exceptions.py` (`F2MError`, `F2MNetworkError`, `F2MParseError`, `F2MConfigError`).
  - Implement `f2m/core/config.py`: XDG standard path resolution (`~/.config/f2m/config.ini`), legacy `f2m.conf` auto-migration, working-directory portable override, and environment variable overrides (`F2M_*`).
  - Update `f2m.py` to import and use `f2m.core` while keeping UI and networking intact.
- **Files Affected**: `f2m/core/*`, `f2m.py`, `tests/unit/test_models.py`, `tests/unit/test_config.py`.
- **Dependencies**: Phase 1.
- **Tests Required**: Unit tests for model validation, config priority hierarchy, legacy `f2m.conf` migration, and read-only directory handling.
- **E2E Scenarios Required**: Run `f2m config` in an environment with legacy `f2m.conf` and verify migration to user config folder.
- **Documentation Required**: Document configuration paths and migration behavior in bilingual READMEs.
- **Migration/Compatibility**: Existing `f2m.conf` files automatically preserved and migrated.
- **Acceptance Criteria**: Configuration loads without write errors on system-wide paths; models pass validation.
- **Explicit Non-Goals**: No changes to scraping regexes, CLI arguments, or UI.

---

### Phase 3: Resilient Network Transport & DOM Scraper Engine
- **Objective**: Replace brittle regex scraping with a robust DOM-based parser, and decouple network transport with safe domain failover.
- **Exact Scope**:
  - Implement `f2m/net/scraper.py`: Tree-tolerant parsing using `beautifulsoup4` for search results, category listings, and movie/series post structures.
  - Implement `f2m/net/client.py`: Decoupled HTTP client supporting mirrors, retry with exponential backoff, proxy configuration, and session-transient domain redirect handling (no silent disk writes).
  - Update `f2m.py` to use `f2m.net` modules.
- **Files Affected**: `f2m/net/*`, `f2m.py`, `tests/unit/test_scraper.py`, `tests/unit/test_client.py`.
- **Dependencies**: Phase 2.
- **Tests Required**: Parser tests verifying extraction across all recorded fixtures; mock network tests verifying mirror failover and retry on 429/500/timeout.
- **E2E Scenarios Required**: Execute `f2m search` and post URL loading against a mock HTTP server with redirect and mirror failover.
- **Documentation Required**: Document proxy options and mirror failover mechanisms in bilingual READMEs (`README.md` and `README.fa.md`).
- **Migration/Compatibility**: Upstream markup variations no longer break post parsing.
- **Acceptance Criteria**: 100% of fixture test cases extract titles, qualities, and episodes cleanly; domain redirects do not alter disk files without approval.
- **Explicit Non-Goals**: No CLI argument parser overhaul; no terminal UX changes.

---

### Phase 4: Non-Interactive CLI Engine & POSIX Exit Codes
- **Objective**: Provide headless scriptability and standardized POSIX exit codes while preserving backward-compatible interactive defaults.
- **Exact Scope**:
  - Implement `f2m/cli/parser.py`: Modern argument parsing supporting `--help`, `--version`, `--json`, `--plain`, `--quiet`, `--config`, and subcommands `search`, `resolve`, `categories`, `config`, `test`.
  - TTY auto-detection: If `f2m search <query>` runs in a terminal without non-interactive flags, invoke the interactive selection screen; if output is piped or `--json`/`--plain` is passed, emit data to `stdout` and logs/spinners to `stderr`.
  - Implement POSIX exit codes: `0` (Success), `1` (Runtime/Network error), `2` (CLI argument syntax error), `130` (Interrupted by user `SIGINT`).
  - Implement `resolve` subcommand for direct headless link extraction.
- **Files Affected**: `f2m/cli/*`, `f2m.py`, `tests/contract/test_cli.py`, `tests/e2e/test_search_headless.py`.
- **Dependencies**: Phase 3.
- **Tests Required**: CLI contract tests for all flags and arguments; exit code verification tests.
- **E2E Scenarios Required**: Pipe `f2m search "Matrix" --format json` into `jq` and verify valid JSON with exit code `0`; test `f2m resolve <url> --quality 1080p` outputting direct URLs.
- **Documentation Required**: Complete CLI command reference and examples in bilingual READMEs.
- **Migration/Compatibility**: Existing manual commands (`f2m search "name"`, `f2m url <url>`) continue working identically in interactive terminals.
- **Acceptance Criteria**: Headless execution outputs clean structured data; exit codes strictly comply with POSIX.
- **Explicit Non-Goals**: No overhaul of interactive menus or color palette yet.

---

### Phase 5: Modern Interactive Terminal UX & RTL/Unicode Alignment
- **Objective**: Deliver a polished, flicker-free interactive terminal experience with proper Persian visual cell width alignment and foolproof signal restoration.
- **Exact Scope**:
  - Implement `f2m/ui/theme.py`: Modern, intentional color palette, standard symbols, and `NO_COLOR` support.
  - Implement `f2m/ui/screen.py`: Robust terminal lifecycle manager trapping `SIGINT` and `atexit` to unconditionally restore normal screen buffer and cursor visibility.
  - Implement `f2m/ui/text.py`: Unicode display-cell width calculation using `rich` primitives for Persian and mixed text.
  - Implement `f2m/ui/views/`: Refactored menus, search tables, genre grids with perfectly aligned columns, breadcrumbs, and cancelable spinners.
- **Files Affected**: `f2m/ui/*`, `f2m.py`, `tests/unit/test_text.py`, `tests/e2e/test_signal_handling.py`.
- **Dependencies**: Phase 4.
- **Tests Required**: Unit tests for Persian Unicode cell width calculation and table column alignment; test signal trapping and cleanup.
- **E2E Scenarios Required**: Run interactive session via PTY, trigger `Ctrl+C` at nested screens, and confirm clean exit with visible cursor and intact scrollback.
- **Documentation Required**: Update terminal UX instructions and screenshots in bilingual READMEs (`README.md` and `README.fa.md`).
- **Migration/Compatibility**: Replaces raw ANSI writes; menus retain familiar numbered options and shortcuts (`0`, `b`, `q`, ranges).
- **Acceptance Criteria**: Two-column genre menus and search results remain aligned with Persian strings; 0 terminal corruptions on `Ctrl+C`.
- **Explicit Non-Goals**: Downloader or streaming process execution changes.

---

### Phase 6: Secure Process Orchestration (Downloads & Streaming)
- **Objective**: Eliminate security hazards in external binary execution, provide clean manual guidance, and add health checks.
- **Exact Scope**:
  - Implement `f2m/integrations/downloader.py`: Multi-connection `aria2c` runner and sequential `curl` fallback. Completely remove automatic `sudo` execution and unverified binary downloads. When `aria2c` is missing, display platform-specific install instructions (`sudo apt install aria2`, `winget install aria2`) and immediately offer fallback to `curl` or link export.
  - Implement `f2m/integrations/player.py`: `mpv`, `vlc`, and `potplayer` runner with startup health checks, cross-platform path detection, and immediate error reporting if the player process fails to launch.
- **Files Affected**: `f2m/integrations/*`, `f2m.py`, `tests/unit/test_downloader.py`, `tests/unit/test_player.py`, `tests/e2e/test_download_fallback.py`.
- **Dependencies**: Phase 5.
- **Tests Required**: Mock tests verifying process argument construction, proxy propagation, player error capture, and missing tool handling.
- **E2E Scenarios Required**: Execute download in an environment without `aria2c` and confirm clear instructions and smooth `curl` fallback with ZERO `sudo` attempts.
- **Documentation Required**: Add external dependency installation guide to bilingual READMEs.
- **Migration/Compatibility**: Safe replacement for legacy downloader and player routines.
- **Acceptance Criteria**: Zero unauthorized privilege escalation; player launch failures reported clearly to user.
- **Explicit Non-Goals**: Modifying aria2 protocol internals.

---

### Phase 7: Packaging, Bilingual Documentation Sync & CI Release
- **Objective**: Finalize package distribution, establish automated CI/CD testing, and synchronize English and Persian documentation.
- **Exact Scope**:
  - Finalize `pyproject.toml` package configuration for `pip install .` and `pipx install .`.
  - Set up GitHub Actions CI workflow to run `pytest` and `ruff` on Linux, macOS, and Windows.
  - Set up GitHub Actions release workflow building standalone single-file executables (`f2m-linux-x64` and `f2m-windows-x64.exe`) using PyInstaller.
  - Synchronize `README.md` and `README.fa.md` completely with updated CLI flags, exit codes, config options, troubleshooting, and screenshots.
- **Files Affected**: `.github/workflows/*`, `pyproject.toml`, `README.md`, `README.fa.md`.
- **Dependencies**: Phase 6.
- **Tests Required**: Full multi-platform CI matrix pass; standalone binary build smoke test.
- **E2E Scenarios Required**: Download built standalone executable and verify execution of `f2m --version` and `f2m search --format json`.
- **Documentation Required**: Full bilingual parity between `README.md` and `README.fa.md`.
- **Migration/Compatibility**: Complete parity for both source and binary users.
- **Acceptance Criteria**: All CI checks pass across platforms; documentation is 100% synchronized and verified.
- **Explicit Non-Goals**: No new feature work.

---

## Complexity Tracking

> **Constitution Compliance**: No unjustified complexity introduced. All 10 principles strictly satisfied.

| Area | Solution | Justification under Constitution Principle IX |
|---|---|---|
| Terminal UI & Unicode | `rich` library | Required to fix terminal misalignments with Persian/Arabic text and provide clean cross-platform VT/signal handling without building a fragile custom ANSI engine. |
| HTML Scraping | `beautifulsoup4` | Required to eliminate fragile regex parsing that breaks on minor upstream whitespace/attribute alterations. |
| Single-File Distribution | `pyinstaller` (CI only) | Ensures end users without Python continue to receive zero-dependency single-file binaries. |
