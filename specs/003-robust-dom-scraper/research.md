# Phase 3 Research & Technical Decisions

**Feature**: Phase 3 — Robust DOM Scraper & Network Reliability  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. DOM Parser & Library Choice

### Decision
Use `beautifulsoup4` (with standard library `html.parser`):
- Add `beautifulsoup4>=4.11.0` to `dependencies` in `pyproject.toml`.
- Avoid `lxml` or C-extensions to preserve pure-Python portability across platforms and Python 3.8+ environments.

### Rationale
- `f2m.py` legacy regex parsing suffers from attribute order sensitivity (e.g., `<a href="..." class="stretched-link">` fails if `class` comes before `href`).
- BeautifulSoup with `html.parser` handles malformed or fragmented HTML gracefully without throwing parsing errors.
- Does not require binary compiler toolchains, ensuring clean PyInstaller builds and lightweight installation.

---

## 2. Scraping Architecture (`f2m/core/scraper.py`)

### Decision
Implement high-level extraction functions that return Phase 2 typed domain entities:
- `parse_categories(html: str) -> tuple[list[tuple[str, str]], dict[str, list[tuple[str, str]]]]`
- `parse_listing(html: str) -> tuple[list[Card], int]`
- `parse_post(html: str, url: str) -> MediaPost` (with `Post = MediaPost` compatibility)
- `parse_quick_search(data: list[dict[str, Any]] | str, base_url: str) -> list[SearchResult]`

All scraping routines wrap DOM interactions in try/except blocks to convert unexpected structural failures into `F2MParseError` with contextual failure details.

---

## 3. Network Transport Architecture (`f2m/net/client.py`)

### Decision
Implement `HttpClient` class:
- Replaces global mutable `_OPENER` in `f2m.py`.
- Encapsulates `urllib.request.OpenerDirector`, `CookieJar`, and `ProxyHandler`.
- Manages:
  - `session_base_url`: Initialized from `ConfigManager.get("base_url")`. Updated in-memory upon HTTP redirect if host changes to an F2M domain. **Never writes to disk.**
  - `mirrors`: List of fallback mirror URLs from configuration.
  - `fetch(path_or_url, *, referer=None, ajax=False, data=None, allow_mirrors=True)`: Core request loop with bounded retries and exponential backoff.

### Bounded Retry Algorithm
1. Candidate hosts: `[session_base_url] + [m for m in mirrors if m != session_base_url]`
2. For each host:
   - For attempt in `range(max_retries + 1)` (default 2 retries = 3 attempts total):
     - Send request with `timeout=TIMEOUT`.
     - On HTTP `429`, `502`, `503`, `504` or `TimeoutError`:
       - If attempt < max_retries: sleep with backoff (`backoff_factor * (2 ** attempt)`), retry.
       - Else: break to next mirror host.
     - On HTTP `400`, `401`, `403`, `404`:
       - Non-retryable on this host; break to next mirror.
     - On success:
       - Detect HTTP redirect (`resp.geturl()`). If hostname changed and contains `f2m`, update `session_base_url` in memory.
       - Return response body string.
3. If all candidate hosts exhausted: raise `F2MNetworkError` summarizing failed endpoints and root cause.
