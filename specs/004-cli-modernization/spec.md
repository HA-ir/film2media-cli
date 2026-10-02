# Feature Specification: Phase 4 — CLI Argument & Output Modernization

**Feature Branch**: `feat/phase-4-cli-modernization`

**Created**: 2026-10-02

**Status**: Draft (Clarified)

**Input**: User description: "Phase 4 — CLI Argument & Output Modernization: Modernize the CLI interface with explicit subcommands, POSIX exit codes, deterministic stdout/stderr separation, and machine-readable --json and --plain output modes while preserving 100% backward compatibility with existing interactive workflows."

---

## 1. Executive Summary & Purpose

Phase 1 established automated test infrastructure and golden fixtures. Phase 2 delivered typed domain entities and an XDG-compliant configuration engine. Phase 3 delivered a resilient BeautifulSoup4 DOM scraper and a retry-enabled HTTP client with mirror failover.

Phase 4 addresses the command-line interface and automation boundary: **CLI Argument & Output Modernization**. In the legacy implementation (`f2m.py`), argument parsing is performed via ad-hoc list slicing (`sys.argv[1:]`), error reporting is routed indiscriminately to `stdout` alongside data, non-interactive execution is impossible for search and URL inspection, process exit codes are uniformly `0` even when operations fail, and output cannot be parsed programmatically without scraping colored ANSI text.

Phase 4 introduces an explicit, robust argument parsing engine and deterministic output formatting:
1. **Explicit Command Structure**: Clear subcommand boundaries (`search`, `url`, `categories`, `config`, `test`, `help`, `version`) while preserving all legacy shorthand invocations and the default bare interactive menu.
2. **Machine-Readable `--json` Output**: Clean, valid, deterministic JSON streams on `stdout` without spinner or ANSI contamination, conforming to domain entity serialization contracts.
3. **Streamlined `--plain` Output**: Unadorned, non-colored, newline- and tab-delimited text on `stdout` tailored for Unix pipelines (`xargs`, `awk`, `cut`, `grep`).
4. **Deterministic Stream Separation**: Strict routing of data payloads to `stdout`, and diagnostics, progress spinners, prompts, and status messages to `stderr`.
5. **Standardized POSIX Exit Codes**: Granular exit codes distinguishing success (`0`), runtime failure (`1`), invalid arguments (`2`), configuration errors (`3`), network failures (`4`), parse errors (`5`), resource not found (`6`), and user cancellation (`130`).
6. **100% Backward Compatibility**: Interactive menus, existing command signatures, default colored terminal formatting, and legacy workflow semantics remain completely operational when neither `--json` nor `--plain` is passed.

---

## 2. Clarifications & Architectural Decisions

### Session 2026-10-02

#### 1. Command & Subcommand Architecture
- **Command Grammar**:
  ```text
  f2m [GLOBAL_OPTIONS] [COMMAND] [COMMAND_OPTIONS] [ARGS...]
  ```
- **Global Options**:
  - `--json`: Output machine-readable JSON on `stdout`. Automatically enforces non-interactive mode.
  - `--plain`: Output unformatted, tab- or newline-delimited text on `stdout`. Automatically enforces non-interactive mode.
  - `--no-color`: Disable all ANSI terminal styling (automatically implied if `NO_COLOR` is in `os.environ` or if `stdout` is not a TTY).
  - `--config <path>`: Explicit configuration file path override (takes precedence over default XDG resolution and `F2M_CONFIG`).
  - `--help`, `-h`: Display command-line usage and exit with code `0`.
  - `--version`, `-V`: Display application version string (`f2m 1.1.0`) and exit with code `0`.
- **Subcommand Specifications**:
  1. **Bare Invocation (`f2m`)**:
     - *Behavior*: If no command arguments are provided on `sys.argv`, enters `banner()` and `main_menu()` interactive flow.
     - *Exit Code*: `0` on clean exit; `130` on `SIGINT`.
  2. **`search` (`s`)**:
     - *Signature*: `f2m search <query...>`
     - *Positional Arguments*: `<query>` (one or more tokens). Multiple tokens (e.g., `f2m search breaking bad`) are joined with spaces (`"breaking bad"`), preserving legacy convenience.
     - *Default Mode*: Launches interactive search result picker (`search_flow`).
     - *`--json` Mode*: Queries Film2Media, outputs JSON array of `SearchResult.to_dict()` objects to `stdout`, and exits `0` (or `6` if empty).
     - *`--plain` Mode*: Outputs tab-delimited rows (`<kind>\t<title>\t<year>\t<rating>\t<url>`) to `stdout`, and exits `0` (or `6` if empty).
     - *Missing Argument*: In interactive mode, prompts `query: `; in `--json`/`--plain` mode, prints error to `stderr` and exits `2`.
  3. **`url`**:
     - *Signature*: `f2m url <post-url>`
     - *Positional Arguments*: `<post-url>` (string, required).
     - *Default Mode*: Fetches post and launches interactive version/quality/episode selection menu (`post_flow`).
     - *`--json` Mode*: Fetches post, outputs complete `MediaPost.to_dict()` structure to `stdout`, and exits `0`.
     - *`--plain` Mode*: Fetches post, outputs all available direct media download URLs one per line to `stdout`, and exits `0`.
     - *Missing Argument*: Prints usage error to `stderr` and exits `2`.
  4. **`categories` (`cat`, `c`)**:
     - *Signature*: `f2m categories`
     - *Default Mode*: Launches interactive categories and genres navigation menu (`categories_flow`).
     - *`--json` Mode*: Fetches homepage/categories, outputs structured JSON taxonomy (`{"sections": [...], "genres": {"movie": [...], "series": [...]}}`) to `stdout`, and exits `0`.
     - *`--plain` Mode*: Outputs tab-delimited taxonomy rows (`<type>\t<name>\t<url>`) where `<type>` is `section`, `movie_genre`, or `series_genre`, and exits `0`.
  5. **`config` (`cfg`)**:
     - *Signatures*:
       - `f2m config`: Lists all configuration keys and values.
         - *Default*: Formatted, colored key-value table on `stdout`.
         - *`--json`*: JSON object mapping all active configuration keys to values.
         - *`--plain`*: `key=value` lines, one per line.
       - `f2m config get <key>`:
         - *Default*: Formatted key-value display on `stdout`.
         - *`--json`*: `{"key": "<key>", "value": "<val>"}`.
         - *`--plain`*: Raw value of the key followed by a newline (suitable for `$(f2m config get base_url --plain)`).
       - `f2m config set <key> <value...>`:
         - *Default*: Updates and persists key, outputs green confirmation `✔ <key> saved`.
         - *`--json`*: Outputs `{"success": true, "key": "<key>", "value": "<val>", "file_path": "<path>"}`.
         - *`--plain`*: Outputs `OK: <key>=<value>`.
     - *Validation*: Rejection of invalid keys raises `F2MConfigError`, outputs error to `stderr`, and exits with code `3`.
  6. **`test` (`t`)**:
     - *Signature*: `f2m test`
     - *Behavior*: Tests reachability of `base_url` and parses homepage categories.
     - *Default*: Colored test progress, base URL, final redirected host, and category counts on `stdout`.
     - *`--json`*: Outputs `{"reachable": bool, "base_url": str, "final_host": str, "sections_count": int, "movie_genres_count": int, "series_genres_count": int, "error": str | None}` to `stdout`.
     - *`--plain`*: Outputs `OK\t<base_url>\t<final_host>` on success, or `FAIL\t<base_url>\t<error>` on failure.
     - *Exit Code*: `0` on reachable; `4` if network failure.
  7. **`help` (`-h`, `--help`)**:
     - *Signature*: `f2m help [command]`
     - *Behavior*: Outputs detailed usage text with available commands and options to `stdout`, exits with code `0`.
  8. **`version` (`-V`, `--version`)**:
     - *Signature*: `f2m version`
     - *Behavior*: Outputs `f2m 1.1.0` to `stdout`, exits with code `0`.

#### 2. Flag Combinations & Conflict Matrix

| Mode Combination | Interaction & Precedence | Exit Code | Stream Behavior |
|---|---|---|---|
| `--json` | Valid non-interactive mode | `0` (or operational error) | Valid JSON on `stdout`; diagnostics/logs on `stderr`. |
| `--plain` | Valid non-interactive mode | `0` (or operational error) | Plain TSV/lines on `stdout`; diagnostics/logs on `stderr`. |
| `--json` + `--plain` | Mutually exclusive flag conflict | `2` (Invalid Arguments) | Error message on `stderr`; `stdout` remains empty. |
| `--no-color` | Disables ANSI coloring in default mode | Dependent on command | Colored escape sequences stripped from all output. |
| `--json` on success | Output generated successfully | `0` | Clean JSON payload on `stdout`; empty/diagnostic `stderr`. |
| `--json` on error | Operation encountered failure | `1` to `5` | `stdout` is completely empty; JSON error object on `stderr`. |
| `--json` on no results | Search returned 0 matches | `6` (Not Found) | `[]` on `stdout`; diagnostic note on `stderr`. |
| `--plain` on success | Output generated successfully | `0` | Unadorned text on `stdout`; empty/diagnostic `stderr`. |
| `--plain` on error | Operation encountered failure | `1` to `5` | `stdout` is completely empty; plain error text on `stderr`. |
| `--plain` on no results | Search returned 0 matches | `6` (Not Found) | `stdout` is completely empty; diagnostic note on `stderr`. |
| Default (human) on success | Standard CLI or interactive flow | `0` | Human-readable colored text or interactive menus. |
| Default (human) on error | Standard operational error | `1` to `5` | Clean `✖ <error>` message on `stderr`, no stack trace. |

#### 3. Deterministic Output Schemas

- **Search Results (`--json`)**:
  ```json
  [
    {
      "kind": "movie",
      "title": "Inception 2010",
      "title_fa": "اینسپشن",
      "year": "2010",
      "rating": "8.8",
      "url": "https://www.myf2ms.top/movies/inception-2010/",
      "image": "https://www.myf2ms.top/poster.jpg",
      "meta": "دوبله فارسی"
    }
  ]
  ```
- **Post Inspection (`--json`)**:
  Matches `MediaPost.to_dict()`:
  ```json
  {
    "title": "Inception 2010",
    "url": "https://www.myf2ms.top/movies/inception-2010/",
    "is_series": false,
    "rating": "8.8",
    "imdb_id": "tt1375666",
    "year": "2010",
    "trailer": "https://trailer.mp4",
    "versions": [
      {
        "key": "dub",
        "title": "نسخه دوبله فارسی",
        "qualities": [
          {
            "label": "1080p BluRay",
            "encoder": "F2M",
            "episodes": [
              {
                "num": 1,
                "label": "قسمت 1",
                "url": "https://dl.example.com/movie.1080p.mkv"
              }
            ]
          }
        ]
      }
    ],
    "seasons": []
  }
  ```
- **Categories Inspection (`--json`)**:
  ```json
  {
    "sections": [
      {"name": "Movies", "url": "https://www.myf2ms.top/movies/"},
      {"name": "Series", "url": "https://www.myf2ms.top/series/"}
    ],
    "genres": {
      "movie": [{"name": "Action", "url": "https://www.myf2ms.top/genre/action/"}],
      "series": [{"name": "Drama", "url": "https://www.myf2ms.top/series-genre/drama/"}]
    }
  }
  ```
- **Configuration Dump (`--json`)**:
  Matches `ConfigurationProfile.to_dict()`:
  ```json
  {
    "base_url": "https://www.myf2ms.top",
    "mirrors": ["https://mirror1.com", "https://mirror2.com"],
    "proxy": "",
    "player": "auto",
    "download_dir": "~/Downloads/f2m",
    "search_sort": "date",
    "user_agent": "Mozilla/5.0 ..."
  }
  ```
- **Connectivity Diagnostic (`--json`)**:
  ```json
  {
    "reachable": true,
    "base_url": "https://www.myf2ms.top",
    "final_host": "www.myf2ms.top",
    "sections_count": 5,
    "movie_genres_count": 22,
    "series_genres_count": 18,
    "error": null
  }
  ```
- **Structured Error Schema (`--json` on `stderr`)**:
  ```json
  {
    "error": true,
    "code": "CONFIG_ERROR",
    "message": "Invalid configuration key 'invalid_key'. Supported keys: base_url, mirrors, proxy, player, download_dir, search_sort, user_agent",
    "exit_code": 3
  }
  ```

#### 4. Exit Code Mapping Matrix

| Exit Code | Identifier | Triggering Condition | Exception / Source |
|---|---|---|---|
| `0` | `SUCCESS` | Successful execution of any command. | Normal return |
| `1` | `RUNTIME_ERROR` | Generic operational or internal failure. | Unhandled `F2MError` |
| `2` | `INVALID_ARGUMENT` | Unknown command, missing positional argument, conflicting `--json` and `--plain`, or bad flag syntax. | Argument parser validation |
| `3` | `CONFIG_ERROR` | Unknown config key, bad value type, unwritable config file, corrupt INI syntax. | `F2MConfigError` |
| `4` | `NETWORK_ERROR` | Connection refused, DNS failure, timeout, HTTP 5xx/429 with all mirrors exhausted. | `F2MNetworkError` |
| `5` | `PARSE_ERROR` | Malformed or corrupt HTML markup where required metadata cannot be extracted. | `F2MParseError` |
| `6` | `NOT_FOUND` | Search returned 0 matching results, or post URL returned HTTP 404. | Search / URL resolution |
| `130` | `SIGINT` | Process interrupted by user via `Ctrl+C`. | `KeyboardInterrupt` |

#### 5. Deterministic Stream & Progress Separation
- **`Spinner` Architecture**:
  - The `Spinner` thread MUST write exclusively to `sys.stderr`.
  - The `Spinner` MUST be active ONLY IF:
    1. Neither `--json` nor `--plain` is present.
    2. `sys.stderr.isatty()` returns `True`.
  - Under `--json`, `--plain`, or redirected output, `Spinner.__enter__` returns immediately without starting a worker thread, ensuring zero carriage returns (`\r`) or frame artifacts leak to streams.
- **Diagnostic Helper Routing**:
  - `ok(msg)`, `info(msg)`, `warn(msg)`, and `err(msg)` MUST write to `sys.stderr` when executing subcommands that output data to `stdout`.
  - In default interactive mode where `stdout` is the terminal canvas, messages may be rendered to `stdout` for visual flow, but whenever data output is redirected or in machine modes, diagnostics belong strictly on `stderr`.

---

## 3. User Scenarios & Testing *(mandatory)*

### User Story 1 - Scriptable Search with Machine-Readable JSON (Priority: P1)
As a developer or automation engineer, I want to query Film2Media using `f2m search <query> --json` so that I can pipe structured media search results directly into tools like `jq`, Python, or shell scripts without terminal screens, prompts, or ANSI color codes breaking JSON parsers.

**Why this priority**: Essential requirement for CLI modernization and automation pipelines. Solves the limitation where `f2m search` was purely interactive.

**Independent Test**: Execute `f2m search "Inception" --json` against offline recorded search fixtures. Verify that `stdout` parses cleanly with `json.loads()` as a JSON array of `SearchResult` objects and exit code is `0`.

**Acceptance Scenarios**:
1. **Given** a valid search query and the `--json` flag, **When** executing `f2m search "Inception" --json`, **Then** the process completes non-interactively, writes a valid JSON array of search result objects to `stdout`, writes any diagnostic notices to `stderr`, and exits with code `0`.
2. **Given** a search query yielding no matches, **When** executing `f2m search "NonexistentTitleXYZ" --json`, **Then** `stdout` emits an empty JSON array `[]`, `stderr` receives a diagnostic message, and the command exits with code `6` (Resource Not Found).
3. **Given** an invalid flag combination such as `--json` and `--plain`, **When** executing `f2m search "Inception" --json --plain`, **Then** the command terminates immediately without network activity, emits a validation error to `stderr`, and exits with code `2`.

---

### User Story 2 - Unix Pipeline Integration with Plain Output (Priority: P2)
As a command-line power user, I want to extract direct download links or search summaries using `f2m --plain` so that I can feed URLs directly into `aria2c`, `curl`, `xargs`, or text processing utilities without manual copying.

**Why this priority**: Empowers command-line composability and headless batch operations in standard Unix shell workflows.

**Independent Test**: Execute `f2m url <post-url> --plain` against a movie post fixture. Verify that `stdout` outputs clean newline-separated URLs without headers, box-drawing characters, or ANSI escape sequences.

**Acceptance Scenarios**:
1. **Given** a valid post URL and the `--plain` flag, **When** executing `f2m url <post-url> --plain`, **Then** `stdout` receives direct media download links formatted one per line, and exits with code `0`.
2. **Given** a search query and the `--plain` flag, **When** executing `f2m search "Inception" --plain`, **Then** `stdout` receives tab-separated lines representing each result (`<kind>\t<title>\t<year>\t<rating>\t<url>`), and exits with code `0`.
3. **Given** the `--plain` flag is active, **When** executing any command, **Then** all status messages, warnings, and error diagnostics are directed to `stderr`.

---

### User Story 3 - Programmatic Configuration Inspection & Modification (Priority: P3)
As a systems administrator or user configuring automated setups, I want to inspect and edit configuration parameters through structured subcommands (`f2m config get <key>`, `f2m config set <key> <value>`) with explicit exit codes and JSON support, so that automation scripts can reliably verify and configure the client.

**Why this priority**: Replaces the limited legacy `f2m config` dump and interactive-only prompts with scriptable, predictable configuration management.

**Independent Test**: Execute `f2m config get base_url --plain` and verify it prints the raw URL string. Execute `f2m config set proxy "http://127.0.0.1:8080" --json` and verify the JSON confirmation object and exit code.

**Acceptance Scenarios**:
1. **Given** an existing configuration key, **When** running `f2m config get base_url --plain`, **Then** the raw value is printed to `stdout` ending in a newline with exit code `0`.
2. **Given** a configuration inspection in JSON mode, **When** running `f2m config --json`, **Then** a JSON object representing all configuration keys and values is written to `stdout`.
3. **Given** an invalid key or value, **When** running `f2m config set invalid_key "some_val"`, **Then** `stderr` receives a clear configuration error message and the process exits with code `3`.

---

### User Story 4 - Backward-Compatible Interactive Workflows (Priority: P4)
As an existing user accustomed to the terminal UI, I want running `f2m` or `f2m search "Inception"` without flags to open the full interactive menu and selection screens exactly as before, so that my everyday interactive experience is preserved without disruption.

**Why this priority**: Upholds Constitution Principle III (Backward Compatibility) and guarantees zero regression for human terminal users.

**Independent Test**: Invoke `f2m` with no arguments or `f2m search <query>` in a TTY environment without `--json`/`--plain`. Confirm that terminal alternate-screen and interactive menus operate identically to Phase 3.

**Acceptance Scenarios**:
1. **Given** no command-line arguments are provided, **When** running `f2m`, **Then** the interactive welcome banner and main navigation menu are displayed.
2. **Given** a search command without formatting flags in an interactive terminal, **When** running `f2m search "Inception"`, **Then** the interactive search results picker opens, allowing menu-driven version, quality, and episode selection.
3. **Given** the user presses `Ctrl+C` at any interactive prompt, **When** interrupted, **Then** the process restores the terminal screen, prints a clean cancellation note to `stderr`, and exits with POSIX code `130` without leaking Python tracebacks.

---

### Edge Cases
- **Non-TTY execution in default mode**: When `stdout` is redirected to a pipe or file (e.g., `f2m search "test" > out.txt`) without explicit flags, the client MUST disable ANSI color codes (`C.ENABLED = False`) to prevent ANSI escapes in files.
- **Empty search results**: When a search returns 0 results in `--json` mode, it emits an empty array `[]` and returns exit code `6`; in `--plain` mode, it outputs nothing on `stdout`, a warning on `stderr`, and exits with code `6`.
- **Network timeout during JSON execution**: When an HTTP request fails during `f2m search "test" --json`, `stdout` MUST NOT receive partial JSON or text; `stderr` receives a structured JSON error object and the process exits with code `4`.
- **Malformed URL passed to `f2m url`**: If an unparseable or non-HTTP URL is passed, validation fails immediately with exit code `2` on invalid argument, or `5` if upstream HTML is malformed.
- **Interactive interrupt (`SIGINT`)**: Trapped cleanly across all modes with exit code `130`.

---

## 4. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an explicit CLI argument parser supporting the primary subcommands: `search`, `url`, `categories`, `config`, `test`, `help`, and `version`.
- **FR-002**: System MUST preserve bare invocation (`f2m`) as the entry point to the interactive terminal main menu when no command arguments are supplied.
- **FR-003**: System MUST support the `--json` flag (both globally and per-subcommand) to output deterministic, unadorned JSON payloads to `stdout`.
- **FR-004**: System MUST guarantee that when `--json` is active, `stdout` is never contaminated with progress spinners, status icons, greeting messages, or ANSI escape codes.
- **FR-005**: System MUST support the `--plain` flag (both globally and per-subcommand) to output unformatted, uncolored, tab-separated or newline-separated data to `stdout`.
- **FR-006**: System MUST enforce mutual exclusivity between `--json` and `--plain`, terminating with exit code `2` if both flags are provided simultaneously.
- **FR-007**: System MUST automatically bypass all interactive prompts, menus, and alternate-screen allocations whenever `--json` or `--plain` is provided.
- **FR-008**: System MUST route all informational messages, warnings, errors, and progress indicators exclusively to `stderr` in non-interactive modes.
- **FR-009**: System MUST support `f2m config get <key>` to retrieve individual configuration values.
- **FR-010**: System MUST support `f2m config set <key> <value>` with validation, atomic write persistence, and appropriate exit codes.
- **FR-011**: System MUST emit standardized POSIX exit codes: `0` (Success), `1` (Runtime Error), `2` (Invalid Arguments), `3` (Config Error), `4` (Network Error), `5` (Parse Error), `6` (Resource Not Found), and `130` (Interrupted).
- **FR-012**: System MUST format error diagnostics as a structured JSON object on `stderr` when an error occurs in `--json` mode, leaving `stdout` clean.
- **FR-013**: System MUST provide a comprehensive, formatted help screen on `f2m --help`, `f2m -h`, or `f2m help`.
- **FR-014**: System MUST output version information (`f2m <VERSION>`) on `f2m --version` or `f2m -V`.
- **FR-015**: System MUST preserve all existing domain entity contracts (`SearchResult`, `MediaPost`, `ConfigurationProfile`) and exception hierarchies (`F2MError`, `F2MConfigError`, `F2MNetworkError`, `F2MParseError`).
- **FR-016**: System MUST preserve all existing interactive menu choices, download triggers, streaming actions, and keyboard navigation when run in human-interactive mode.

---

## 5. Testing & Verification Matrix

The test strategy spans 4 complementary verification layers:

1. **Unit Tests (`tests/unit/test_cli_args.py`)**:
   - Argument parsing and tokenization across all subcommands (`search`, `url`, `categories`, `config`, `test`).
   - Flag extraction: global vs subcommand placement of `--json`, `--plain`, `--no-color`.
   - Mutual exclusivity detection: `--json` and `--plain` flag conflict validation.
   - Missing required argument validation (`url` without URL, `config set` without value).
2. **Formatter Tests (`tests/unit/test_formatters.py`)**:
   - JSON serialization of `SearchResult`, `MediaPost`, `ConfigurationProfile`, and categories taxonomy.
   - Plain-text TSV formatting of search results and newline-separated URL lists.
   - JSON error payload serialization on `stderr`.
3. **E2E Subprocess Tests (`tests/e2e/test_cli_e2e.py`)**:
   - `test_e2e_cli_json_search`: Invokes `f2m search "query" --json` via `subprocess.run`, verifies valid JSON on `stdout`, empty `stderr` (or clean diagnostics), and exit code `0`.
   - `test_e2e_cli_plain_url`: Invokes `f2m url <post-url> --plain`, verifies clean direct links on `stdout` and exit code `0`.
   - `test_e2e_cli_config_get_set`: Invokes `f2m config get base_url --plain` and `f2m config set proxy ... --json`, verifying roundtrip persistence and output format.
   - `test_e2e_cli_mutual_exclusivity`: Invokes `f2m search "query" --json --plain`, asserts exit code `2`, error on `stderr`, and empty `stdout`.
   - `test_e2e_cli_exit_codes`: Tests simulated network timeout (code `4`), malformed config (code `3`), and 0 results (code `6`).
   - `test_e2e_cli_stream_isolation`: Verifies that `stdout` receives zero carriage returns (`\r`), zero ANSI codes, and zero spinner text in `--json` mode.
4. **Regression Safety Net**:
   - All 45 existing unit and E2E tests from Phases 1, 2, and 3 continue to pass without modification.

---

## 6. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of `--json` command invocations produce valid JSON parsable by standard JSON parsers (`json.loads`, `jq`) with zero syntactic errors.
- **SC-002**: 100% of `--plain` command invocations contain zero ANSI color escape sequences and zero carriage returns from progress spinners.
- **SC-003**: In non-interactive mode (`--json` or `--plain`), commands execute to completion without ever hanging on stdin or requiring user keystrokes.
- **SC-004**: 100% of CLI failures yield the exact designated POSIX exit code from the exit code matrix rather than a generic `0` or unhandled traceback.
- **SC-005**: 100% of existing unit and regression tests from Phases 1, 2, and 3 continue to pass with zero regressions.
- **SC-006**: Interactive terminal workflows (`f2m`, `f2m search`, `f2m url`, `f2m categories`) maintain identical visual presentation and menu navigation when invoked without machine-readable flags.

---

## 7. Assumptions & Scope Exclusions

### Assumptions
- Python standard library (`argparse` or custom robust tokenizer) is sufficient to implement explicit subcommand routing without introducing external dependencies.
- Downstream automation consumers inspect process exit codes in addition to parsing `stdout`.
- When `--plain` is used on `f2m url <post-url>`, emitting all available direct download links sequentially matches standard pipeline expectations (`aria2c -i -`).

### Scope Exclusions
- **Terminal UI / RTL Redesign**: Introduction of the `rich` library, table rendering, bilingual Persian RTL shaping, and modern progress bars is strictly deferred to **Phase 5**.
- **Downloader & Player Security**: Removal of `sudo` invocations during package manager installation and download manager sandboxing is strictly deferred to **Phase 6**.
- **Packaging & CI/CD**: PyPI distribution packaging, entry points (`console_scripts`), and GitHub Actions CI pipelines remain strictly deferred to **Phase 7**.

---

## 8. Backward Compatibility Invariants

1. **Existing Command Invocations**:
   - `python f2m.py` -> Opens main interactive menu.
   - `python f2m.py search <query>` -> Opens interactive search results menu.
   - `python f2m.py url <url>` -> Opens interactive post menu.
   - `python f2m.py categories` -> Opens interactive categories menu.
   - `python f2m.py config` -> Displays formatted configuration keys.
   - `python f2m.py config set <key> <value>` -> Sets configuration key.
   - `python f2m.py test` -> Runs connectivity test.
   - `python f2m.py help` -> Shows usage help.
2. **Configuration Precedence**: Preserves the 5-tier precedence resolved in Phase 2: CLI Overrides > Environment Variables (`F2M_*`) > Local Config (`./f2m.conf`) > User XDG Config (`~/.config/f2m/config.ini`) > Defaults.
3. **Parser & Network Invariants**: All domain model mappings, BeautifulSoup DOM extraction routines, and resilient HTTP client retry/mirror policies from Phases 2 and 3 remain authoritative and unmodified.
