# Tasks: Phase 2 — Domain Entities & XDG Configuration Engine

**Branch**: `feat/phase-2-domain-entities-config`  
**Phase**: Phase 2 of 7  
**Input**: Approved specification from `specs/002-domain-entities-config/spec.md`, architecture plan from `specs/002-domain-entities-config/plan.md`, research from `specs/002-domain-entities-config/research.md`, data model from `specs/002-domain-entities-config/data-model.md`, and contracts from `specs/002-domain-entities-config/contracts/config-contract.md`.  
**Governance**: **Only the repository owner may merge a PR.** Agents must never merge PRs.

---

## Phase Overview & Scope

- **Goal**: Introduce typed domain entities in `f2m.core.models`, standardized exceptions in `f2m.core.exceptions`, and an XDG-compliant configuration engine in `f2m.core.config` with atomic writes, precedence resolution, and non-destructive legacy migration. Integrate them cleanly into `f2m.py` without modifying CLI commands or scraping logic.
- **Strict Scope Boundaries**:
  - Zero UI/TUI redesign (no `rich` rendering; deferred to Phase 5).
  - Zero scraping rewrite (no `beautifulsoup4`; deferred to Phase 3).
  - Zero CLI argument restructuring or new flags like `--json`/`--plain` (deferred to Phase 4).
  - Zero downloader/player changes or `sudo` removal (deferred to Phase 6).
  - All existing commands (`f2m config`, `f2m config set`, `f2m search`, etc.) and all Phase 1 regression tests MUST remain 100% passing.

---

## Task List

### Phase 1: Setup & Package Foundation

**Purpose**: Establish the package layout and export boundaries for `f2m.core`

- [X] T001 Create package directories `f2m/` and `f2m/core/` per implementation plan
- [X] T002 [P] Implement package entry export in `f2m/__init__.py` exposing package `__version__ = "1.1.0"`
- [X] T003 [P] Implement domain exception hierarchy in `f2m/core/exceptions.py` defining `F2MError(Exception)`, `F2MConfigError(F2MError)`, `F2MNetworkError(F2MError)`, and `F2MParseError(F2MError)`
- [X] T004 [P] Implement unit tests for exception hierarchy instantiation and inheritance in `tests/unit/test_exceptions.py`

---

### Phase 2: Foundational Domain Entities (`f2m.core.models`)

**Purpose**: Core typed domain entities, validation, normalization, and dictionary serialization

- [X] T005 [P] Implement typed dataclass models in `f2m/core/models.py` including `SearchResult`, `Card`, `Episode` (validating `num >= 1`, URL unquoting, default label), `Quality` (encoder normalization), `MediaVersion` (validating `key` in `("dub", "hardsub")`), `Season` (`number >= 1`), `MediaPost` (title cleaning and metadata normalization), and backward-compatible aliases `Post = MediaPost` and `Version = MediaVersion`
- [X] T006 Implement bidirectional serialization methods `to_dict()` and `from_dict()` on all models in `f2m/core/models.py` ensuring unknown keys are safely ignored without raising errors
- [X] T007 Implement unit tests in `tests/unit/test_models.py` covering model creation, validation rules, normalization of titles and filenames, `to_dict()`, `from_dict()`, unknown-key tolerance, and legacy dataclass attribute compatibility

---

### Phase 3: User Story 1 & User Story 3 — XDG Configuration Engine & Precedence (Priority: P1 & P3)

**Goal**: Deliver multi-user XDG configuration resolution, permission safety in read-only directories, atomic writes, and environment variable precedence

**Independent Test**: Execute configuration load and update in an isolated environment where the script directory is read-only; verify writes target `$XDG_CONFIG_HOME/f2m/config.ini` and environment overrides take precedence without mutating disk

#### Unit & Integration Tests for Configuration
- [X] T008 [P] [US1] Implement unit tests in `tests/unit/test_config.py` for XDG path resolution on POSIX (`$XDG_CONFIG_HOME/f2m/config.ini` vs `~/.config/f2m/config.ini`), Windows `%APPDATA%\f2m\config.ini`, custom `F2M_CONFIG` override, and directory creation
- [X] T009 [P] [US3] Implement unit tests in `tests/unit/test_config.py` for the 5-layer precedence hierarchy (`CLI Overrides > Environment Variables > Working Directory Local File > User XDG Config > Defaults`), type conversions, and explicit empty string semantics (`F2M_PROXY=""`)
- [X] T010 [P] [US1] Implement unit tests in `tests/unit/test_config.py` for atomic file writes via temporary file replacement (`os.replace`), read-only filesystem graceful degradation to in-memory config, and malformed INI error recovery

#### Configuration Engine Implementation
- [X] T011 [US1] Implement `ConfigurationProfile` dataclass and `ConfigManager` class in `f2m/core/config.py` supporting standard defaults (`base_url`, `mirrors`, `proxy`, `player`, `download_dir`, `search_sort`, `user_agent`), key validation rules (`player` in `("auto", "mpv", "vlc", "potplayer")`, valid URL schemes), and dictionary conversions
- [X] T012 [US1] Implement platform-specific config path resolution (`resolve_config_path()`) in `f2m/core/config.py` respecting `F2M_CONFIG`, local `./f2m.conf` / `./config.ini`, `$XDG_CONFIG_HOME`, `%APPDATA%`, and `~/.config/f2m/config.ini`
- [X] T013 [US3] Implement layered configuration loading (`load_config()`) in `f2m/core/config.py` applying built-in defaults, user XDG config, local config, environment variables (`F2M_*`), and programmatic CLI overrides
- [X] T014 [US1] Implement atomic configuration persistence (`save_config()`, `set_key()`) in `f2m/core/config.py` using `NamedTemporaryFile` in the target directory and `os.replace`, with graceful error handling and `stderr` warning if the target directory is read-only
- [X] T015 [US1] Export clean public APIs in `f2m/core/__init__.py` exposing models, `ConfigManager`, and exception classes

---

### Phase 4: User Story 2 — Seamless Legacy Configuration Migration (Priority: P2)

**Goal**: Automatically migrate settings from a legacy `f2m.conf` adjacent to the executable into the user XDG configuration path without deleting or modifying the original file

**Independent Test**: Place a custom `f2m.conf` next to `f2m.py`, run config loading with an isolated `$HOME`, and verify settings are imported into `~/.config/f2m/config.ini` while the original file remains intact

- [X] T016 [P] [US2] Implement unit tests in `tests/unit/test_config_migration.py` covering legacy file detection adjacent to script/executable, non-destructive copying, idempotency when XDG config already exists, corrupted legacy file recovery, and write-failure resilience
- [X] T017 [US2] Implement `migrate_legacy_config()` in `f2m/core/config.py` checking recognized legacy paths (`sys.executable` and `__file__` directory for `f2m.conf`), copying settings to the resolved user XDG path if missing, logging an informational migration notice to `stderr`, and strictly preserving the original file untouched

---

### Phase 5: Backward-Compatible `f2m.py` Integration

**Purpose**: Wire `f2m.core` into `f2m.py` while preserving existing CLI commands, output formats, and interactive menu flows

- [X] T018 Update `f2m.py` to import domain dataclasses (`SearchResult`, `Card`, `Episode`, `Quality`, `Version`, `Season`, `Post`) from `f2m.core.models`, removing redundant inline dataclass declarations
- [X] T019 Update `f2m.py` to replace module-level `_cfg` dictionary mutations with `f2m.core.config.ConfigManager`, updating `load_config()`, `save_config()`, `ensure_config()`, `base_url()`, `set_base_url()`, and `proxies()` to delegate cleanly to `ConfigManager` while preserving two-column `f2m config` output formatting
- [X] T020 Update `f2m.py` config command handler (`cli()` and `settings_flow()`) to catch `F2MConfigError` and report clean user-facing error messages via `err(...)` without leaking tracebacks

---

### Phase 6: End-to-End Workflow Verification

**Purpose**: Deterministic, offline End-to-End validation of real CLI configuration workflows

- [X] T021 [P] Implement E2E configuration persistence workflow test in `tests/e2e/test_config_e2e.py` verifying that running `f2m config set download_dir ~/Movies` persists to the user XDG directory and is reloaded in a subsequent CLI execution
- [X] T022 [P] Implement E2E permission safety workflow test in `tests/e2e/test_config_e2e.py` reproducing `DEF-003` by executing `f2m config set` with a completely read-only application directory (`chmod -R 555`) and verifying success (exit code `0`) with config written to isolated user `$HOME`
- [X] T023 [P] Implement E2E legacy migration workflow test in `tests/e2e/test_config_e2e.py` placing a legacy `f2m.conf` next to the script, executing `f2m config`, and verifying automatic migration into the user XDG directory with the original file retained
- [X] T024 [P] Implement E2E environment precedence workflow test in `tests/e2e/test_config_e2e.py` verifying that `F2M_PROXY` and `F2M_BASE_URL` override on-disk configuration during CLI execution without mutating the on-disk file

---

### Phase 7: Documentation Synchronization

**Purpose**: Synchronize bilingual documentation with new configuration behavior

- [X] T025 Update `README.md` documenting standard user configuration paths (`~/.config/f2m/config.ini` / `%APPDATA%\f2m\config.ini`), working directory local override (`./f2m.conf`), `F2M_*` environment variables, and automatic legacy migration
- [X] T026 Update `README.fa.md` with exact Persian translation parity for configuration locations, portable override, environment variables, and automatic migration

---

### Phase 8: Final Phase 2 Verification Gate

> **CRITICAL GATE**: All 8 checks below must be verified and passing before preparing the Phase 2 Pull Request.

- [X] T027 **Gate 1 — Unit & Exception Tests**: Run `pytest tests/unit/test_exceptions.py tests/unit/test_models.py tests/unit/test_config.py tests/unit/test_config_migration.py` and verify all tests pass with 0 failures
- [X] T028 **Gate 2 — Phase 1 Regression Invariant**: Run `pytest tests/unit/test_legacy_baseline.py` and confirm 100% pass on all 7 legacy baseline extraction tests
- [X] T029 **Gate 3 — E2E Offline Suite**: Run `pytest tests/e2e/test_offline_suite.py tests/e2e/test_config_e2e.py` and verify all offline and configuration E2E scenarios pass
- [X] T030 **Gate 4 — Syntax & Compilation**: Run `python3 -m py_compile f2m.py f2m/__init__.py f2m/core/*.py tests/**/*.py` ensuring zero syntax errors
- [X] T031 **Gate 5 — Static Analysis & Linting**: Run `ruff check f2m/ tests/` ensuring clean static analysis
- [X] T032 **Gate 6 — Documentation Parity**: Confirm `README.md` and `README.fa.md` have identical configuration instructions and bilingual synchronization
- [X] T033 **Gate 7 — Manual Verification**: Execute manual verification steps:
  1. `python3 f2m.py config` (verify clean display of default config from user XDG path)
  2. `python3 f2m.py config set proxy http://127.0.0.1:8080` (verify clean save)
  3. `F2M_PROXY="" python3 f2m.py config` (verify empty environment override disables proxy)
  4. `python3 f2m.py help` (verify help message is intact)
- [X] T034 **Gate 8 — Scope Review & PR Readiness**: Review git diff to ensure NO scraping regexes, UI design, downloader logic, or future-phase code were modified; verify working tree is clean on `feat/phase-2-domain-entities-config`; prepare PR description; halt and wait for repository owner merge

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: No dependencies — start immediately.
- **Phase 2 (Models)**: Depends on Phase 1 completion.
- **Phase 3 (Config Engine)**: Depends on Phase 1 & 2 completion.
- **Phase 4 (Legacy Migration)**: Depends on Phase 3 completion.
- **Phase 5 (`f2m.py` Integration)**: Depends on Phases 2, 3, and 4 completion.
- **Phase 6 (E2E Tests)**: Depends on Phase 5 integration.
- **Phase 7 (Docs)**: Can run in parallel with Phase 6.
- **Phase 8 (Verification Gate)**: Depends on all prior tasks.

---

## Notes & Constraints

- `[P]` tasks mark different files with no dependencies on incomplete tasks that can run in parallel.
- All file paths are explicit and absolute within the project tree.
- Every functional requirement (FR-001 through FR-018) in `spec.md` is mapped directly to one or more tasks.
- No work from future Phases 3–7 is included.
