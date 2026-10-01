# Feature Specification: Baseline Modernization of film2media-cli

**Feature Branch**: `001-baseline-specification`

**Created**: 2026-10-01

**Status**: Draft

**Input**: User description: "Create the baseline specification for transforming film2media-cli into a professional-grade CLI application."

---

## 1. Executive Summary & Purpose

`film2media-cli` (`f2m`) is an interactive and non-interactive command-line tool designed to search, browse, resolve, stream, and download media content from the Iranian media portal Film2Media.

The current repository reflects an early-stage, single-file fork (`f2m.py`, ~1400 LOC) that combines CLI parsing, terminal UI rendering, web scraping via regular expressions, configuration persistence, subprocess management, and package installation into a single procedural namespace. While functional under nominal conditions, it suffers from severe architectural fragility, zero automated test coverage, security risks in external tool handling, terminal display glitches with Persian/RTL text, and tight coupling that prevents safe enhancement.

This specification serves as the **authoritative architectural baseline and roadmap**. It reverse-engineers the current implementation, catalogs all defects and constraints, defines the target product behavior, and partitions the transformation into decoupled, independently reviewable, and testable delivery phases in strict accordance with the project Constitution (`.specify/memory/constitution.md`).

---

## Clarifications

### Session 2026-10-01
- Q: Should `film2media-cli` remain strictly standard-library-only at runtime, or may it adopt a minimal set of vetted external libraries for parsing and terminal rendering? → A: Option B (Pragmatic Curated Dependencies: Allow a minimal set of vetted, high-quality dependencies such as `rich` for resilient terminal UI/tables/Unicode/RTL alignment and a robust HTML parser for source/pip installations, while continuing to distribute zero-dependency standalone binaries via PyInstaller for end users).
- Q: When a user executes `f2m search <query>` in an interactive terminal, should it launch the full-screen interactive selection menu by default, or print results as a standard terminal table? → A: Option A (Interactive Default in TTY with Auto-Detection: Maintain legacy behavior where `f2m search <query>` opens the interactive selection screen in a TTY for 100% backward compatibility, while automatically emitting structured plain text/JSON without entering the TUI if piped or if `--json`/`--plain`/`--quiet` flags are passed).
- Q: When `aria2c` is not found on the system, how should `film2media-cli` handle downloading? → A: Option A (Manual Guidance with Graceful Fallback: Completely eliminate automated binary installations and `sudo` executions. Display clear platform-specific install instructions such as `sudo apt install aria2` or `winget install aria2`, while offering an immediate graceful fallback to `curl` or exporting links).
- Q: How should `film2media-cli` handle migration from the legacy `f2m.conf` file to standard user-level configuration directories? → A: Option A (Seamless Migration with Portable Override: If standard user config does not exist but a legacy `f2m.conf` is found, import its values into the standard XDG/AppData location and inform the user. Also support a local `./f2m.conf` in the working directory as a portable override taking precedence when present).
- Q: When the upstream website redirects to a new domain or an ISP filter necessitates using a mirror, how should `film2media-cli` persist domain changes? → A: Option A (Session-Transient with Prompt for Permanence: Automatically follow redirects or fail over to mirrors for the active session without silently mutating disk; prompt the user interactively before updating persistent configuration, and in non-interactive/headless mode, never mutate disk configuration without an explicit flag).

---

## 2. Current Implementation Baseline

### 2.1 Complete Architecture & Code Structure
- **Monolithic Single File**: All functionality resides in `f2m.py` (1,399 lines).
- **Global & Mutable State**:
  - `_cfg`: Module-global dictionary holding runtime configuration.
  - `_OPENER`: Global `urllib.request.OpenerDirector` initialized at import time with `CookieJar` and `ProxyHandler`.
  - `Screen.depth`: Class-level variable tracking alternate screen buffer recursion.
  - `C.ENABLED`: Global boolean evaluated once at import time for ANSI color support.
- **Layer Coupling**: HTTP fetching (`fetch`), HTML parsing (`PATTERNS`), domain mutation (`maybe_update_domain`), user prompts (`prompt`, `menu`), and subprocess execution (`do_download`, `do_stream`) are directly interlocked within interactive flow loops (`movie_flow`, `series_flow`, `listing_menu`).

### 2.2 Command Handling & CLI Interface
- **Dispatching**: Minimal custom string matching on `sys.argv[1]` in `cli(argv)` (`help`, `search`, `url`, `categories`, `config`, `test`).
- **Standard Library Gaps**: Does not use standard `argparse`, `click`, or structured CLI frameworks. Options cannot be combined cleanly (e.g. `--proxy` or `--no-color` as global flags).
- **Exit Codes**: Does not follow POSIX exit code conventions. Failure paths frequently call `return` instead of terminating with a distinct exit code (e.g. `2` for invalid syntax, `1` for network failure).
- **Automation / Scriptability**: Commands like `search` and `url` force users into an interactive full-screen menu via `run_interactive()`, preventing programmatic use (piping URLs to files or stdout).

### 2.3 Interactive Menus & Navigation Model
- **Screen Buffer & Redraws**: Uses ANSI escape `\033[?1049h` (alternate screen) and `\033[H\033[2J` to redraw frames. If a user interrupts via `Ctrl+C` or an unhandled exception occurs, the terminal can remain trapped in the alternate buffer or corrupted.
- **Selection Parsing**:
  - Numeric inputs (`1-N`), ranges (`1,3,5-8`), and wildcards (`all`, `*`, `a`).
  - Supports Persian comma (`،`) splitting.
- **Navigation Inconsistencies**:
  - Exit/Back keys vary across screens (`0`, `b`, `q`, empty Enter).
  - No breadcrumb navigation or ability to jump to main menu from deep nested flows (Category → Genre → Page → Post → Season → Version → Quality → Episode).

### 2.4 Search & Scraping Behavior
- **Dual-Path Search**:
  1. `quick_search`: AJAX POST to `/quick-search` with `q` and `sort` (`modified_at:desc`), parsing JSON.
  2. Fallback to HTML search: GET `/?s=<query>`, parsing HTML cards.
- **Regular Expression Scraping (`PATTERNS`)**:
  - HTML parsing relies exclusively on compiled regular expressions (`re.compile`) rather than a DOM parser (e.g., `html.parser` or BeautifulSoup).
  - Minor markup changes by the upstream site (e.g., attribute ordering, extra whitespace, modified classes) completely break link and metadata extraction.

### 2.5 Media Selection & Parsing Model
- **Entities**: `Post`, `Season`, `Version` (Dub vs Hardsub), `Quality` (resolution, encoder), `Episode` (number, URL, filename).
- **Post Parsing (`parse_post`)**:
  - Detects series vs movie based on URL slug `/series/` or existence of `<div class="download-season"`.
  - Filename heuristics (`SE_TOKEN`, `DUB_TOKEN`, `SUB_TOKEN`) parse season/episode numbers and audio language directly from download URLs.
  - Fragile splitting on `<div class="download-list">` and `<li>` tags.

### 2.6 Downloads & External Tool Integration
- **Download Dispatch**:
  - Prioritizes `aria2c` with aggressive flags (`-x 16 -s 16 -j 4`).
  - Fallback to sequential `curl` commands if `aria2c` is absent.
  - Fallback to printing raw URLs if both are missing.
- **Automatic Binary Installation Risks**:
  - **Windows**: Downloads precompiled binary from `https://github.com/aria2/aria2/releases/...` without SHA-256 verification or TLS certificate pinning.
  - **Linux**: Iterates through `LINUX_PKG_MANAGERS` (`apt-get`, `dnf`, `yum`, `pacman`, `apk`, `zypper`) and invokes `sudo <mgr> install -y aria2` automatically. Spawning `sudo` under the hood without explicit prompt or user awareness is a critical security and operational hazard.
- **Streaming Players**:
  - Resolves player from `_cfg["player"]` (`auto`, `mpv`, `vlc`, `potplayer`).
  - Hardcoded Windows file paths (e.g., `C:\Program Files\VideoLAN\VLC\vlc.exe`).
  - Spawns background process via `subprocess.Popen` with discarded `stdout`/`stderr`, hiding crashes or missing codec errors from the user.

### 2.7 Domain, Mirror, and Proxy Management
- **Domain Persistence**: Defaults to `https://www.myf2ms.top` with mirror `https://www.myf2m.info`.
- **Silent Auto-Update**: `maybe_update_domain()` inspects HTTP redirects. If the response hostname contains `"f2m"`, it updates `_cfg["base_url"]` and immediately writes to `f2m.conf` on disk. If an upstream domain redirects to a malicious or compromised landing page containing `"f2m"`, the application permanently switches its trust anchor.
- **Proxy Configuration**: Passes proxy to `urllib`, `aria2c --all-proxy`, and `--http-proxy` for `mpv`/`VLC`.

### 2.8 Configuration Storage & Platform Issues
- **File Location (`CONF_PATH`)**: Determined relative to `__file__` or `sys.executable`.
- **Permission Bug**: If installed in system directories (e.g., `/usr/local/bin` or `C:\Program Files`), saving configuration throws `PermissionError`. Fails to adhere to standard XDG Base Directory specification (`~/.config/f2m/config.ini`) on Linux/macOS or `%APPDATA%` on Windows.

### 2.9 Terminal Rendering & Bidirectional Text (RTL)
- **Formatting**: ANSI color utility class `C`.
- **RTL & Column Misalignment**: The genre menu attempts two-column formatting using fixed character width:
  `line += " " * max(2, 34 - len(f"{i + 1}. {left[i][0]}"))`
  Because Persian characters have different visual/terminal cell widths and bidirectional rendering rules, `len()` on Unicode strings produces severe visual misalignment and broken table borders in terminal emulators.

### 2.10 Testing & Testability State
- **Automated Tests**: Exactly 0 tests exist.
- **Testability**: Extremely low in current form due to hardcoded module globals, static `urllib` calls inside UI routines, and direct calls to `subprocess.call` without dependency injection.

### 2.11 Documentation Parity
- `README.md` (English) and `README.fa.md` (Persian) exist.
- Documentation lacks details on CLI exit codes, environment variables (`NO_COLOR`, `F2M_CONFIG`), proxy authentication formatting, and troubleshooting corrupted terminal states.

---

## 3. Defect & Risk Catalog

| ID | Category | Description | Severity | Impact |
|---|---|---|---|---|
| **DEF-001** | Security | Auto-installing `aria2c` on Linux calls `sudo` without interactive confirmation. | Critical | Unauthorized privilege escalation attempt. |
| **DEF-002** | Security | Auto-downloading Windows `aria2c.exe` lacks checksum / signature verification. | High | Potential remote binary tampering or MITM risk. |
| **DEF-003** | Reliability | `f2m.conf` stored next to script/binary causes `PermissionError` when installed system-wide. | High | CLI crashes on standard multi-user or root installations. |
| **DEF-004** | Architecture | Regex-only HTML scraping breaks on minor upstream whitespace/attribute alterations. | High | Core features (search, episode listing) fail silently or produce empty menus. |
| **DEF-005** | Security / Reliability | `maybe_update_domain()` updates `base_url` permanently based on unverified redirect hostnames. | Medium | Poisoned domain redirection or config corruption. |
| **DEF-006** | UX / Terminal | Alternate screen buffer not restored cleanly on SIGINT / unhandled exceptions. | Medium | Leaves user's terminal broken, hiding cursor or scrollback. |
| **DEF-007** | UX / Internationalization | String `len()` used for column calculation breaks two-column genre layouts with Persian text. | Medium | Disjointed terminal tables and misaligned columns. |
| **DEF-008** | Usability / Scriptability | Search and URL commands force full-screen interactive mode; cannot output links to stdout. | Medium | Cannot be piped into external download managers or scripts. |
| **DEF-009** | Reliability | Player process errors suppressed via `DEVNULL`; user sees success message even if player fails to launch. | Medium | Silent playback failure with false positive feedback. |
| **DEF-010** | Architecture | Monolithic single file with zero automated tests and high coupling. | High | High regression risk during any maintenance or refactor. |

---

## 4. User Scenarios & Target Product Capabilities

### User Story 1 - Reliable Non-Interactive Search & Resolution (Priority: P1)
As a terminal power user or script author, I want to query media and resolve direct download links non-interactively via standard CLI arguments, so that I can automate downloads and integrate `f2m` with external tools.

**Why this priority**: Core value proposition of a CLI tool; unblocks automated testing, headless usage, and decoupled architecture.

**Independent Test**: Execute `f2m search "Inception" --json` or `f2m get-links <url> --quality 1080p` and verify structured output on `stdout` without entering interactive TUI mode.

**Acceptance Scenarios**:
1. **Given** a valid query, **When** running `f2m search "Matrix" --format json`, **Then** the system outputs valid JSON containing matching titles, years, ratings, and URLs to `stdout` with exit code `0`.
2. **Given** a post URL and specific quality flag, **When** running `f2m resolve <url> --quality 1080p --stdout`, **Then** direct download links are emitted one per line to `stdout` and logs/progress to `stderr`.
3. **Given** network failure or invalid URL, **When** running CLI commands, **Then** diagnostic messages are sent to `stderr` and a non-zero exit code is returned.

---

### User Story 2 - Robust & Clean Interactive Terminal Experience (Priority: P2)
As an interactive desktop user, I want a modern, polished, and resilient terminal interface with clear navigation and reliable rendering, so that I can browse and select media comfortably without visual glitches or terminal corruption.

**Why this priority**: Primary human interaction mode; directly addresses current UX flaws, Persian text alignment, and graceful cancellation.

**Independent Test**: Launch interactive mode, navigate nested menus, resize terminal, trigger `Ctrl+C`, and verify the terminal returns to normal scrollback with clean exit.

**Acceptance Scenarios**:
1. **Given** the interactive menu is open, **When** pressing `Ctrl+C` or selecting `0 / Back`, **Then** the application restores cursor, normal screen buffer, and exits gracefully without dumping raw tracebacks.
2. **Given** Persian and English text displayed in category/genre tables, **When** rendering in varying terminal widths, **Then** columns remain aligned based on visual cell width (East Asian / Unicode width awareness).
3. **Given** a slow network connection, **When** fetching data, **Then** a non-blocking or polite spinner is shown, which can be cleanly cancelled by the user.

---

### User Story 3 - Resilient Network, Mirror & Domain Management (Priority: P3)
As a user in a restricted or filtered network environment, I want the client to reliably detect mirror availability, handle proxies, and validate domain updates, so that I can access media despite ISP blocks.

**Why this priority**: Essential for target user base in regions with frequent domain filtering.

**Independent Test**: Mock primary domain failure and verify deterministic fallback to configured mirrors and validated domain updates.

**Acceptance Scenarios**:
1. **Given** the primary `base_url` is unreachable or times out, **When** fetching content, **Then** the client systematically tries configured mirrors in order and warns the user with actionable diagnostics.
2. **Given** a domain redirect occurs, **When** validating the new domain, **Then** the new domain is used transiently for the active session, and permanent updates to disk require explicit user confirmation or an explicit command.
3. **Given** a proxy is configured (HTTP/SOCKS5), **When** communicating with site or downloading, **Then** all network operations correctly route through the configured proxy.

---

### User Story 4 - Safe & Controllable Download and Stream Dispatch (Priority: P4)
As a user, I want download and streaming operations to be transparent, safe, and controllable, with clear progress feedback and zero unexpected privileged actions.

**Why this priority**: Protects system security and ensures reliable external process orchestration.

**Independent Test**: Attempt download without `aria2c` installed and verify that system requests user permission or provides manual instructions instead of running `sudo`.

**Acceptance Scenarios**:
1. **Given** `aria2c` is not installed on Linux, **When** download is initiated, **Then** the client informs the user, offers manual package manager commands, and falls back to `curl` or link export without running `sudo`.
2. **Given** a stream action is triggered, **When** launching `mpv` or `vlc`, **Then** client validates player availability and surfaces player launch errors immediately if the player fails.
3. **Given** multiple episode downloads, **When** downloading via `aria2c`, **Then** files are organized into structured directories and progress is visible.

---

### Edge Cases
- **Upstream Structure Changes**: Upstream site alters HTML hierarchy or class names; parser MUST fail with a structured diagnostic identifying the parsing gap rather than crashing with unhandled `AttributeError` or `IndexError`.
- **Terminal Resize & Small Windows**: User runs client in an 80x24 terminal; menus and long titles MUST truncate or wrap without breaking table layout.
- **`NO_COLOR` Environment Variable**: When `NO_COLOR` is set or stdout is redirected, ANSI color codes MUST be completely stripped.
- **Permission-Restricted Config Directory**: In environments where default config paths are read-only, client MUST respect `--config <path>` or `F2M_CONFIG` override and degrade to in-memory configuration if unwritable.

---

## 5. Functional Requirements (Testable & Technology-Agnostic)

### CLI Core & Configuration
- **FR-001**: System MUST follow standard POSIX exit codes: `0` for success, `1` for runtime/operational errors, `2` for invalid CLI syntax/arguments, and `130` for user termination via `SIGINT`.
- **FR-002**: System MUST separate data output (`stdout`) from diagnostic logging, errors, and interactive UI framing (`stderr`).
- **FR-003**: System MUST load configuration hierarchically: built-in defaults < standard user configuration file (`~/.config/f2m/config.ini` on Unix, `%APPDATA%\f2m\config.ini` on Windows) < local `./f2m.conf` (if present in working directory, for portable mode) < environment variables (`F2M_*`) < explicit CLI flags (`--config <path>`). If a legacy `f2m.conf` exists adjacent to the executable but no standard user configuration exists, the system MUST migrate settings to the standard path automatically.
- **FR-004**: System MUST NOT attempt to write configuration files into application binary directories unless explicitly configured.
- **FR-015**: System MUST preserve backward compatibility by launching the interactive selection menu when `f2m search <query>` is invoked in a TTY, but MUST automatically switch to headless structured output (`stdout`) if output is piped, redirected, or when explicit non-interactive flags (`--json`, `--plain`, `--quiet`) are provided.

### Network & Scraping
- **FR-005**: System MUST isolate HTTP transport logic from domain parsing and user presentation.
- **FR-006**: System MUST parse HTML documents using robust tree parsing that tolerates whitespace, attribute reordering, and minor tag adjustments.
- **FR-007**: System MUST provide deterministic retry logic with configurable timeouts and exponential backoff across primary and mirror endpoints.
- **FR-008**: System MUST treat domain redirects and mirror failovers as session-transient by default; persistent updates to configuration on disk MUST require explicit interactive confirmation or an explicit CLI command/flag (`f2m config set base_url ...`), never occurring silently during automated/headless execution.

### Terminal UI & Rendering
- **FR-009**: Terminal UI MUST compute column widths using Unicode character display cells rather than byte or character length to properly align mixed Persian and English text.
- **FR-010**: System MUST trap `SIGINT` (`Ctrl+C`) and unexpected exceptions to restore terminal cursor visibility, disable mouse tracking, and exit alternate screen buffers cleanly.
- **FR-011**: System MUST strictly adhere to `NO_COLOR` and non-TTY detection by disabling ANSI color codes.

### External Tool Management & Process Control
- **FR-012**: System MUST NEVER invoke `sudo`, execute privileged package manager commands, or perform silent/unverified remote binary downloads.
- **FR-013**: When `aria2c` is missing, the system MUST display platform-specific copy-paste install commands (Linux package managers, macOS Homebrew, Windows winget) and immediately provide an automatic graceful fallback to sequential `curl` downloads or link export.
- **FR-014**: System MUST verify external player binaries before launch and capture startup failures, reporting errors to the user instead of silently failing.

---

## 6. Success Criteria (Measurable & Technology-Agnostic)

- **SC-001 (Automated Test Coverage)**: 100% of network parsing, URL extraction, configuration handling, and argument routing logic covered by automated unit/integration tests with offline mock fixtures.
- **SC-002 (Terminal Resilience)**: 0 unhandled terminal corruptions or abandoned alternate screen buffers across test runs involving interrupted operations (`SIGINT`).
- **SC-003 (RTL Alignment)**: Menu and category grids render without column wrapping or border breakage across standard terminal widths (80 to 120 columns) when displaying Persian strings.
- **SC-004 (Scriptability)**: Non-interactive search and link extraction commands complete in under 3 seconds on standard connections and emit 100% compliant structured output (`JSON` / plain text).
- **SC-005 (Zero Unauthorized Privileges)**: 0 invocations of `sudo` or silent binary downloads without explicit user consent.
- **SC-006 (Documentation Parity)**: 100% alignment between English and Persian documentation for all commands, options, environment variables, and configuration settings.

---

## 7. Assumptions & Boundaries

### Assumptions
- Target website Film2Media continues to provide publicly accessible media indexing pages and quick-search endpoints.
- Python 3.8+ runtime is available on the host system.
- Standard terminal emulators support VT100 / ANSI escape sequences, with optional truecolor/256-color support.
- Curated minimal third-party libraries (e.g., `rich` for UI/Unicode cell width, `beautifulsoup4` for HTML parsing) are permitted for Python package distributions, while standalone releases bundle all dependencies via PyInstaller to retain zero-dependency execution for binary users.

### Explicit Out of Scope (Non-Goals)
- Implementing web-based GUIs or mobile applications.
- Bypassing DRM or paywalls (tool only indexes publicly accessible direct links).
- Hosting or re-distributing copyrighted media files.

---

## 8. Target Architecture & Decoupled Domain Model

To evolve `f2m` into a professional, maintainable application, the architecture must transition from a monolithic procedural script into clearly separated packages:

```text
film2media-cli/
├── f2m/                       # Core Application Package
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── cli/                   # Command Line Parsing & Dispatch
│   │   ├── parser.py          # Structured argument parsing
│   │   └── commands/          # Subcommand handlers (search, get, config, browse)
│   ├── core/                  # Core Business Entities & Configuration
│   │   ├── models.py          # Post, Season, Quality, Episode dataclasses
│   │   ├── config.py          # XDG-compliant configuration manager
│   │   └── exceptions.py      # Standardized domain & network exceptions
│   ├── net/                   # Transport & Network Layer
│   │   ├── client.py          # HTTP client, mirrors, retries, proxies
│   │   └── scraper.py         # Robust HTML & JSON parsing (DOM-based)
│   ├── ui/                    # Terminal User Interface & Formatting
│   │   ├── theme.py           # Color palette, NO_COLOR handling
│   │   ├── screen.py          # Terminal state manager & signal handler
│   │   ├── text.py            # Unicode width & RTL-aware text formatting
│   │   └── views/             # Menus, tables, spinners, breadcrumbs
│   └── integrations/          # External Process Runners
│       ├── downloader.py      # aria2c & curl process management
│       └── player.py          # mpv, vlc, potplayer streaming manager
├── tests/                     # Automated Test Suite
│   ├── unit/                  # Fast offline unit tests
│   ├── integration/           # Scraper & parsing tests with HTML fixtures
│   └── e2e/                   # Subprocess CLI execution tests
└── docs/                      # Technical Documentation & Specs
```

---

## 9. Phased Modernization Roadmap

In accordance with Constitution Principle VI (Incremental Delivery) and VII (PR Ownership), modernization MUST proceed through seven independent, reviewable phases to eliminate mega-PR risks. Each phase will have its own dedicated feature branch, test plan, PR, and E2E gate.

### Phase 1: Test Infrastructure & Fixture Safety Net
- **Scope**: Establish project test infrastructure (`pytest`), build offline HTML/JSON fixture suite for Film2Media markup, and implement golden regression tests against legacy routines (`f2m.py`) with zero changes to existing application code.
- **Non-Goals**: No changes to application code, no UI changes, no feature implementations.
- **Dependencies**: None.
- **Acceptance Criteria**: Test harness runs via `pytest`; legacy golden tests pass with 0 failures; complete fixture suite in place.
- **E2E Acceptance Criteria**: Run `pytest` offline and verify tests pass without network access.
- **Documentation Requirements**: Document testing and dev setup in `README.md` and `README.fa.md`.
- **Regression Risks**: Low; additive test infrastructure only.

### Phase 2: Domain Entities & XDG Configuration Engine
- **Scope**: Extract typed domain models (`models.py`, `exceptions.py`) and replace unsafe binary-directory configuration with standard XDG/AppData configuration management (`~/.config/f2m/config.ini`), automatic legacy `f2m.conf` migration, and working-directory portable overrides.
- **Non-Goals**: No changes to scraping regexes, CLI arguments, or UI rendering.
- **Dependencies**: Phase 1 (requires test fixtures).
- **Acceptance Criteria**: Configuration loads without write errors on system-wide paths; models pass validation; legacy settings migrate cleanly.
- **E2E Acceptance Criteria**: Run `f2m config` in an environment with legacy `f2m.conf` and verify migration to user config folder.
- **Documentation Requirements**: Document configuration paths and migration behavior in bilingual READMEs.
- **Regression Risks**: Low; backward compatibility preserved via legacy migration.

### Phase 3: Resilient Network Transport & DOM Scraper Engine
- **Scope**: Replace regex-only HTML scraping with a robust, tree-tolerant scraper module (`beautifulsoup4`). Introduce structured HTTP client with retry policies, mirror failover, proxy support, and session-transient domain redirect validation (no silent disk writes).
- **Non-Goals**: No CLI argument parser overhaul; no terminal UX changes.
- **Dependencies**: Phase 2.
- **Acceptance Criteria**: 100% of existing search, category, post, and episode parsing test fixtures pass; network failures trigger clean `F2MNetworkError` without raw tracebacks; domain redirects do not alter disk configuration without approval.
- **E2E Acceptance Criteria**: Test CLI search against recorded mock server verifying complete extraction of titles, seasons, and download URLs.
- **Documentation Requirements**: Document proxy options and mirror failover mechanisms in bilingual READMEs.
- **Regression Risks**: Medium; changes to parsing logic could miss edge-case quality encodings.

### Phase 4: Non-Interactive CLI Engine & POSIX Exit Codes
- **Scope**: Implement modern CLI argument parser supporting non-interactive commands: `search`, `resolve` (extract links without TUI), `categories`, `config`, and `test` with `--json`, `--plain`, and `--quiet` output flags. Enforce POSIX exit codes (`0`, `1`, `2`, `130`). Preserve interactive menu launching in TTY for `search` and `url`.
- **Non-Goals**: No overhaul of interactive menus or color palette yet.
- **Dependencies**: Phase 3.
- **Acceptance Criteria**: Commands execute headlessly without entering alternate screen buffer; structured output emits to `stdout`, logs to `stderr`; exit codes strictly comply with POSIX.
- **E2E Acceptance Criteria**: Pipe `f2m search "Matrix" --format json` into `jq` and validate output schema; test `f2m resolve <url> --quality 1080p` outputting direct URLs.
- **Documentation Requirements**: Complete CLI manual and command reference in bilingual READMEs.
- **Regression Risks**: Low; existing interactive command defaults remain intact.

### Phase 5: Modern Interactive Terminal UX & RTL/Unicode Alignment
- **Scope**: Overhaul interactive terminal experience: clean terminal lifecycle management (alternate buffer and cursor restore on `Ctrl+C`), breadcrumb navigation, unified back/quit controls, and Unicode/RTL visual width calculation (`rich`) for Persian text alignment.
- **Non-Goals**: Modifying download engines or network protocols.
- **Dependencies**: Phase 4.
- **Acceptance Criteria**: Menu tables remain strictly aligned with Persian text; `Ctrl+C` at any screen leaves terminal in pristine state; 0 unhandled terminal corruptions.
- **E2E Acceptance Criteria**: Interactive terminal session driven via pseudo-terminal (PTY) testing verifying clean redraws and exits.
- **Documentation Requirements**: Update screenshot assets and terminal usage instructions in bilingual READMEs.
- **Regression Risks**: Medium; input handling across Linux, macOS, and Windows terminals.

### Phase 6: Secure Process Orchestration (Downloads & Streaming)
- **Scope**: Re-engineer `aria2c`, `curl`, and media player integrations. Completely remove automated `sudo` execution and unverified binary downloads. Provide clear manual installation commands for missing tools with immediate graceful fallback to `curl` or link export. Add player startup health checks and error capture.
- **Non-Goals**: Protocol-level modifications to aria2c.
- **Dependencies**: Phase 5.
- **Acceptance Criteria**: Missing `aria2c` triggers copy-paste instructions and clean fallback without attempting privileged escalation or downloads; streaming launch failures report actionable stderr output.
- **E2E Acceptance Criteria**: Verified download dispatch using local test file and mock aria2c binary.
- **Documentation Requirements**: Dependency setup guide for Linux, macOS, and Windows in bilingual READMEs.
- **Regression Risks**: Low.

### Phase 7: Packaging, Bilingual Documentation Sync & CI Release
- **Scope**: Finalize package distribution, establish automated multi-platform CI/CD testing, and synchronize English and Persian documentation. Set up GitHub Actions for PyInstaller standalone single-file binary builds (`f2m-linux-x64`, `f2m-windows-x64.exe`).
- **Non-Goals**: No new feature work.
- **Dependencies**: Phase 6.
- **Acceptance Criteria**: All CI checks pass across Linux, macOS, and Windows; documentation is 100% synchronized and verified; standalone single-file binary builds cleanly.
- **E2E Acceptance Criteria**: Download built standalone executable and verify execution of `f2m --version` and `f2m search --format json`.
- **Documentation Requirements**: Full bilingual audit and parity between `README.md` and `README.fa.md`.
- **Regression Risks**: Low.
- **E2E Acceptance Criteria**: Verified download dispatch using local test file and mock aria2c binary.
- **Documentation Requirements**: Dependency setup guide for Linux, macOS, and Windows.
- **Regression Risks**: Low.

---

## 10. Key Entities & Attributes

- **MediaPost**: Unique ID/URL, English Title, Persian Title, Year, Media Type (`Movie` vs `Series`), IMDb ID, Rating, Poster Image URL, Trailer URL, Seasons List, Versions List.
- **Season**: Season Number, Title, Version List.
- **MediaVersion**: Audio/Subtitle Type (`Dubbed`, `Hardsub`, `Original`), Title, Quality List.
- **Quality**: Resolution/Label (`1080p`, `720p`, `x265`, `10bit`), Encoder (`F2M`, `PSA`, etc.), Episode List.
- **Episode**: Episode Number, Download URL, Direct Filename, Label.
- **ConfigurationProfile**: Base URL, Mirrors List, Proxy Settings, Preferred Player, Download Directory, Search Sort Order, Color Mode.
