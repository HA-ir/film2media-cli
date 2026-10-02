# Feature Specification: Phase 3 — Robust DOM Scraper & Network Reliability

**Feature Branch**: `feat/phase-3-robust-dom-scraper`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "Phase 3 — Robust DOM Scraper & Network Reliability: Replace fragile regex parsing with beautifulsoup4 DOM scraper and introduce resilient network client with mirror fallback, retries, and clean exceptions."

---

## 1. Executive Summary & Purpose

Phase 1 established automated test infrastructure and golden fixtures. Phase 2 delivered typed domain models and an XDG-compliant configuration engine.

Phase 3 addresses the most vulnerable operational component in `film2media-cli`: **fragile HTML scraping and ad-hoc HTTP transport**. Currently, `f2m.py` parses upstream markup exclusively via brittle compiled regular expressions (`PATTERNS`), causing silent extraction failures or empty menus whenever the website introduces minor whitespace, attribute reordering, or wrapper tags. Concurrently, network requests are performed by an unmanaged global `urllib.request.OpenerDirector` that silently mutates configuration files upon HTTP redirects (`maybe_update_domain`), lacks structured retry with backoff, and provides no graceful fallback for malformed responses.

Phase 3 introduces a dedicated, resilient DOM scraping package (`f2m/core/scraper.py`) powered by `beautifulsoup4` (using standard library `html.parser`), alongside a resilient HTTP client (`f2m/net/client.py`) supporting ordered mirror fallback, bounded retries, proxy support, and session-transient domain failover.

**User-facing CLI behavior, terminal menus, and downloader/streaming routines remain completely intact in this phase.**

---

## Clarifications

### Session 2026-10-02

#### 1. DOM Scraper Architecture & Selector Contracts
- **Selector Strategy & Resilience**:
  - Prefer semantic CSS selectors: `article.entry`, `nav a`, `a.stretched-link`, `h2.entry-title`, `.download-season`, `.download-list`, `li`.
  - Tolerate attribute reordering and whitespace variations natively through BeautifulSoup DOM methods (`soup.find_all`, `soup.select`).
  - Use regexes only where text-level token extraction within DOM nodes is genuinely necessary (e.g. season/episode tokens in filenames `S\d+E\d+`, IMDb ID `tt\d+`, year `-20\d\d` in URL slug).
- **Required vs Optional Elements**:
  - *Post Page*: Title is required (falls back to URL slug if missing); IMDb ID, rating, year, and trailer are optional (default to empty string). If no seasons or versions are found, `MediaPost` is returned with empty lists, allowing UI callers to display `"no download links found on this page"` rather than crashing.
  - *Episode extraction*: If an anchor URL contains media extension (`.mkv`, `.mp4`, `.avi`, `.mka`), it is extracted. If episode number cannot be derived from label or filename token, fallback to sequential 1-based index.
- **Movie vs Series Detection**:
  - Classified as `series` if URL contains `/series/` OR page contains any `.download-season` block; otherwise classified as `movie`.
- **Parsing Failure Invariants**:
  - Scraper never leaks raw `AttributeError`, `IndexError`, or `KeyError`.
  - Malformed HTML or unparseable markup raises `F2MParseError` with contextual diagnostics.

#### 2. Network Client Behavior, Retries & Mirror Failover
- **Timeout Defaults**: `TIMEOUT = 25` seconds per attempt (configurable via `HttpClient`).
- **Retry Policy**:
  - Max retries: 2 retries per host (total 3 attempts on primary before falling back to mirrors).
  - Backoff: Exponential backoff with delay factor (e.g. 0.5s for attempt 1, 1.0s for attempt 2).
  - Retryable conditions: Socket/connect timeout, HTTP `429` (Rate Limited), `502` (Bad Gateway), `503` (Service Unavailable), `504` (Gateway Timeout).
  - Non-retryable conditions: HTTP `400`, `401`, `403`, `404` (fail immediately or advance to next mirror if 404 on obsolete mirror path).
- **Mirror Failover Order**:
  - Primary `base_url` tried first with bounded retries.
  - On failure, try each mirror in `ConfigurationProfile.mirrors` sequentially in configured order.
  - If a candidate URL starts with `http://` or `https://` matching primary host, mirror candidate substitutes host while preserving query and path.
- **Session-Transient Domain Failover**:
  - If a request redirects to a new domain (matching `f2m` in netloc), the client updates an in-memory session variable `current_base_url`.
  - **The on-disk `config.ini` is NEVER modified during a fetch or redirect.**
- **Transport Exception Normalization**:
  - All standard `urllib`, `http.client`, `socket`, and `ssl` exceptions are caught and wrapped into `F2MNetworkError` with the root cause preserved in error string.

#### 3. Backward Compatibility
- Signatures and return types of `parse_categories`, `parse_listing`, `parse_post`, `quick_search`, and `fetch` remain 100% backward-compatible.
- `f2m.py` interactive flows (`movie_flow`, `series_flow`, `listing_menu`, `categories_flow`, `search_flow`) continue operating with zero user-visible disruption.
- All 28 existing Phase 1 and Phase 2 tests continue passing.

---

## 2. User Scenarios & Testing *(mandatory)*

### User Story 1 - Resilient Media & Post Extraction (Priority: P1)
As an interactive or headless user, I want the client to extract movie and series download links, qualities, and seasons reliably even when upstream page formatting changes slightly, so that I never encounter empty version lists or unhandled extraction crashes.

**Why this priority**: Core functional capability of the tool. Prevents `DEF-004` (silent breakage caused by attribute or whitespace variations).

**Independent Test**: Load recorded HTML fixtures with reordered attributes, extra classes, or varying whitespace into the scraper. Verify that 100% of versions, qualities, and episodes are extracted as typed `MediaPost`, `Season`, and `Quality` domain entities.

**Acceptance Scenarios**:
1. **Given** a movie page with standard or reordered HTML attributes, **When** scraping the post, **Then** all versions (Dub vs Hardsub), quality labels (`1080p`, `720p`), encoders (`F2M`, `PSA`), direct links, and trailer URLs are extracted into a valid `MediaPost`.
2. **Given** a multi-season series page with accordion season blocks, **When** scraping the post, **Then** all seasons, version lists, and episode download anchors are correctly mapped into structured `Season` and `Episode` objects.
3. **Given** a malformed HTML page missing expected download containers, **When** parsing fails, **Then** the scraper raises a clear `F2MParseError` with diagnostic context rather than leaking an `AttributeError` or `IndexError`.

---

### User Story 2 - Ordered Mirror Failover & Bounded Retries (Priority: P2)
As a user whose ISP or DNS intermittently filters or throttles the primary Film2Media domain, I want the client to automatically retry transient network errors and systematically fall back across configured mirrors, so that searches and downloads succeed without manual configuration edits.

**Why this priority**: Essential for regional network resilience where media domains experience frequent disruption.

**Independent Test**: Simulate primary domain timeout/429/500 errors against mock HTTP endpoints. Verify that the client attempts up to 2 retries with backoff on the primary domain before cleanly falling back to the secondary mirror.

**Acceptance Scenarios**:
1. **Given** the primary `base_url` returns a retryable status code (`429`, `502`, `503`, `504`) or times out, **When** fetching a page, **Then** the client retries with exponential backoff (e.g., 0.5s, 1.0s) up to a bounded maximum (default 2 retries per host).
2. **Given** the primary `base_url` is completely unreachable (connection refused, DNS failure, persistent timeout), **When** fetching content, **Then** the client systematically tries configured mirrors in order and returns the successful response.
3. **Given** all mirrors fail, **When** the request cannot be fulfilled, **Then** the client raises a clean `F2MNetworkError` summarizing the failed hosts and diagnostics, without exposing raw library tracebacks.

---

### User Story 3 - Session-Transient Domain Redirection (Priority: P3)
As a user accessing a domain that redirects to a newer portal domain, I want the client to use the new domain transiently for my current command without silently corrupting my on-disk configuration file.

**Why this priority**: Fixes critical security/reliability defect `DEF-005` (unverified permanent configuration writes during redirects).

**Independent Test**: Mock an HTTP 301/302 redirect from `https://www.myf2ms.top` to `https://www.newf2m.top`. Verify that subsequent requests in the session use the redirected domain while `config.ini` on disk remains completely unchanged.

**Acceptance Scenarios**:
1. **Given** an HTTP redirect to a new domain occurs, **When** handling the response, **Then** the client stores the new domain in memory for the active session.
2. **Given** the active session terminates, **When** checking the on-disk `config.ini`, **Then** the file remains unmodified unless the user explicitly executes `f2m config set base_url <url>`.

---

### User Story 4 - Resilient Search & Pagination Extraction (Priority: P4)
As a user searching for media or browsing genres, I want search results and category listings to be extracted reliably into typed `SearchResult` and `Card` objects, so that results display cleanly in menus or output.

**Why this priority**: Required for core search and category browsing workflows.

**Independent Test**: Parse quick-search JSON and HTML listing pages with varying card counts, validating that all metadata, badges, and pagination page numbers are extracted accurately.

**Acceptance Scenarios**:
1. **Given** a quick-search JSON response, **When** parsed, **Then** results are mapped into typed `SearchResult` entities with unescaped Persian titles, clean years, ratings, and dub/hardsub booleans.
2. **Given** an HTML search or category listing page with pagination, **When** parsed, **Then** cards are extracted as `Card` entities and the maximum page number is correctly identified.

---

### Edge Cases
- **Completely Empty Response**: If the server returns HTTP 200 with an empty body, the scraper MUST raise `F2MParseError("Received empty response from server")`.
- **Corrupted Quick-Search JSON**: If `/quick-search` returns malformed JSON or HTML error pages, the client MUST gracefully fall back to HTML search (`/?s=<query>`) with a diagnostic warning on `stderr`.
- **Malformed Season / Episode Labels**: If an episode link contains no episode number in text or filename, the scraper MUST assign a safe sequential index (`1, 2, ...`) without crashing.
- **Proxy Connection Errors**: If a configured proxy is unreachable (`ProxyError` / `ConnectionRefused`), the network client MUST raise `F2MNetworkError` identifying the proxy failure.

---

## 3. Requirements *(mandatory)*

### Functional Requirements

#### DOM Scraping Engine (`f2m/core/scraper.py`)
- **FR-001**: System MUST parse HTML pages using `beautifulsoup4` with Python's standard `html.parser` engine.
- **FR-002**: System MUST extract category navigation links (`/movies/`, `/series/`, etc.) and genre links (`/genres/<slug>/?type=movie|series`) into structured tuples `(title, url)` via DOM element selection.
- **FR-003**: System MUST extract search and category listing cards (`<article class="entry">`) into typed `Card` domain entities, extracting URL from `.stretched-link`, title from `.entry-title`, poster from `img[src]`, and release year from URL slug heuristics.
- **FR-004**: System MUST extract pagination bounds from `.page-numbers` elements, identifying current and maximum page numbers.
- **FR-005**: System MUST parse `/quick-search` JSON payloads into a list of typed `SearchResult` entities, unescaping Persian titles and normalizing media types.
- **FR-006**: System MUST parse single-movie post pages into typed `MediaPost` entities, extracting OpenGraph titles, IMDb IDs (`tt\d+`), IMDb ratings, trailer URLs, and nested `MediaVersion` / `Quality` / `Episode` download structures.
- **FR-007**: System MUST parse television series post pages into typed `MediaPost` entities, extracting accordion season containers (`.download-season`), audio versions (`.download-list.dub`, `.download-list.sub`), qualities, and episode links (`Episode(num, url, filename)`).
- **FR-008**: System MUST catch unhandled DOM extraction failures (e.g. malformed tag hierarchies) and raise structured `F2MParseError` with contextual messages, strictly avoiding raw `AttributeError`, `KeyError`, or `IndexError` leaks.

#### Network Transport & Client (`f2m/net/client.py`)
- **FR-009**: System MUST provide a decoupled `HttpClient` class handling requests, timeouts, custom headers (`User-Agent`, `Referer`, `Origin`), and proxies.
- **FR-010**: System MUST support HTTP, HTTPS, and SOCKS5 proxies as configured in `ConfigurationProfile.proxy`.
- **FR-011**: System MUST implement bounded retry logic for transient failures (timeouts, `429`, `502`, `503`, `504`) with configurable retry count (default: 2 retries) and exponential backoff (e.g. 0.5s, 1.0s).
- **FR-012**: System MUST implement ordered mirror failover: if a request to the primary `base_url` fails after retries, the client MUST attempt the same path against each configured mirror in `ConfigurationProfile.mirrors`.
- **FR-013**: System MUST treat domain redirects and mirror failovers as session-transient; on-disk configuration (`config.ini`) MUST NOT be modified automatically during redirects.
- **FR-014**: System MUST convert low-level transport exceptions (`URLError`, `HTTPError`, `TimeoutError`, `OSError`) into `F2MNetworkError` with informative diagnostics on `stderr`.

#### Integration & Backward Compatibility
- **FR-015**: Core scraping functions (`parse_categories`, `parse_listing`, `parse_post`, `quick_search`) in `f2m.py` MUST delegate to the new DOM scraper while maintaining identical signatures and return types.
- **FR-016**: Core fetch routines (`fetch`, `fetch_post`, `fetch_home`) in `f2m.py` MUST delegate to `f2m.net.client.HttpClient` while maintaining existing interactive UI spinner integration.
- **FR-017**: All 28 existing Phase 1 and Phase 2 tests MUST continue passing without regression.

---

## 4. Success Criteria *(mandatory)*

- **SC-001 (DOM Scraping Robustness)**: 100% of recorded HTML fixtures (including edge cases with reordered attributes or extra whitespace) are successfully parsed into valid domain models with 0 unhandled exceptions.
- **SC-002 (Graceful Parse Error Handling)**: 100% of malformed HTML inputs raise `F2MParseError` rather than Python built-in exceptions (`AttributeError`, `IndexError`, `KeyError`).
- **SC-003 (Mirror Failover Resilience)**: In simulated network failure tests where the primary domain is down, requests automatically resolve via configured mirrors without user intervention.
- **SC-004 (Zero Silent Config Mutation)**: 0 writes to `config.ini` occur during HTTP redirects or mirror failovers across all test executions.
- **SC-005 (Full Regression Safety)**: All 28 existing tests from Phase 1 and Phase 2 pass with 0 failures after integration.
- **SC-006 (Documentation Synchronization)**: Complete documentation of network retry behavior, timeout defaults, mirror failover, and scraper architecture in both `README.md` and `README.fa.md`.

---

## 5. Assumptions & Boundaries

### Assumptions
- `beautifulsoup4` (>=4.11.0) is added to `pyproject.toml` runtime dependencies, utilizing standard library `html.parser` so no external C-compilation (e.g. `lxml`) is required.
- Target website Film2Media continues to use standard semantic HTML tags (`<article>`, `<nav>`, `<a>`, `<h2>`, `<img>`, `<div>`).

### Explicit Scope Boundaries (Out of Scope for Phase 3)
- No terminal UI redesign or `rich` formatting (deferred to Phase 5).
- No new CLI flags such as `--json` or `--plain` (deferred to Phase 4).
- No downloader changes, aria2c alterations, or `sudo` removal (deferred to Phase 6).
- No packaging or CI release pipelines (deferred to Phase 7).
