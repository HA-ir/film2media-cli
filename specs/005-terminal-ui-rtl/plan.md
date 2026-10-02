# Implementation Plan: Phase 5 — Terminal UI & RTL Redesign with Rich

**Branch**: `feat/phase-5-terminal-ui-rtl` | **Date**: 2026-10-02 | **Spec**: [specs/005-terminal-ui-rtl/spec.md](spec.md)

---

## Important Governance Notice
> **CRITICAL RULE**: **Only the repository owner may merge a PR.**  
> Automated agents, tools, or bots are strictly prohibited from merging pull requests, enabling auto-merge, or pushing directly to protected/default branches (`master`, `main`). Agents may prepare branches, commits, tests, documentation, and draft PRs, but MUST stop and wait for human review, verification, and explicit merge.

---

## 1. Summary

Phase 5 modernizes the human-interactive terminal presentation layer of `film2media-cli` using the `rich` library. In the legacy implementation, interactive menus and search outputs rely on raw ANSI escape sequences, manual string padding, unbuffered printing, and ad-hoc string formatting, causing severe visual misalignment and bracket inversion when rendering mixed Persian/English titles, years, and ratings.

Phase 5 introduces a structured presentation package in `f2m/ui/` providing:
1. **Rich Console & Theme System** (`f2m/ui/console.py`, `f2m/ui/theme.py`): Managed `Console` abstractions for `stdout` and `stderr` with automatic TTY detection, `NO_COLOR` / `--no-color` support, and width adaptation.
2. **Terminal-Safe BiDi & Escaping** (`f2m/ui/bidi.py`): Directional boundary protection, Unicode character cell width calculation (`‌`), strict LTR protection for URLs and machine tokens, and Rich markup injection defense (`escape()`).
3. **Responsive View Renderers** (`f2m/ui/views.py`): Reusable, testable renderers for the welcome banner, search result tables (with narrow terminal fallback), post metadata panels, season/quality trees, and transient status spinners.
4. **Architectural Isolation & Preservation**:
   - Machine-readable `--json` and `--plain` streams remain 100% pure and untouched.
   - Core domain models (`f2m.core.models`), configuration engine (`f2m.core.config`), scraper (`f2m.core.scraper`), and network client (`f2m.net.client`) remain 100% untouched.

---

## 2. Technical Context

- **Language/Version**: Python 3.8+ (cross-platform Linux, macOS, Windows).
- **Dependencies**: Add `rich>=13.0.0` to runtime `dependencies` in `pyproject.toml`.
- **Target File Locations**:
  - `f2m/ui/__init__.py` (UI package exports)
  - `f2m/ui/models.py` (UI dataclasses & Enums: `UiThemeConfig`, `TableLayoutMode`, `MenuItem`)
  - `f2m/ui/console.py` (Rich `Console` singletons, stream isolation, `NO_COLOR` handling)
  - `f2m/ui/theme.py` (Unified theme and style tokens)
  - `f2m/ui/bidi.py` (BiDi protection, cell width helpers, `escape_text`)
  - `f2m/ui/views.py` (SearchTable, PostHeader, Menu, Banner renderers)
  - `f2m.py` (Updated to consume `f2m/ui/` renderers for interactive screens)
  - `pyproject.toml` (Added `rich>=13.0.0`)
  - `tests/unit/test_ui_rendering.py` (Unit tests for console, escaping, BiDi width, and tables)
  - `tests/unit/test_ui_geometry.py` (Width adaptation and narrow fallback tests)
  - `tests/e2e/test_ui_e2e.py` (E2E subprocess tests asserting clean Rich output and `--json`/`--plain` purity)
- **Error Handling**: Preserves all Phase 4 POSIX exit codes (`0`, `1`, `2`, `3`, `4`, `5`, `6`, `130`).

---

## 3. Constitution Check

*GATE: All 10 mandatory principles from `.specify/memory/constitution.md` evaluated.*

| Principle | Compliance Status | Implementation Strategy |
|---|---|---|
| **I. Professional CLI UX** | **PASS** | Replaces ad-hoc ANSI escapes with modern Rich tables, panels, and status spinners; ensures unbroken borders and clean typography. |
| **II. Reliability Over Aesthetics** | **PASS** | Escapes all upstream text with `escape()` preventing markup crashes; strictly protects URLs, paths, and tokens from BiDi corruption. |
| **III. Backward Compatibility** | **PASS** | Preserves all CLI subcommands, flags, interactive keyboard habits (`1-5`, `all`, `b`/`q`), and Phase 4 exit codes. |
| **IV. Multi-Layered Testing** | **PASS** | Unit tests for UI renderers with in-memory `record=True`, terminal width tests, subprocess E2E tests, and regression tests. |
| **V. Documentation as Implementation** | **PASS** | `README.md` and `README.fa.md` updated in exact bilingual parity to showcase the modernized Rich terminal interface and screenshots. |
| **VI. Incremental Delivery** | **PASS** | Scoped strictly to Phase 5. Exactly one reviewable PR. Zero leakage into Phase 6 (Downloader security) or Phase 7 (Packaging). |
| **VII. PR Ownership & Merge Control** | **PASS** | Enforced: Human repository owner alone merges. Automated agents halt after opening the PR. |
| **VIII. End-to-End Acceptance Gate** | **PASS** | All 72 existing tests pass + new Phase 5 unit and E2E subprocess tests + manual verification. |
| **IX. Scope Discipline** | **PASS** | Minimal, industry-standard dependency (`rich>=13.0.0`); downloader security and packaging strictly excluded. |
| **X. Honest Claims** | **PASS** | Every claim verified via automated subprocess execution, in-memory console recording, and stream isolation assertions. |

---

## 4. Architecture & Module Design

```text
film2media-cli/
├── f2m/
│   ├── core/                      # Untouched (models, config, scraper)
│   ├── net/                       # Untouched (network client)
│   ├── cli/                       # Untouched (parser, runners, formatters)
│   └── ui/                        # NEW: Phase 5 Terminal UI Subsystem
│       ├── __init__.py            # Public exports
│       ├── models.py              # UiThemeConfig, TableLayoutMode, MenuItem
│       ├── console.py             # UiConsole (stdout/stderr Console management)
│       ├── theme.py               # Theme tokens & style definitions
│       ├── bidi.py                # BiDi utilities, cell_len, escape_text
│       └── views.py               # Renderers: Banner, SearchTable, PostHeader, Menu
├── f2m.py                         # Delegates interactive screens to f2m/ui/
├── pyproject.toml                 # Adds rich>=13.0.0
├── tests/
│   ├── unit/
│   │   ├── test_ui_rendering.py   # Unit tests for console, escaping, BiDi, tables
│   │   ├── test_ui_geometry.py    # Responsive width adaptation tests
│   │   └── ...
│   └── e2e/
│       ├── test_ui_e2e.py         # Subprocess E2E and stream purity tests
│       └── ...
├── README.md
└── README.fa.md
```

---

## 5. Implementation Sequence & Detailed Tasks

### Task 1: Dependency Update (`pyproject.toml`)
- Add `rich>=13.0.0` to `dependencies` list in `pyproject.toml`.

### Task 2: UI Models & Console Infrastructure (`f2m/ui/models.py`, `console.py`, `theme.py`)
- Define `UiThemeConfig`, `TableLayoutMode`, and `MenuItem` in `f2m/ui/models.py`.
- Implement `f2m/ui/theme.py` mapping semantic roles to Rich styles.
- Implement `f2m/ui/console.py` providing `get_stdout_console()` and `get_stderr_console()`, detecting TTY, `NO_COLOR`, and width.

### Task 3: BiDi & Text Utilities (`f2m/ui/bidi.py`)
- Implement `escape_text(text: str) -> str` using `rich.markup.escape()`.
- Implement `get_cell_width(text: str) -> int` using `rich.cells.cell_len()`.
- Implement directional boundary helpers guaranteeing that URLs, file paths, and filenames are never bidirectionalized or corrupted.

### Task 4: UI View Components (`f2m/ui/views.py`)
- Implement `render_banner() -> Panel`.
- Implement `render_search_table(results: list[SearchResult], width: int) -> Table | Renderable`.
- Implement `render_post_header(post: MediaPost) -> Panel`.
- Implement `render_menu(title: str, items: list[MenuItem]) -> Table`.
- Implement `render_quality_menu(qualities: list[Quality]) -> Table`.
- Implement `status_spinner(message: str)` context manager wrapping `stderr_console.status()`, inert in non-interactive modes.

### Task 5: Integration in `f2m.py`
- Update `f2m.py` interactive flows (`banner`, `show_post_header`, `choose_quality`, `choose_episodes`, `after_selection`, `categories_flow`, `search_flow`) to use `f2m/ui/` renderers.
- Replace legacy `Spinner` with `status_spinner()` from `f2m/ui/views.py`.
- Preserve 100% of interactive prompt selection logic (`parse_selection`), action triggers (`do_download`, `do_stream`, `copy_links`), and Phase 4 CLI dispatch.

### Task 6: Unit Test Suites
- Create `tests/unit/test_ui_rendering.py`:
  - Test `Console` initialization under color, `NO_COLOR`, and non-TTY modes.
  - Test `escape_text` with bracketed tokens (`[1080p]`, `[Dubbed]`).
  - Test cell width calculation with Persian text and ZWNJ (`‌`).
  - Test `render_search_table` and `render_post_header` with in-memory `Console(record=True)`.
  - Test that URLs and paths are never reversed or altered.
- Create `tests/unit/test_ui_geometry.py`:
  - Test table rendering at 80 columns: verify zero broken borders and clean wrapping.
  - Test table rendering at narrow width (< 65 columns): verify compact fallback.
  - Test rendering at wide width (120 columns).

### Task 7: E2E Subprocess Test Suite (`tests/e2e/test_ui_e2e.py`)
- Test `f2m search "Inception" --json | jq .`: assert zero Rich ANSI codes or markup on `stdout`.
- Test `f2m url <url> --plain`: assert pure direct links on `stdout`.
- Test `f2m search "Inception"` with `NO_COLOR=1`: assert colors stripped cleanly.
- Test `f2m help`, `f2m version`, `f2m config`, and `f2m test`: assert clean formatting in human mode.

### Task 8: Documentation Updates (`README.md` & `README.fa.md`)
- Update `README.md` and `README.fa.md` documenting modernized Rich terminal presentation, Persian text layout, responsive terminal support, and bilingual parity.

---

## 6. Verification Gates

Before concluding Phase 5 and preparing the PR, all 8 verification gates must pass:
1. **Gate 1 — Unit Tests**: `pytest tests/unit/test_ui_rendering.py tests/unit/test_ui_geometry.py` passes 100%.
2. **Gate 2 — Regression Invariant**: `pytest tests/unit/test_legacy_baseline.py tests/unit/test_models.py tests/unit/test_config.py tests/unit/test_config_migration.py tests/unit/test_exceptions.py tests/unit/test_scraper.py tests/unit/test_client.py tests/unit/test_cli_args.py tests/unit/test_formatters.py` passes 100% (all 56 prior unit tests).
3. **Gate 3 — E2E Suites**: `pytest tests/e2e/` passes 100% (including all prior and new UI E2E tests).
4. **Gate 4 — Syntax & Compilation**: `python3 -m py_compile f2m.py f2m/__init__.py f2m/core/*.py f2m/net/*.py f2m/cli/*.py f2m/ui/*.py tests/**/*.py` succeeds with zero errors.
5. **Gate 5 — Static Analysis & Linting**: `ruff check f2m/ tests/` succeeds cleanly.
6. **Gate 6 — Documentation Parity**: `README.md` and `README.fa.md` have identical content updates.
7. **Gate 7 — Manual Verification**:
   - `python3 f2m.py` (verify Rich welcome banner and main menu)
   - `python3 f2m.py search "Inception" --json | jq .` (verify pure JSON)
   - `python3 f2m.py config` (verify Rich configuration table)
   - `python3 f2m.py test` (verify Rich test diagnostics)
8. **Gate 8 — Scope Review**: Confirm zero downloader changes (no `sudo` touch), zero packaging changes, clean git diff on `feat/phase-5-terminal-ui-rtl`, halt and wait for human review and merge.
