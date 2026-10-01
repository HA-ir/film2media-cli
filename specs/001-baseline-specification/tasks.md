# Tasks: Phase 1 — Test Infrastructure & Fixture Safety Net

**Branch**: `001-baseline-specification`  
**Phase**: Phase 1 of 7  
**Input**: Approved specification from `specs/001-baseline-specification/spec.md` and plan from `specs/001-baseline-specification/plan.md`  
**Governance**: **Only the repository owner may merge a PR.** Agents must never merge PRs.

---

## Phase Overview & Scope

- **Goal**: Establish an automated test harness (`pytest`) and an offline HTML/JSON fixture suite capturing real Film2Media markup, and implement golden regression tests against legacy routines in `f2m.py` before any application code is touched.
- **Strict Scope Boundaries**:
  - Additive only: `pyproject.toml`, `tests/*`, and developer documentation in `README.md` and `README.fa.md`.
  - Application code (`f2m.py`) MUST NOT be refactored or modified in this phase.
  - No UI, network, or downloader changes.

---

## Task List

### 1. Setup & Environment Configuration

- [X] T001 Initialize project configuration and developer dependencies (`pytest>=7.0`, `pytest-cov`, `pytest-mock`, `ruff`) in `pyproject.toml`
- [X] T002 [P] Create test suite directory layout (`tests/fixtures/`, `tests/unit/`, `tests/e2e/`)
- [X] T003 [P] Implement shared pytest fixtures and offline HTML/JSON loader helpers in `tests/conftest.py`

---

### 2. Offline Fixture Suite Creation

- [X] T004 [P] Create realistic homepage HTML fixture in `tests/fixtures/homepage.html` containing navigation links (`/movies/`, `/series/`, `/250tmdb/`) and genre links (`/genres/<slug>/?type=movie|series`)
- [X] T005 [P] Create quick-search JSON response fixture in `tests/fixtures/quick_search.json` containing movie and series search results with Persian titles, ratings, and dub/hardsub flags
- [X] T006 [P] Create HTML search/listing fixture in `tests/fixtures/search_results.html` containing `<article class="entry">` cards, titles, years, and pagination links
- [X] T007 [P] Create single-movie post HTML fixture in `tests/fixtures/movie_post.html` containing OG metadata, IMDb rating, and version download lists (`1080p`, `720p`, dub, hardsub)
- [X] T008 [P] Create television series post HTML fixture in `tests/fixtures/series_post.html` containing `<div class="download-season">` season blocks, version lists, qualities, and episode links

---

### 3. Regression & Unit Test Implementation

- [X] T009 [P] Implement unit tests for title sanitization and Persian prefix stripping (`clean_title`) in `tests/unit/test_legacy_baseline.py`
- [X] T010 [P] Implement unit tests for filename and season/episode token parsing (`parse_filename`, `SE_TOKEN`, `DUB_TOKEN`, `SUB_TOKEN`) in `tests/unit/test_legacy_baseline.py`
- [X] T011 [P] Implement unit tests for interactive selection parser (`parse_selection`), covering single numbers, comma lists, ranges (`1-4`), wildcards (`all`, `*`), and Persian commas (`،`) in `tests/unit/test_legacy_baseline.py`
- [X] T012 Implement regression unit tests for category and genre extraction (`parse_categories`) using `tests/fixtures/homepage.html` in `tests/unit/test_legacy_baseline.py`
- [X] T013 Implement regression unit tests for card listing and pagination extraction (`parse_listing`) using `tests/fixtures/search_results.html` in `tests/unit/test_legacy_baseline.py`
- [X] T014 Implement regression unit tests for movie and series post parsing (`parse_post`) using `tests/fixtures/movie_post.html` and `tests/fixtures/series_post.html` in `tests/unit/test_legacy_baseline.py`

---

### 4. End-to-End & Offline Verification

- [X] T015 Implement offline test runner verification scenario in `tests/e2e/test_offline_suite.py` asserting that the entire test suite executes and passes with 100% offline isolation (no external network socket connections allowed)

---

### 5. Documentation Synchronization

- [X] T016 Update developer and testing instructions in `README.md` documenting virtual environment setup (`pip install -e ".[dev]"`) and test commands (`pytest`)
- [X] T017 Update developer and testing instructions in `README.fa.md` with exact Persian translation parity for virtual environment setup and test commands

---

### 6. Final Phase 1 Verification Gate

> **CRITICAL GATE**: All 7 checks below must be verified and passing before preparing the Phase 1 Pull Request.

- [X] T018 **Gate 1 — Unit & Integration Tests**: Run `pytest tests/unit/` and verify all baseline tests pass with 0 failures
- [X] T019 **Gate 2 — E2E Offline Verification**: Run `pytest tests/e2e/` and confirm offline test suite passes
- [X] T020 **Gate 3 — Regression Safety**: Verify all golden test assertions in `tests/unit/test_legacy_baseline.py` match legacy `f2m.py` extraction behavior without any modifications to `f2m.py`
- [X] T021 **Gate 4 — Static Analysis & Linting**: Run `ruff check tests/` and `python3 -m py_compile f2m.py` ensuring zero lint or syntax violations
- [X] T022 **Gate 5 — Documentation Parity**: Confirm `README.md` and `README.fa.md` contain identical instructions for test execution
- [X] T023 **Gate 6 — Manual Verification**: Execute manual verification steps:
  1. `python3 -m venv .venv && source .venv/bin/activate`
  2. `pip install -e ".[dev]"`
  3. `pytest -v`
  4. Verify existing script continues running: `python3 f2m.py help`
- [X] T024 **Gate 7 — PR Readiness**: Verify clean git working tree, review git diff to ensure NO application code was modified, prepare descriptive PR body, and halt for human repository owner review and merge
