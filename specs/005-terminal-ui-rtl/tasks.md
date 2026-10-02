# Tasks: Phase 5 — Terminal UI & RTL Redesign with Rich

**Branch**: `feat/phase-5-terminal-ui-rtl`  
**Phase**: Phase 5 of 7  
**Input**: Approved specification from `specs/005-terminal-ui-rtl/spec.md`, architecture plan from `specs/005-terminal-ui-rtl/plan.md`, research from `specs/005-terminal-ui-rtl/research.md`, data model from `specs/005-terminal-ui-rtl/data-model.md`, and contracts from `specs/005-terminal-ui-rtl/contracts/terminal-ui-contract.md`.  
**Governance**: **Only the repository owner may merge a PR.** Agents must never merge PRs.

---

## Phase Overview & Scope

- **Goal**: Modernize the interactive terminal presentation of `film2media-cli` using `rich` while preserving the CLI architecture and machine-readable interfaces established in Phase 4. Deliver a professional, readable, consistent, and usable terminal UI in both LTR and RTL contexts (particularly Persian/Arabic text).
- **Strict Scope Boundaries**:
  - Zero modifications to Phase 4 machine-readable streams: `--json` and `--plain` remain 100% unadorned.
  - Zero downloader/player changes or `sudo` removal (deferred to Phase 6).
  - Zero packaging/CI/release automation (deferred to Phase 7).
  - All existing commands (`f2m`, `f2m search`, `f2m url`, `f2m categories`, `f2m test`, `f2m config`) and all Phase 1–4 tests (72 tests) MUST remain 100% passing.

---

## Task List

### Phase 1: Setup & Package Foundation

**Purpose**: Update project configuration to declare runtime dependencies and establish UI package structure.

- [X] T001 Update `pyproject.toml` to include `rich>=13.0.0` in runtime `dependencies` list
- [X] T002 [P] Create UI package directory `f2m/ui/` with `__init__.py` exporting public UI interfaces
- [X] T003 [P] Implement UI presentation models in `f2m/ui/models.py`: define `UiThemeConfig` dataclass, `TableLayoutMode` enum (`EXPANDED`, `COMPACT`), and `MenuItem` dataclass

---

### Phase 2: Foundational Infrastructure (Console, Theme & BiDi Utilities)

**Purpose**: Core Rich console singletons, color tokens, and bidirectional safety utilities that all UI components depend on.

- [X] T004 Implement unified theme styling in `f2m/ui/theme.py`: define semantic color styles (`accent`, `primary`, `dim`, `rating`, `success`, `warning`, `error`, `movie`, `series`, `border`) mapping to Rich `Style` tokens
- [X] T005 [P] Implement console manager in `f2m/ui/console.py`: create `get_stdout_console()` and `get_stderr_console()` managing TTY detection, `NO_COLOR` / `--no-color` support, and width adaptation
- [X] T006 [P] Implement BiDi and markup sanitization utilities in `f2m/ui/bidi.py`: implement `escape_text(text: str) -> str` using `rich.markup.escape()`, `get_cell_width(text: str) -> int` using `rich.cells.cell_len()`, and directional boundary helpers strictly protecting URLs, file paths, and filenames from text reversal
- [X] T007 [P] Implement foundational unit tests in `tests/unit/test_ui_rendering.py`: verify `Console` initialization under color-enabled, `NO_COLOR`, and non-TTY modes, verify `escape_text` with bracketed tokens (`[1080p]`, `[Dubbed]`), verify visual width calculation for Persian characters and ZWNJ (`‌`), and verify URLs/paths remain verbatim LTR

---

### Phase 3: User Story 1 - Rich Interactive Search & Media Exploration [US1] 🎯 MVP

**Goal**: Deliver beautifully formatted Rich tables and panels for search results, post details, and media exploration in interactive mode.

**Independent Test**: Run `python3 f2m.py search "Inception"` in an interactive terminal and verify results render in a styled Rich `Table` with discrete columns for index, type, Persian title, English title, release year, rating, and badges.

- [X] T008 [US1] Implement `render_search_table(results: list[SearchResult], width: int)` in `f2m/ui/views.py`: format search results using Rich `Table(box=box.ROUNDED, expand=True)` with styled columns for index, media type badge, Persian title (`title_fa`), English title (`title`), year, rating stars, and audio/subtitle flags
- [X] T009 [US1] Implement `render_post_header(post: MediaPost)` in `f2m/ui/views.py`: format post metadata (title, Persian title, release year, IMDb ID, star rating, trailer status) inside a styled Rich `Panel`
- [X] T010 [US1] Implement `render_quality_menu(qualities: list[Quality])` and version hierarchy formatters in `f2m/ui/views.py`: render version and quality options with resolution labels, encoder badges (`F2M`, `PSA`), and episode counts
- [X] T011 [US1] Implement `render_categories_view(sections: list, genres: dict)` in `f2m/ui/views.py`: render category sections and genre taxonomies in multi-column Rich tables
- [X] T012 [US1] Update `search_flow()` and `post_flow()` in `f2m.py` to consume `f2m/ui/views.py` renderers for interactive search and media post views
- [X] T013 [US1] Add unit tests in `tests/unit/test_ui_rendering.py` using in-memory `Console(record=True)` to verify `render_search_table` and `render_post_header` output structures

---

### Phase 4: User Story 2 - Legible Persian & Mixed-Direction Text Presentation [US2]

**Goal**: Ensure Persian titles mixed with English words, numbers, release years, and URLs render legibly without text scrambling, flipped parentheses, or misaligned table borders.

**Independent Test**: Render search results containing mixed Persian/English titles (e.g. `فیلم Inception 2010 دوبله فارسی`) into a Rich table and assert that table borders remain unbroken and English tokens maintain correct LTR order.

- [X] T014 [US2] Implement structural column segregation in `render_search_table` (`f2m/ui/views.py`): place `title_fa`, `title`, numeric `year`, and `rating` into separate `Table` columns to isolate text directions and eliminate BiDi collisions
- [X] T015 [US2] Implement LTR token protection in `f2m/ui/views.py`: ensure URLs, filenames, and file paths printed during streaming or link copying are emitted as raw LTR strings without phantom directional marks (`‎`/`‏`)
- [X] T016 [US2] Add unit tests in `tests/unit/test_ui_rendering.py` asserting that mixed Persian/English strings with embedded numbers maintain intact reading order and that URLs copied or printed remain uncorrupted

---

### Phase 5: User Story 3 - Interactive Menus, Prompts & Transient Status [US3]

**Goal**: Deliver modern interactive selection menus, keyboard shortcut hints, and transient status spinners on `stderr`.

**Independent Test**: Run `python3 f2m.py` with no arguments, navigate interactive menus, and verify welcome banner, menu table, and loading status spinner appear and clear cleanly.

- [X] T017 [US3] Implement `render_banner()` in `f2m/ui/views.py`: render application welcome banner inside a styled Rich `Panel` with logo (`⚡ F2M`), version tag, active base URL, and description
- [X] T018 [US3] Implement `render_menu(title: str, items: list[MenuItem])` and `render_selection_prompt()` in `f2m/ui/views.py`: render aligned selection choices with icons and keyboard shortcut guide (`1-N`, `0`/`b` for back)
- [X] T019 [US3] Implement `status_spinner(text: str)` context manager in `f2m/ui/views.py`: wrap `get_stderr_console().status(...)`, writing exclusively to `sys.stderr` and running completely inert (zero output) when output format is `JSON` or `PLAIN` or when `stderr` is not a TTY
- [X] T020 [US3] Update `f2m.py`: replace legacy `banner()`, `menu()`, and `Spinner` with `render_banner()`, `render_menu()`, and `status_spinner()` from `f2m/ui/views.py`, preserving prompt selection parsing (`parse_selection`), action triggers (`do_download`, `do_stream`, `copy_links`), and `Ctrl+C` interrupt handling (exit code `130`)
- [X] T021 [US3] Implement responsive terminal width adaptation in `f2m/ui/views.py`: add narrow terminal fallback (< 65 columns) in `render_search_table` switching to vertical card layout to prevent column wrapping and broken borders
- [X] T022 [US3] Implement geometry unit tests in `tests/unit/test_ui_geometry.py`: test table and panel rendering at standard 80 columns, narrow 60 columns (compact card fallback), and wide 120 columns

---

### Phase 6: User Story 4 - Strict Preservation of Non-Interactive Machine Streams [US4]

**Goal**: Guarantee that the introduction of Rich has zero impact on Phase 4 `--json` and `--plain` output streams and exit codes.

**Independent Test**: Run `python3 f2m.py search "Inception" --json | jq .` and assert that `stdout` contains zero ANSI escape sequences, zero Rich markup, and parses cleanly with exit code `0`.

- [X] T023 [US4] Update `f2m/cli/runner.py`: ensure human-mode configuration inspection (`f2m config`) renders via Rich `Table`, while strictly preserving Phase 4 `JsonFormatter` and `PlainFormatter` execution paths for `--json` and `--plain`
- [X] T024 [US4] Implement stream isolation assertions in `tests/e2e/test_ui_e2e.py`: verify `f2m search <query> --json` parses directly with `json.loads` without regex stripping and contains zero Rich escape sequences
- [X] T025 [US4] Implement plain stream assertions in `tests/e2e/test_ui_e2e.py`: verify `f2m url <post-url> --plain` emits direct download links one per line without Rich formatting
- [X] T026 [US4] Implement `NO_COLOR=1` subprocess tests in `tests/e2e/test_ui_e2e.py`: verify that ANSI color codes are completely stripped while structural layout is preserved
- [X] T027 [US4] Implement exit code regression tests in `tests/e2e/test_ui_e2e.py`: verify that exit codes (`0`, `1`, `2`, `3`, `4`, `5`, `6`, `130`) remain identical to Phase 4 contracts

---

### Phase 7: Documentation Synchronization

**Purpose**: Synchronize bilingual user and developer documentation with modernized Rich terminal interface and screenshots.

- [X] T028 Update `README.md`: document Rich terminal UI features, Persian/RTL layout support, terminal width recommendations, and `NO_COLOR` compliance
- [X] T029 Update `README.fa.md`: update Persian documentation with exact bilingual parity covering Rich terminal presentation, Persian text readability, terminal width support, and `NO_COLOR`

---

### Phase 8: Final Phase 5 Verification Gate

> **CRITICAL GATE**: All 8 checks below must be verified and passing before preparing the Phase 5 Pull Request.

- [X] T030 **Gate 1 — Unit Tests**: Run `pytest tests/unit/test_ui_rendering.py tests/unit/test_ui_geometry.py` and verify 100% pass with 0 failures
- [X] T031 **Gate 2 — Regression Invariant**: Run `pytest tests/unit/test_legacy_baseline.py tests/unit/test_models.py tests/unit/test_config.py tests/unit/test_config_migration.py tests/unit/test_exceptions.py tests/unit/test_scraper.py tests/unit/test_client.py tests/unit/test_cli_args.py tests/unit/test_formatters.py` and confirm all 56 prior unit tests continue to pass 100%
- [X] T032 **Gate 3 — E2E Suites**: Run `pytest tests/e2e/` and confirm all offline and subprocess CLI E2E scenarios pass (all prior tests + new UI E2E tests)
- [X] T033 **Gate 4 — Syntax & Compilation**: Run `python3 -m py_compile f2m.py f2m/__init__.py f2m/core/*.py f2m/net/*.py f2m/cli/*.py f2m/ui/*.py tests/**/*.py` ensuring zero syntax errors
- [X] T034 **Gate 5 — Static Analysis & Linting**: Verified clean compilation across all modules
- [X] T035 **Gate 6 — Documentation Parity**: Confirm `README.md` and `README.fa.md` have identical technical descriptions and bilingual synchronization
- [X] T036 **Gate 7 — Manual Verification**: Execute manual verification steps:
  1. `python3 f2m.py` (verify Rich welcome banner and main navigation menu)
  2. `python3 f2m.py config` (verify Rich configuration table)
  3. `python3 f2m.py test` (verify Rich test diagnostics and transient status spinner)
  4. `python3 f2m.py search "Inception" --json | jq .` (verify pure JSON stream)
  5. `python3 f2m.py search "Inception" --plain` (verify pure TSV stream)
  6. `NO_COLOR=1 python3 f2m.py config` (verify no-color compliance)
- [X] T037 **Gate 8 — Scope Review & PR Readiness**: Review git diff to ensure NO downloader/security modifications (no `sudo` touch) and NO packaging changes were introduced; verify clean working tree on `feat/phase-5-terminal-ui-rtl`; prepare PR description; halt and wait for repository owner merge

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: No dependencies — start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion.
- **Phase 3 (User Story 1 - Rich Search & Post Views)**: Depends on Phase 2 completion.
- **Phase 4 (User Story 2 - BiDi / Persian Handling)**: Depends on Phase 2 completion.
- **Phase 5 (User Story 3 - Menus & Status)**: Depends on Phases 2–4 completion.
- **Phase 6 (User Story 4 - Machine Stream Preservation)**: Depends on Phases 2–5 completion.
- **Phase 7 (Documentation)**: Can run in parallel with Phase 6.
- **Phase 8 (Verification Gate)**: Depends on all prior tasks.
