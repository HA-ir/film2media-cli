# Tasks: Phase 3 — Robust DOM Scraper & Network Reliability

**Branch**: `feat/phase-3-robust-dom-scraper`  
**Phase**: Phase 3 of 7  
**Input**: Approved specification from `specs/003-robust-dom-scraper/spec.md`, architecture plan from `specs/003-robust-dom-scraper/plan.md`, research from `specs/003-robust-dom-scraper/research.md`, data model from `specs/003-robust-dom-scraper/data-model.md`, and contracts from `specs/003-robust-dom-scraper/contracts/scraper-network-contract.md`.  
**Governance**: **Only the repository owner may merge a PR.** Agents must never merge PRs.

---

## Phase Overview & Scope

- **Goal**: Replace legacy regex-based HTML scraping with a resilient DOM scraping module in `f2m.core.scraper` using `beautifulsoup4`, and introduce a robust HTTP client in `f2m.net.client` featuring bounded retries with exponential backoff, ordered mirror failover, proxy support, and session-transient domain redirect handling.
- **Strict Scope Boundaries**:
  - Zero UI/TUI redesign (no `rich` rendering; deferred to Phase 5).
  - Zero CLI argument restructuring or new flags like `--json`/`--plain` (deferred to Phase 4).
  - Zero downloader/player changes or `sudo` removal (deferred to Phase 6).
  - All existing commands (`f2m search`, `f2m url`, `f2m categories`, `f2m test`, `f2m config`) and all Phase 1/Phase 2 tests MUST remain 100% passing.

---

## Task List

### Phase 1: Setup & Dependency Configuration

**Purpose**: Update project configuration to declare runtime dependencies

- [X] T001 Update `pyproject.toml` to include `beautifulsoup4>=4.11.0` in runtime `dependencies` list
- [X] T002 [P] Create network package directory `f2m/net/` with `__init__.py` exporting `HttpClient`
- [X] T003 [P] Add malformed and edge-case HTML fixtures in `tests/fixtures/malformed_post.html` and `tests/fixtures/edge_cases_post.html`

---

### Phase 2: DOM Scraper Implementation (`f2m.core.scraper`)

**Purpose**: Robust HTML/DOM parsing producing typed Phase 2 domain entities

- [X] T004 [P] Implement title cleaning and token parsing utilities (`clean_title`, `parse_filename`, `_version_key`, `ygroup`) in `f2m/core/scraper.py`
- [X] T005 [P] Implement `parse_categories(html: str)` in `f2m/core/scraper.py` using BeautifulSoup selectors on navigation and genre anchors
- [X] T006 Implement `parse_listing(html: str)` in `f2m/core/scraper.py` using BeautifulSoup to extract `article.entry` elements into `Card` models and extract max pagination page
- [X] T007 Implement `parse_quick_search(data: list[dict[str, Any]], base_url: str)` in `f2m/core/scraper.py` mapping JSON payloads to typed `SearchResult` entities with unescaped Persian titles
- [X] T008 Implement `parse_post(html: str, url: str)` in `f2m/core/scraper.py` using BeautifulSoup DOM selectors to extract metadata, trailer, and nested `Season` / `MediaVersion` / `Quality` / `Episode` download structures for both movie and multi-season series posts, raising `F2MParseError` on unparseable HTML
- [X] T009 Export scraper public APIs in `f2m/core/__init__.py`
- [X] T010 Implement comprehensive unit tests in `tests/unit/test_scraper.py` covering category extraction, card listing, movie post parsing, series post parsing, quick-search mapping, reordered HTML attributes tolerance, empty markup handling, and `F2MParseError` assertions

---

### Phase 3: Resilient Network Client (`f2m.net.client`)

**Purpose**: Decoupled HTTP transport with bounded retries, backoff, mirror failover, and session-transient redirects

- [X] T011 [P] Implement `HttpClient` class in `f2m/net/client.py` encapsulating `urllib.request.OpenerDirector`, `CookieJar`, `ProxyHandler`, custom headers (`User-Agent`, `Referer`, `Origin`), and in-memory `session_base_url` tracking
- [X] T012 Implement bounded retry logic with exponential backoff on retryable HTTP error codes (`429`, `502`, `503`, `504`) and timeouts in `f2m/net/client.py`
- [X] T013 Implement ordered mirror failover across `ConfigurationProfile.mirrors` in `f2m/net/client.py` with URL path and query preservation
- [X] T014 Implement session-transient domain redirect handling in `f2m/net/client.py` updating in-memory `session_base_url` without mutating on-disk `config.ini`
- [X] T015 Implement transport exception normalization in `f2m/net/client.py` converting low-level network errors into `F2MNetworkError` with informative diagnostics
- [X] T016 Implement unit tests in `tests/unit/test_client.py` using mocked HTTP handlers to test bounded retries, backoff intervals, mirror failover order, proxy routing, session-transient redirects, and `F2MNetworkError` wrapping

---

### Phase 4: Integration into `f2m.py`

**Purpose**: Wire the new scraper and network client into `f2m.py` while preserving existing interactive CLI behavior

- [X] T017 Update `f2m.py` to import scraper functions (`parse_categories`, `parse_listing`, `parse_post`, `clean_title`, `parse_filename`) from `f2m.core.scraper`, deprecating the regex `PATTERNS` class
- [X] T018 Update `f2m.py` to initialize `f2m.net.client.HttpClient` from active configuration, replacing global `_OPENER`, `fetch`, and `maybe_update_domain`
- [X] T019 Update `quick_search()` in `f2m.py` to use `HttpClient` and `parse_quick_search()`, falling back to HTML search on JSON failure
- [X] T020 Update `f2m/__init__.py` to re-export new core scraper and client functions for complete backward compatibility

---

### Phase 5: End-to-End Workflow Verification

**Purpose**: Deterministic, offline End-to-End validation of scraper and network workflows

- [X] T021 [P] Implement E2E search workflow test in `tests/e2e/test_scraper_e2e.py` verifying quick-search JSON parsing and HTML fallback via subprocess CLI execution
- [X] T022 [P] Implement E2E post parsing workflow test in `tests/e2e/test_scraper_e2e.py` verifying movie and series post parsing from offline fixtures
- [X] T023 [P] Implement E2E mirror failover and retry workflow test in `tests/e2e/test_scraper_e2e.py` verifying that primary domain failure triggers clean mirror failover without on-disk configuration mutation
- [X] T024 [P] Implement E2E malformed HTML error reporting test in `tests/e2e/test_scraper_e2e.py` asserting clean user diagnostic message and error exit code on corrupted markup

---

### Phase 6: Documentation Synchronization

**Purpose**: Synchronize bilingual documentation with scraper and network enhancements

- [X] T025 Update `README.md` documenting DOM scraper architecture, network retry policies, timeout defaults, mirror failover, and proxy handling
- [X] T026 Update `README.fa.md` with exact Persian translation parity for scraper architecture, network retries, timeouts, mirror failover, and proxy handling

---

### Phase 7: Final Phase 3 Verification Gate

> **CRITICAL GATE**: All 8 checks below must be verified and passing before preparing the Phase 3 Pull Request.

- [X] T027 **Gate 1 — Unit Tests**: Run `pytest tests/unit/test_scraper.py tests/unit/test_client.py` and verify 100% pass with 0 failures
- [X] T028 **Gate 2 — Regression Invariant**: Run `pytest tests/unit/test_legacy_baseline.py tests/unit/test_models.py tests/unit/test_config.py tests/unit/test_config_migration.py tests/unit/test_exceptions.py` and confirm all 23 prior unit tests continue to pass 100%
- [X] T029 **Gate 3 — E2E Suites**: Run `pytest tests/e2e/` and confirm all offline and workflow E2E scenarios pass
- [X] T030 **Gate 4 — Syntax & Compilation**: Run `python3 -m py_compile f2m.py f2m/__init__.py f2m/core/*.py f2m/net/*.py tests/**/*.py` ensuring zero syntax errors
- [X] T031 **Gate 5 — Static Analysis & Linting**: Run `ruff check f2m/ tests/` ensuring clean static analysis
- [X] T032 **Gate 6 — Documentation Parity**: Confirm `README.md` and `README.fa.md` have identical technical descriptions and bilingual synchronization
- [X] T033 **Gate 7 — Manual Verification**: Execute manual verification steps:
  1. `python3 f2m.py help` (verify help message is intact)
  2. `python3 f2m.py config` (verify config display is intact)
  3. `python3 f2m.py test` (verify connectivity test routine runs)
- [X] T034 **Gate 8 — Scope Review & PR Readiness**: Review git diff to ensure NO UI design, new CLI flags (`--json`), or downloader changes were introduced; verify clean working tree on `feat/phase-3-robust-dom-scraper`; prepare PR description; halt and wait for repository owner merge

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup & Deps)**: No dependencies — start immediately.
- **Phase 2 (DOM Scraper)**: Depends on Phase 1 completion.
- **Phase 3 (HTTP Client)**: Depends on Phase 1 completion.
- **Phase 4 (`f2m.py` Integration)**: Depends on Phases 2 and 3 completion.
- **Phase 5 (E2E Tests)**: Depends on Phase 4 integration.
- **Phase 6 (Docs)**: Can run in parallel with Phase 5.
- **Phase 7 (Verification Gate)**: Depends on all prior tasks.
