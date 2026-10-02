# Feature Specification: Phase 5 — Terminal UI & RTL Redesign with Rich

**Feature Branch**: `feat/phase-5-terminal-ui-rtl`

**Created**: 2026-10-02

**Status**: Draft (Clarified)

**Input**: User description: "Phase 5 — Terminal UI / RTL Redesign with Rich: Modernize the interactive terminal experience using rich while preserving the CLI architecture and machine-readable interfaces established in Phase 4. Deliver a professional, readable, consistent, and usable terminal UI in both LTR and RTL contexts (particularly Persian/Arabic text)."

---

## 1. Executive Summary & Purpose

Phase 1 established automated test infrastructure and golden fixtures. Phase 2 delivered typed domain entities and an XDG-compliant configuration engine. Phase 3 delivered a resilient BeautifulSoup4 DOM scraper and retry-enabled HTTP client with mirror failover. Phase 4 delivered modern CLI argument parsing, strict stream isolation, POSIX exit codes, and machine-readable `--json` and `--plain` modes.

Phase 5 addresses the human-interactive terminal presentation layer: **Terminal UI & RTL Redesign with Rich**. Currently, the interactive terminal presentation in `f2m.py` relies on ad-hoc ANSI escape sequences (`C` class), raw string padding (`str.rjust`), manual box-drawing characters (`╔═══╗`), unbuffered stdout printing, and an elementary background spinner thread. Persian titles with mixed English tokens (e.g. `فیلم Inception 2010 دوبله فارسی`), years, episode badges, and URLs frequently exhibit misalignment, awkward wrapping, visual truncation, or bracket inversion across varying terminal geometries.

Phase 5 introduces a structured, testable presentation architecture using the `rich` library (under `f2m/ui/`):
1. **Professional Terminal Aesthetics**: Cohesive visual styling using Rich `Console`, styled `Panel`, semantic `Table` widgets, and clean typography.
2. **Terminal-Safe RTL & BiDi Handling**: Robust rendering strategies for Persian and Arabic text mixed with English movie titles, release years, IMDb scores, URLs, and filesystem paths without corrupting machine-readable tokens or overflowing columns.
3. **Responsive Geometry Adaptation**: Graceful handling of narrow terminals (down to standard 80x24) through automatic column wrapping, ellipsis truncation, and adaptive padding.
4. **Interactive Menus & Status Presentation**: Modernized interactive selections, category explorers, quality pickers, and transient spinners (`rich.status.Status` / `rich.progress`) routed strictly to `stderr`.
5. **Architectural Isolation & Preservation**:
   - Zero modifications to Phase 4 machine-readable streams: `--json` and `--plain` remain 100% unadorned and never pass through Rich rendering.
   - Zero changes to core domain models (`f2m.core.models`), configuration engine (`f2m.core.config`), scraper (`f2m.core.scraper`), or HTTP client (`f2m.net.client`).
   - Strict adherence to Constitution Principle I (Professional CLI UX), Principle II (Reliability Over Aesthetics), and Principle III (Backward Compatibility).

---

## 2. Clarifications & Architectural Decisions

### Session 2026-10-02

#### 1. In-Scope Interactive Flows & Components
The following user-facing interactive flows and presentation elements are upgraded to Rich:
1. **Welcome Banner (`banner()`)**: Styled Rich `Panel` with app name, version tag, active base URL, and short description.
2. **Interactive Menus (`menu()`)**: Aligned table-based selection layout with keyboard shortcuts (`1-N`, `0`/`b`/`q` to go back) and distinctive prompt symbol (`❯ `).
3. **Search Results (`search_flow()`)**: Rich `Table` featuring discrete columns: index, media type badge (`🎞 Movie` / `📺 Series`), Persian title, English title, release year, IMDb star rating, and audio/subtitle flags.
4. **Categories & Genres (`categories_flow()`, `genre_menu()`, `listing_menu()`)**: Multi-column layout with section badges and pagination indicators (`— page 1/12`).
5. **Post Inspection Header (`show_post_header()`)**: Rich `Panel` with title, rating, IMDb link, genres, and trailer badge.
6. **Download Version & Quality Picker (`choose_quality()`, `choose_episodes()`)**: Clean tabular layout with encoder badges (`F2M`, `PSA`) and episode counts.
7. **Pre-Download / Action Screen (`after_selection()`)**: Styled panel displaying selected files count, sample filenames, destination folder, and action buttons (`Download`, `Stream`, `Copy links`).
8. **Transient Network & Status Indicators**: Replaces multi-threaded `Spinner` with Rich `Console.status()` on `stderr`.
9. **Diagnostics & Messages**: `ok()`, `warn()`, `info()`, and `err()` updated to use Rich text styling with clean Unicode badges.

#### 2. Exact Boundary Between Rich UI and Phase 4 `--json` / `--plain`
- **Machine-Readable Streams Untouched**:
  - In `--json` mode: `stdout` emits pure JSON via `JsonFormatter`. Rich `Console` is **NEVER** used to format or emit data payloads.
  - In `--plain` mode: `stdout` emits pure TSV/lines via `PlainFormatter`. Rich `Console` is **NEVER** used to format or emit plain data payloads.
  - In `--json` and `--plain` modes, transient spinners and Rich status animations are disabled (inert).
- **Human-Interactive Mode**:
  - Only when output format is `OutputFormat.HUMAN` does the Rich presentation layer render styled tables, panels, and menus.
- **Diagnostic Stream Routing**:
  - Status spinners, progress bars, operational warnings, and error diagnostics route strictly to `sys.stderr`.
  - Data payloads (tables in human mode, JSON in `--json` mode, TSV in `--plain` mode) route strictly to `sys.stdout`.

#### 3. Practical BiDi & RTL Presentation Strategy
- **Terminal Emulator Realities**:
  - Terminal emulators have fragmented, conflicting implementations of the Unicode Bidirectional Algorithm (UBA). Forcing wholesale string reversal corrupts modern terminals with native BiDi (e.g. Windows Terminal, modern VTE, Kitty), while naive LTR rendering misaligns mixed strings.
- **Structural Segregation Contract**:
  - Rather than concatenating Persian titles, English titles, years, and ratings into a single string, Rich `Table` columns isolate discrete fields.
  - **Column 1**: Index (`#`, numeric, right-aligned)
  - **Column 2**: Type (`🎞 Movie` / `📺 Series`)
  - **Column 3**: Persian Title (`title_fa`)
  - **Column 4**: English / Original Title (`title`, LTR)
  - **Column 5**: Release Year (`year`, numeric)
  - **Column 6**: IMDb Rating (`★ rating`, yellow)
  - **Column 7**: Badges (`Dub` / `Hardsub`)
- **Strict Protection for Machine Tokens**:
  - URLs, magnet links, filesystem paths, filenames, quality tokens (`1080p.BluRay.x265`), episode numbers (`S01E02`), and command options MUST NEVER be reshaped, reversed, or bidirectionalized. They remain strictly LTR.
- **Copyability Guarantee**:
  - URLs and paths printed to the terminal (e.g. during link copying or streaming) must be printed as raw, intact LTR strings to guarantee they can be copied or clicked without phantom directional characters (`‎`/`‏`) breaking downstream tools.
- **Accurate Character Cell Width**:
  - Character cell width calculation uses `rich.cells.cell_len` (handling Persian characters and zero-width non-joiners `‌`) to guarantee unbroken, aligned table borders.

#### 4. Rich Markup Escaping & Security
- All external or upstream strings (movie titles, synopsis text, URLs, error messages) MUST pass through `rich.markup.escape()` before being interpolated into Rich renderables.
- This prevents user-controlled or site-controlled strings containing brackets (e.g. `[1080p]`, `[Dubbed]`, `[F2M]`) from being misinterpreted as Rich BBCode markup tags.

#### 5. ANSI, Terminal Width & `NO_COLOR` Handling
- **`NO_COLOR` and `--no-color`**:
  - When `NO_COLOR` is present in `os.environ` or `--no-color` is passed, `UiConsole` sets `no_color=True` on Rich `Console`. Colors are stripped while borders, padding, and alignment are preserved.
- **Non-TTY Detection**:
  - When `stdout` is redirected to a pipe or file without explicit flags, Rich `Console` automatically disables color codes (`color_system=None`) and status spinners.
- **Terminal Width Adaptability**:
  - For standard 80x24 terminals: Tables enable `overflow="fold"` or `overflow="ellipsis"` on non-critical columns; panels adapt dynamically to `console.width`.
  - For narrow windows (< 60 columns): Menus and results fall back to a clean single-column vertical list to prevent horizontal truncation.

#### 6. Error & Exit-Code Preservation
- Operational errors in human-interactive mode are formatted with Rich `err()` on `stderr`.
- All Phase 4 exit codes are strictly preserved:
  - `0`: Success
  - `1`: Operational error
  - `2`: Invalid argument / syntax error
  - `3`: Configuration error (`F2MConfigError`)
  - `4`: Network error (`F2MNetworkError`)
  - `5`: Parse error (`F2MParseError`)
  - `6`: Not found (empty search results, HTTP 404)
  - `130`: Interrupted (`SIGINT` / `Ctrl+C`)
- When `Ctrl+C` is pressed, Rich screen state is restored cleanly, `interrupted` is printed to `stderr`, and the process terminates with exit code `130`.

#### 7. Testing Strategy Without Brittle Terminal Snapshots
- Unit tests use `Console(record=True, width=80)` to capture text rendering into memory.
- Assertions verify **semantic presence** rather than pixel/ANSI-exact screen dumps:
  - Assert that titles, years, ratings, and column headers appear in the rendered text.
  - Assert that table border characters (`│`, `─`) are present and aligned.
  - Assert that `escape()` properly neutralizes bracketed strings like `[1080p]`.
  - Assert that `NO_COLOR` output contains zero ANSI escape sequences.
  - Assert that cell width helper correctly measures Persian strings with ZWNJ (`‌`).
- Subprocess E2E tests verify that `--json` and `--plain` outputs remain 100% identical to Phase 4 contracts with zero Rich markup.

---

## 3. User Scenarios & Testing *(mandatory)*

### User Story 1 - Rich Interactive Search & Media Exploration (Priority: P1)
As an interactive terminal user, I want search results, movie details, and categories to be displayed in clear, beautifully formatted Rich tables and panels with proper alignment and typography, so that exploring media in the terminal is intuitive, readable, and visually polished.

**Why this priority**: Core human-facing capability of the tool. Delivers Constitution Principle I (Professional CLI UX).

**Independent Test**: Run `python3 f2m.py search "Inception"` in an interactive terminal. Verify that results render in a styled Rich `Table` with distinct columns for index, title, Persian title, year, rating, and badges, followed by a clean selection prompt.

**Acceptance Scenarios**:
1. **Given** a search query with multiple results, **When** executing in interactive mode, **Then** results are rendered in an aligned Rich table with styled column headers, formatted rating stars, and clear index numbers.
2. **Given** a post URL or search selection, **When** inspecting media details, **Then** post metadata is presented inside a styled Rich `Panel`, with seasons and qualities structured hierarchically.
3. **Given** a terminal resize to 80 columns, **When** displaying tables or panels, **Then** content wraps gracefully without visual truncation or character overflow.

---

### User Story 2 - Legible Persian & Mixed-Direction Text Presentation (Priority: P2)
As a Persian-speaking user, I want titles containing both Persian text and English words (along with years and numbers) to render legibly without reversed words, inverted parentheses, or misaligned table borders, so that I can easily read titles and descriptions.

**Why this priority**: Essential for the target user demographic. Resolves the long-standing issue where Persian and English mixed text caused terminal rendering chaos.

**Independent Test**: Render search results containing mixed Persian/English titles (e.g. `فیلم Inception 2010 دوبله فارسی`) into a Rich table. Verify that table borders remain unbroken, column widths are calculated accurately taking wide characters into account, and English tokens remain in correct LTR sequence.

**Acceptance Scenarios**:
1. **Given** a media post with both English title (`Inception`) and Persian title (`اینسپشن`), **When** rendered in the search table, **Then** both titles are displayed in separate aligned columns, preventing BiDi text collisions.
2. **Given** a Persian title string containing embedded numbers (e.g. `فصل 2 قسمت 10`), **When** rendered, **Then** numbers and words maintain correct reading order without reversing.
3. **Given** any text containing URLs or filesystem paths, **When** rendered, **Then** the path or URL is strictly protected as LTR and never reversed or mutated.

---

### User Story 3 - Interactive Menus & Transient Status Presentation (Priority: P3)
As an interactive user navigating multi-season series or selecting episode ranges, I want responsive selection prompts, clear range syntax assistance (`1-5`, `all`), and unobtrusive transient loading spinners on `stderr`, so that I always know what the program is doing.

**Why this priority**: Upholds interactive responsiveness, transparency, and clean cancellation.

**Independent Test**: Navigate a multi-season series flow in an interactive terminal. Verify that loading indicators use Rich status spinners on `stderr` and clear cleanly upon completion, leaving the screen clean.

**Acceptance Scenarios**:
1. **Given** an asynchronous network fetch, **When** loading data, **Then** a transient Rich status spinner appears on `stderr` and clears upon completion without leaving lingering characters.
2. **Given** an episode selection prompt, **When** displaying options, **Then** valid range syntax (`3`, `1,3,5-8`, `all`) is displayed in styled dim guide text.
3. **Given** the user presses `Ctrl+C`, **When** interrupted, **Then** the interactive display exits cleanly, prints `interrupted` to `stderr`, and exits with code `130`.

---

### User Story 4 - Strict Preservation of Non-Interactive Machine Streams (Priority: P4)
As an automation engineer piping `f2m search ... --json` or `f2m url ... --plain`, I want the introduction of Rich to have absolutely zero effect on `--json` and `--plain` streams, so that automated scripts, cron jobs, and downstream consumers experience zero regression.

**Why this priority**: Guarantees Constitution Principle III (Backward Compatibility) and preserves the contract established in Phase 4.

**Independent Test**: Execute `f2m search "Inception" --json | jq .` and `f2m url <url> --plain`. Assert that `stdout` contains zero ANSI escape sequences, zero Rich markup, and 100% matches Phase 4 test contracts.

**Acceptance Scenarios**:
1. **Given** the `--json` flag is provided, **When** executing any command, **Then** Rich terminal rendering is completely bypassed; pure JSON is written to `stdout`.
2. **Given** the `--plain` flag is provided, **When** executing any command, **Then** Rich terminal rendering is completely bypassed; pure TSV or newline links are written to `stdout`.
3. **Given** an error occurs in `--json` mode, **When** terminating, **Then** `stdout` is empty and `stderr` receives the Phase 4 structured JSON error object.

---

### Edge Cases
- **`NO_COLOR` Environment Variable**: When `NO_COLOR` is present in `os.environ` or `--no-color` is supplied, Rich `Console` MUST disable all colors and styling while maintaining structural alignment.
- **Non-TTY `stdout` in default mode**: When `f2m` is piped to a file or another command without explicit flags (`f2m search ... > file.txt`), Rich `Console` MUST disable interactive colors and status spinners.
- **Extremely Narrow Terminals (< 60 columns)**: When terminal width is severely restricted, the UI falls back to a compact single-column list rather than overflowing tables.
- **Corrupt / Zero-Width Unicode Characters**: Titles containing invisible RTL marks, non-breaking spaces, or zero-width joiners (`‌`) must have their visual cell width calculated accurately via `rich.cells.cell_len` to prevent table border misalignment.
- **Bracketed Upstream Titles**: Titles containing bracketed tokens like `[1080p]` must be escaped with `rich.markup.escape()` so Rich does not crash or misinterpret them as formatting tags.

---

## 4. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST declare `rich>=13.0.0` in `pyproject.toml` runtime dependencies.
- **FR-002**: System MUST isolate terminal UI components into a dedicated package `f2m/ui/` with zero coupling to core scraping or network transport logic.
- **FR-003**: System MUST provide a configured `Console` abstraction in `f2m/ui/console.py` that automatically detects TTY status, color capabilities, terminal width, and `NO_COLOR` / `--no-color` flags.
- **FR-004**: System MUST render interactive search results using a styled Rich `Table` with distinct, aligned columns for index, type, Persian title, English title, release year, rating, and dub/sub badges.
- **FR-005**: System MUST render media post details (metadata, IMDb ID, rating, trailer availability) inside a styled Rich `Panel`.
- **FR-006**: System MUST format version, quality, and episode selection hierarchies using clear Rich lists or tables with distinct encoder badges and episode counts.
- **FR-007**: System MUST render categories and genres in multi-column Rich tables or organized panels.
- **FR-008**: System MUST display configuration tables using styled Rich tables in human-readable mode.
- **FR-009**: System MUST preserve pure, unadorned JSON serialization on `stdout` when `--json` is supplied, guaranteeing zero Rich markup or ANSI codes leak into JSON streams.
- **FR-010**: System MUST preserve pure TSV and newline-delimited text on `stdout` when `--plain` is supplied, guaranteeing zero Rich markup leaks into plain streams.
- **FR-011**: System MUST route all transient status spinners (`Console.status()`) and progress indicators exclusively to `sys.stderr`.
- **FR-012**: System MUST disable transient spinners and progress animations when `--json` or `--plain` is active or when `sys.stderr` is not a TTY.
- **FR-013**: System MUST isolate Persian and English text into separate table columns or use directional boundaries (`‎` / `‏`) to prevent BiDi text collisions.
- **FR-014**: System MUST calculate Unicode cell widths accurately (supporting zero-width non-joiners `‌` and Persian characters) to prevent table border misalignment.
- **FR-015**: System MUST escape all upstream text and user input with `rich.markup.escape()` before rendering.
- **FR-016**: System MUST strictly preserve URLs, file paths, and filenames as verbatim LTR strings without directional mutation.
- **FR-017**: System MUST preserve all existing interactive menu choices, prompt parsing (`parse_selection`), download triggers (`aria2c`/`curl`), and streaming dispatch (`mpv`/`vlc`).
- **FR-018**: System MUST preserve all Phase 4 POSIX exit codes (`0`, `1`, `2`, `3`, `4`, `5`, `6`, `130`) across all interactive and non-interactive workflows.

---

### Key Entities

- **`Theme`**: Unified color palette mapping semantic roles (`title`, `accent`, `rating`, `success`, `warning`, `error`, `dim`, `border`) to terminal styles.
- **`UiConsole`**: Managed wrapper around Rich `Console` managing `stdout` and `stderr` streams, width limits, and color toggles.
- **`MediaTable`**: View component rendering `SearchResult` collections into responsive, BiDi-safe Rich tables.
- **`PostView`**: View component rendering `MediaPost` metadata panels, version choices, and quality listings.
- **`CategoryView`**: View component rendering category sections and genre taxonomies into organized tables.

---

## 5. Testing & Verification Matrix

The test strategy spans 4 complementary verification layers:

1. **Unit Tests (`tests/unit/test_ui_rendering.py`)**:
   - Verify Rich `Console` initialization under color-enabled, `NO_COLOR`, and non-TTY configurations.
   - Verify cell width calculation for Persian text, ZWNJ (`‌`), and mixed strings.
   - Verify `MediaTable` rendering using an in-memory `Console(record=True)`.
   - Verify `PostView` panel and quality hierarchy rendering.
   - Verify that URLs and paths are never reversed or corrupted by BiDi processing.
   - Verify that bracketed text `[1080p]` is safely escaped via `escape()`.
2. **Terminal Geometry & Width Tests (`tests/unit/test_ui_geometry.py`)**:
   - Test table rendering at standard 80-column width: verify zero broken borders and clean column wrapping.
   - Test rendering at narrow 60-column width: verify fallback or clean truncation.
   - Test rendering at wide 120-column width: verify balanced column distribution.
3. **Stream Isolation & Subprocess Regression Tests (`tests/e2e/test_ui_e2e.py`)**:
   - Execute `f2m search "Inception" --json` via `subprocess.run`: assert `stdout` parses with `json.loads` and contains zero Rich ANSI codes.
   - Execute `f2m url <url> --plain` via `subprocess.run`: assert `stdout` contains only direct download links without Rich formatting.
   - Execute `f2m search "Inception"` with `NO_COLOR=1`: verify colors are cleanly stripped.
   - Execute `f2m help`, `f2m version`, `f2m config`, and `f2m test`: verify Rich formatting in TTY mode and clean text when piped.
4. **Regression Safety Net**:
   - All 72 existing unit and E2E tests from Phases 1, 2, 3, and 4 continue to pass with 100% success.

---

## 6. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of interactive search results, post views, and menus render using structured Rich tables/panels with aligned borders and zero overlapping text.
- **SC-002**: 100% of table borders remain unbroken and aligned when rendering mixed Persian/English titles and release years.
- **SC-003**: 100% of `--json` and `--plain` command invocations remain completely free of Rich markup, ANSI escape sequences, or spinner text.
- **SC-004**: In non-TTY environments or with `NO_COLOR=1`, 100% of ANSI color codes are stripped while retaining structured table borders and text layout.
- **SC-005**: All 72 existing unit and regression tests from Phases 1–4 continue to pass with zero regressions.
- **SC-006**: Interactive keyboard navigation (`1-5`, `all`, `q`/`b` for back, `Ctrl+C` for clean exit 130) functions identically to legacy workflows.

---

## 7. Assumptions & Scope Exclusions

### Assumptions
- `rich>=13.0.0` is portable across Linux, macOS, and modern Windows terminals (Windows Terminal / PowerShell with VT support).
- Modern terminal emulators correctly handle standard UTF-8 box drawing characters (`│`, `─`, `┌`, `┐`, `└`, `┘`).
- For legacy Windows consoles without full VT support, Rich automatically provides ASCII fallbacks.

### Scope Exclusions
- **Downloader Security (`sudo` removal)**: Downloader execution, `aria2c` sandboxing, and package manager privilege removal are strictly deferred to **Phase 6**.
- **Packaging / PyPI Distribution / CI Workflows**: PyPI build configuration, wheel packaging, entry points, and GitHub Actions CI pipelines remain strictly deferred to **Phase 7**.
- **Scraper / Network Modifications**: Scraper DOM selectors and HTTP retry/mirror failover logic remain strictly untouched.

---

## 8. Backward Compatibility Invariants

1. **CLI Commands & Flags**:
   - All Phase 4 commands (`search`, `url`, `categories`, `config`, `config get`, `config set`, `test`, `help`, `version`) and options (`--json`, `--plain`, `--no-color`, `--config`) retain identical syntax, semantics, and exit codes.
2. **Machine-Readable Payload Purity**:
   - The exact JSON schemas and TSV plain output formats established in Phase 4 contracts remain strictly invariant.
3. **Interactive Menu Usability**:
   - Existing selection habits (entering single numbers, comma-separated lists, hyphens for ranges `1-5`, `all`, and `0`/`b`/`q` to go back) remain 100% supported.
