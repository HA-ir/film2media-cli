# Phase 3 Quickstart & Validation Guide

**Feature**: Phase 3 — Robust DOM Scraper & Network Reliability  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Automated Test Execution

```bash
# Run DOM scraper unit tests
pytest tests/unit/test_scraper.py -v

# Run HTTP client unit tests (mock retry & mirror failover)
pytest tests/unit/test_client.py -v

# Run Phase 1 & Phase 2 regression suites (must remain 100% passing)
pytest tests/unit/test_legacy_baseline.py tests/unit/test_models.py tests/unit/test_config.py -v

# Run E2E offline and CLI workflows
pytest tests/e2e/test_scraper_e2e.py -v

# Run full test suite
pytest -v
```

---

## 2. Manual Verification Scenarios

### Scenario 1: Quick Search & HTML Fallback
```bash
# Execute search query
python3 f2m.py search "Inception"
```
*Expected*: Clean search display using parsed DOM entities with rating and dub/hardsub badges.

### Scenario 2: Post URL Loading
```bash
# Open post URL directly
python3 f2m.py url "https://www.myf2ms.top/movies/inception-2010/"
```
*Expected*: Post header shows rating and title; versions menu displays available dubbed and hardsub qualities extracted via BeautifulSoup.

### Scenario 3: Connectivity & Diagnostics Command
```bash
# Run test command
python3 f2m.py test
```
*Expected*: Diagnostic output validates reachability and parses categories cleanly via new scraper.
