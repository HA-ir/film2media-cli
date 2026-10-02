# Implementation Plan: Phase 2 — Domain Entities & XDG Configuration Engine

**Branch**: `feat/phase-2-domain-entities-config` | **Date**: 2026-10-02 | **Spec**: [specs/002-domain-entities-config/spec.md](spec.md)

---

## Important Governance Notice
> **CRITICAL RULE**: **Only the repository owner may merge a PR.**  
> Automated agents, tools, or bots are strictly prohibited from merging pull requests, enabling auto-merge, or pushing directly to protected/default branches (`master`, `main`). Agents may prepare branches, commits, tests, documentation, and draft PRs, but MUST stop and wait for human review, verification, and explicit merge.

---

## 1. Summary

Phase 2 extracts typed, validated **domain models** into `f2m.core.models` and replaces the unsafe binary-directory configuration with a robust, **XDG-compliant configuration engine** in `f2m.core.config`. It resolves critical defect `DEF-003` (preventing permission crashes on system-wide installs in `/usr/local/bin`), establishes a 5-tier configuration precedence hierarchy, introduces non-destructive legacy `f2m.conf` auto-migration, and implements atomic configuration writes.

All user-visible commands (`f2m config`, `f2m config set`, `f2m search`, etc.) and scraping behaviors remain 100% backward-compatible. Application script `f2m.py` integrates with `f2m.core` while keeping UI and scraping routines operational.

---

## 2. Technical Context

- **Language/Version**: Python 3.8+ (cross-platform Linux, macOS, Windows).
- **Dependencies**: Pure standard library (`dataclasses`, `configparser`, `pathlib`, `tempfile`, `os`, `sys`, `urllib.parse`). Zero external runtime dependencies.
- **Development/Testing Dependencies**: `pytest`, `pytest-cov`, `pytest-mock`, `ruff`.
- **Target File Locations**:
  - `f2m/core/models.py` (Domain entities)
  - `f2m/core/config.py` (XDG configuration engine)
  - `f2m/core/exceptions.py` (Standardized domain exceptions)
  - `f2m.py` (Integration call sites)
- **Configuration Storage**:
  - Linux / macOS / POSIX: `$XDG_CONFIG_HOME/f2m/config.ini` (default `~/.config/f2m/config.ini`).
  - Windows: `%APPDATA%\f2m\config.ini`.
  - Local Portable: `./f2m.conf` or `./config.ini` in working directory.

---

## 3. Constitution Check

*GATE: All 10 mandatory principles from `.specify/memory/constitution.md` evaluated.*

| Principle | Compliance Status | Implementation Strategy |
|---|---|---|
| **I. Professional CLI UX** | **PASS** | `f2m config` and `f2m config set` retain identical clean output and meaningful messages; zero visual noise added. |
| **II. Reliability Over Aesthetics** | **PASS** | Fixes `DEF-003` root cause; adds atomic write guarantees and non-destructive legacy migration. |
| **III. Backward Compatibility** | **PASS** | 100% backward compatibility: aliased `Post = MediaPost`, `Version = MediaVersion`, and legacy `f2m.conf` auto-migration. |
| **IV. Testability & Testing** | **PASS** | Comprehensive unit test suite for models and config; E2E tests reproducing read-only and migration scenarios. |
| **V. Documentation as Implementation** | **PASS** | Bilingual documentation (`README.md` and `README.fa.md`) updated with XDG paths and environment variables. |
| **VI. Incremental Delivery** | **PASS** | Strictly scoped to Phase 2. Zero UI redesign, zero scraper overhaul. Exactly one isolated PR. |
| **VII. PR Ownership & Merge Control** | **PASS** | Explicitly enforced: Human repository owner alone merges. Agents stop after PR creation. |
| **VIII. End-to-End Acceptance Gate** | **PASS** | All 8 Phase 1 tests must pass + new Phase 2 unit & E2E tests + manual verification. |
| **IX. Scope Discipline** | **PASS** | Minimal standard-library implementation; no unrequested abstractions. |
| **X. Honest Claims** | **PASS** | Explicit test runner execution and verified assertions. |

---

## 4. Target Architecture & Module Structure

```text
film2media-cli/
├── f2m/
│   ├── __init__.py                # Package version
│   └── core/
│       ├── __init__.py            # Exports models, config, and exceptions
│       ├── exceptions.py          # F2MError, F2MConfigError, F2MNetworkError, F2MParseError
│       ├── models.py              # SearchResult, Card, Episode, Quality, MediaVersion, Season, MediaPost
│       └── config.py              # ConfigManager, XDG resolution, precedence, atomic writes
├── f2m.py                         # Updated to import and use f2m.core while keeping UI/scraping
├── tests/
│   ├── conftest.py                # Fixtures
│   ├── fixtures/                  # Offline HTML/JSON fixtures
│   ├── unit/
│   │   ├── test_legacy_baseline.py# Phase 1 golden tests (regression invariant)
│   │   ├── test_models.py         # Phase 2 domain entity unit tests
│   │   └── test_config.py         # Phase 2 configuration engine unit tests
│   └── e2e/
│       ├── test_offline_suite.py  # Phase 1 offline E2E test
│       └── test_config_e2e.py     # Phase 2 read-only & migration E2E workflows
├── pyproject.toml
├── README.md
└── README.fa.md
```

---

## 5. Implementation Sequence & Detailed Tasks

### Task 1: Standard Exception Hierarchy (`f2m/core/exceptions.py`)
- Define:
  - `F2MError(Exception)`: Base exception.
  - `F2MConfigError(F2MError)`: Configuration validation, path, or syntax errors.
  - `F2MNetworkError(F2MError)`: Network transport errors.
  - `F2MParseError(F2MError)`: HTML/JSON scraping errors.
- Test: Unit test exception instantiation and inheritance.

### Task 2: Typed Domain Entities (`f2m/core/models.py`)
- Implement dataclasses with type annotations:
  - `SearchResult` (with `to_dict`, `from_dict`, `clean_title` integration)
  - `Card`
  - `Episode` (num >= 1 validation, URL unquoting, label generation)
  - `Quality` (label, encoder normalization, episode list)
  - `MediaVersion` (`key` validation for `"dub"` / `"hardsub"`, title, qualities)
  - `Season` (number, title, versions)
  - `MediaPost` (title, year, rating, is_series, seasons, versions, trailer)
  - Aliases: `Post = MediaPost`, `Version = MediaVersion`
- Implement bidirectional serialization `to_dict()` and `from_dict()`.
- Test: Comprehensive unit tests in `tests/unit/test_models.py`.

### Task 3: XDG Configuration Engine (`f2m/core/config.py`)
- Implement `ConfigManager`:
  - `CONFIG_DEFAULTS` and `CONF_COMMENT` preservation.
  - XDG path resolver: `$XDG_CONFIG_HOME/f2m/config.ini`, `%APPDATA%\f2m\config.ini`, or fallback `~/.config/f2m/config.ini`.
  - Resolution precedence: `CLI Overrides > Environment Variables > Working Directory Local Config > User XDG Config > Defaults`.
  - Non-destructive legacy migration: checks `sys.executable` and `__file__` directory for legacy `f2m.conf`, copies if user XDG file is absent.
  - Atomic write: writes to temporary file in target directory, renames via `os.replace`.
  - Read-only fallback: catches permission errors on save, logs diagnostic to `stderr`, and degrades in-memory without crashing.
- Test: Comprehensive unit tests in `tests/unit/test_config.py`.

### Task 4: Integrate `f2m.core` into `f2m.py`
- Replace inline dataclasses in `f2m.py` with imports from `f2m.core.models`.
- Replace legacy `_cfg` global manipulations in `f2m.py` with `f2m.core.config.ConfigManager`.
- Update `load_config()`, `save_config()`, `ensure_config()`, `base_url()`, `set_base_url()`, and `proxies()` to delegate to `f2m.core.config`.
- Keep existing CLI commands (`f2m config`, `f2m config set`) working identically.
- Ensure all 8 Phase 1 regression tests in `test_legacy_baseline.py` pass without modifications.

### Task 5: End-to-End Configuration Verification (`tests/e2e/test_config_e2e.py`)
- Implement E2E Scenario 1: Run `f2m config set` when the script directory is completely read-only (`chmod -R 555`) with isolated `$HOME`. Assert clean exit `0` and verified write to user XDG directory.
- Implement E2E Scenario 2: Legacy migration test. Place temporary legacy `f2m.conf`, run `f2m config`, assert legacy file remains untouched and new XDG file is populated.
- Implement E2E Scenario 3: Environment variable override test. Set `F2M_PROXY` and assert CLI reflects value without writing to disk.

### Task 6: Documentation Synchronization
- Update `README.md` and `README.fa.md` in full parity:
  - Document user-level configuration path (`~/.config/f2m/config.ini` / `%APPDATA%\f2m\config.ini`).
  - Document local `./f2m.conf` portable override.
  - Document `F2M_*` environment variables.
  - Document automatic legacy migration.

---

## 6. Verification Gates

Before preparing the Phase 2 Pull Request, all 7 gates must pass:
1. **Unit Tests**: `pytest tests/unit/test_models.py tests/unit/test_config.py` passes 100%.
2. **Phase 1 Regression Tests**: `pytest tests/unit/test_legacy_baseline.py` passes 100%.
3. **E2E Tests**: `pytest tests/e2e/test_config_e2e.py` and `test_offline_suite.py` pass 100%.
4. **Syntax & Compilation**: `python3 -m py_compile f2m.py f2m/core/*.py` passes with zero errors.
5. **Linting**: `ruff check .` passes with zero violations.
6. **Documentation Parity**: English (`README.md`) and Persian (`README.fa.md`) configuration sections match.
7. **Manual CLI Verification**: Run `python3 f2m.py config` and `python3 f2m.py help` manually and confirm identical clean terminal output.

---

## 7. PR Boundary & Governance Notice

- **Branch**: `feat/phase-2-domain-entities-config`
- **Target**: `master`
- **Merge Authority**: **Only the repository owner may merge this pull request.**
- Automated agents must stop after creating the PR and wait for human testing and merge.
