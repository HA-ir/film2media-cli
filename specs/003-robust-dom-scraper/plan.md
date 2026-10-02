# Implementation Plan: Phase 3 — Robust DOM Scraper & Network Reliability

**Branch**: `feat/phase-3-robust-dom-scraper` | **Date**: 2026-10-02 | **Spec**: [specs/003-robust-dom-scraper/spec.md](spec.md)

---

## Important Governance Notice
> **CRITICAL RULE**: **Only the repository owner may merge a PR.**  
> Automated agents, tools, or bots are strictly prohibited from merging pull requests, enabling auto-merge, or pushing directly to protected/default branches (`master`, `main`). Agents may prepare branches, commits, tests, documentation, and draft PRs, but MUST stop and wait for human review, verification, and explicit merge.

---

## 1. Summary

Phase 3 modernizes the core HTML scraping and network transport layers of `film2media-cli`. It replaces fragile regular expressions with a structured, DOM-based scraper in `f2m/core/scraper.py` using `beautifulsoup4` (standard `html.parser`), and encapsulates HTTP requests into a resilient `HttpClient` in `f2m/net/client.py` featuring bounded retries with exponential backoff, ordered mirror failover, proxy support, and session-transient domain redirect handling (preventing silent on-disk configuration mutations).

All existing interactive commands (`f2m search`, `f2m categories`, `f2m url`, `f2m test`, etc.) and all Phase 1/Phase 2 test suites continue to operate with 100% backward compatibility.

---

## 2. Technical Context

- **Language/Version**: Python 3.8+ (cross-platform Linux, macOS, Windows).
- **Dependencies**: `beautifulsoup4>=4.11.0` added to runtime dependencies in `pyproject.toml`. Standard library `html.parser` used for pure-Python portability.
- **Target File Locations**:
  - `f2m/core/scraper.py` (DOM scraper module)
  - `f2m/net/__init__.py` & `f2m/net/client.py` (Network transport module)
  - `f2m.py` (Integration call sites)
  - `pyproject.toml` (Dependency updates)
- **Error Handling**: Converts parsing anomalies into `F2MParseError` and transport failures into `F2MNetworkError`.

---

## 3. Constitution Check

*GATE: All 10 mandatory principles from `.specify/memory/constitution.md` evaluated.*

| Principle | Compliance Status | Implementation Strategy |
|---|---|---|
| **I. Professional CLI UX** | **PASS** | Error messages for network and parsing failures provide clean diagnostics on `stderr` without raw stack traces. |
| **II. Reliability Over Aesthetics** | **PASS** | Replaces brittle regex scraping with DOM-based tree traversal; introduces bounded retries and ordered mirror failover. |
| **III. Backward Compatibility** | **PASS** | Signatures of `parse_post`, `parse_listing`, `parse_categories`, and `fetch` remain identical, returning Phase 2 domain models. |
| **IV. Testability & Testing** | **PASS** | Comprehensive offline fixture tests for scraper; mock network server tests for retries and mirror failover. |
| **V. Documentation as Implementation** | **PASS** | Bilingual documentation (`README.md` and `README.fa.md`) updated with network retry and mirror fallback details. |
| **VI. Incremental Delivery** | **PASS** | Scoped strictly to Phase 3. Exactly one reviewable PR. Zero leakage into future UI or CLI flags. |
| **VII. PR Ownership & Merge Control** | **PASS** | Enforced: Human owner alone merges. Agents stop after PR creation. |
| **VIII. End-to-End Acceptance Gate** | **PASS** | All 28 existing tests pass + new Phase 3 unit and E2E scraper tests + manual verification. |
| **IX. Scope Discipline** | **PASS** | Minimal, focused dependency (`beautifulsoup4`); no speculative frameworks. |
| **X. Honest Claims** | **PASS** | Every claim verified through executable automated tests. |

---

## 4. Target Architecture & Module Structure

```text
film2media-cli/
├── f2m/
│   ├── core/
│   │   ├── models.py              # Domain entities (Phase 2)
│   │   ├── config.py              # XDG config engine (Phase 2)
│   │   ├── exceptions.py          # Domain exceptions (Phase 2)
│   │   └── scraper.py             # DOM-based scraper engine (Phase 3)
│   └── net/
│       ├── __init__.py            # Exports HttpClient
│       └── client.py              # HttpClient, retries, mirrors, proxies (Phase 3)
├── f2m.py                         # Updated to delegate scraping and fetching
├── pyproject.toml                 # Updated with beautifulsoup4 dependency
├── tests/
│   ├── fixtures/                  # Offline HTML/JSON fixtures (expanded for Phase 3)
│   ├── unit/
│   │   ├── test_scraper.py        # DOM scraper unit tests
│   │   └── test_client.py         # HttpClient retry & failover tests
│   └── e2e/
│       └── test_scraper_e2e.py    # E2E search & post parsing CLI workflows
├── README.md
└── README.fa.md
```

---

## 5. Implementation Sequence & Detailed Tasks

### Task 1: Dependency Update (`pyproject.toml`)
- Add `beautifulsoup4>=4.11.0` to `dependencies` list in `pyproject.toml`.

### Task 2: DOM Scraper Implementation (`f2m/core/scraper.py`)
- Implement `clean_title(raw: str) -> str` and `parse_filename(url: str) -> tuple`.
- Implement `parse_categories(html: str)` using BeautifulSoup CSS selectors (`nav a`, `a[href*="/genres/"]`).
- Implement `parse_listing(html: str)` using DOM extraction on `article.entry`, extracting URL, title, poster, year, and pagination max.
- Implement `parse_post(html: str, url: str)` extracting metadata, trailer, seasons (`div.download-season`), audio versions (`div.download-list`), qualities, and episode links into typed `MediaPost`.
- Implement `parse_quick_search(data: list[dict[str, Any]], base_url: str)` mapping JSON items to `SearchResult`.
- Enforce `F2MParseError` on unparseable/corrupted markup.

### Task 3: Resilient HTTP Client (`f2m/net/client.py`)
- Implement `HttpClient` class:
  - Supports configurable timeouts, user-agent, custom headers (`Referer`, `Origin`, `X-Requested-With`), and proxies.
  - Bounded retry loop with exponential backoff on retryable status codes (`429`, `502`, `503`, `504`) and timeouts.
  - Ordered mirror failover across `ConfigurationProfile.mirrors`.
  - In-memory session-transient domain failover on redirect (never mutates on-disk `config.ini`).
  - Converts transport exceptions to `F2MNetworkError`.

### Task 4: Integration into `f2m.py`
- Import scraper functions from `f2m.core.scraper`.
- Instantiate and use `f2m.net.client.HttpClient` in `f2m.py`, replacing the global `_OPENER` and legacy `fetch` / `maybe_update_domain`.
- Update `quick_search()` to use `parse_quick_search` and fall back gracefully to `fetch("/?s=")` on JSON errors.
- Ensure all interactive flows (`search_flow`, `post_flow`, `movie_flow`, `series_flow`, `categories_flow`) operate seamlessly.

### Task 5: Comprehensive Unit & E2E Tests
- `tests/unit/test_scraper.py`: Test DOM parsing of all fixtures, edge cases (reordered attributes, malformed tags, empty pages), and assert `F2MParseError` on corrupt input.
- `tests/unit/test_client.py`: Test retry loop, backoff delays, mirror failover, session redirect handling, and proxy configuration.
- `tests/e2e/test_scraper_e2e.py`: E2E CLI workflows for offline search, post loading, mirror fallback, and clean error reporting.

### Task 6: Documentation Synchronization
- Update `README.md` and `README.fa.md` with scraper architecture notes, network retry policy, and mirror failover details in exact bilingual parity.

---

## 6. Verification Gates

Before opening the Phase 3 PR, all 8 gates must pass:
1. **Scraper Unit Tests**: `pytest tests/unit/test_scraper.py` passes 100%.
2. **Network Client Unit Tests**: `pytest tests/unit/test_client.py` passes 100%.
3. **Regression Invariant**: All 28 existing Phase 1 & 2 tests pass 100%.
4. **E2E Tests**: `pytest tests/e2e/test_scraper_e2e.py` passes 100%.
5. **Syntax & Compilation**: `python3 -m py_compile f2m.py f2m/core/*.py f2m/net/*.py tests/**/*.py` passes with 0 errors.
6. **Linting**: `ruff check .` passes cleanly.
7. **Documentation Parity**: English and Persian documentation match.
8. **Manual Verification**: Run `python3 f2m.py help`, `python3 f2m.py config`, and `python3 f2m.py test` manually.
