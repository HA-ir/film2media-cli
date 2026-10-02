# Implementation Plan: Phase 4 — CLI Argument & Output Modernization

**Branch**: `feat/phase-4-cli-modernization` | **Date**: 2026-10-02 | **Spec**: [specs/004-cli-modernization/spec.md](spec.md)

---

## Important Governance Notice
> **CRITICAL RULE**: **Only the repository owner may merge a PR.**  
> Automated agents, tools, or bots are strictly prohibited from merging pull requests, enabling auto-merge, or pushing directly to protected/default branches (`master`, `main`). Agents may prepare branches, commits, tests, documentation, and draft PRs, but MUST stop and wait for human review, verification, and explicit merge.

---

## 1. Summary

Phase 4 modernizes the command-line argument parsing and output presentation architecture of `film2media-cli`. In the legacy implementation, argument parsing is performed via manual `sys.argv[1:]` slicing, error messages and progress spinners leak indiscriminately into `stdout`, non-interactive query and extraction are unsupported, and exit codes are uniformly `0` regardless of operational failures.

Phase 4 introduces an explicit, robust CLI module in `f2m/cli/` that cleanly separates:
1. **Argument Parsing & Validation** (`f2m/cli/parser.py`): Typed tokenization supporting global options (`--json`, `--plain`, `--no-color`, `--config`), subcommands (`search`, `url`, `categories`, `config`, `test`, `help`, `version`), multi-word positional parameters, and mutual exclusivity enforcement.
2. **Output Formatters & Stream Isolation** (`f2m/cli/formatters.py`): Deterministic JSON serialization, plain-text TSV/line generation, structured JSON error rendering on `stderr`, and strict stream separation (data to `stdout`, diagnostics/spinners to `stderr`).
3. **Command Dispatch & POSIX Exit Code Runner** (`f2m/cli/runner.py`): Centralized dispatcher routing commands to core operations, mapping domain exceptions (`F2MConfigError`, `F2MNetworkError`, `F2MParseError`) and edge cases to standard POSIX exit codes (`0`, `1`, `2`, `3`, `4`, `5`, `6`, `130`).

All existing commands, bare interactive invocations (`f2m`), terminal menus, and Phase 1–3 regression test suites continue to operate with 100% backward compatibility.

---

## 2. Technical Context

- **Language/Version**: Python 3.8+ (cross-platform Linux, macOS, Windows).
- **Dependencies**: Zero new runtime dependencies (uses Python standard library `dataclasses`, `enum`, `json`, `sys`, `os`).
- **Target File Locations**:
  - `f2m/cli/__init__.py` (CLI package exports)
  - `f2m/cli/models.py` (CLI dataclasses & Enums: `OutputFormat`, `CliCommand`, `CliArgs`)
  - `f2m/cli/parser.py` (CLI tokenizer and argument validator)
  - `f2m/cli/formatters.py` (JSON, plain TSV, and human presentation formatters)
  - `f2m/cli/runner.py` (Command dispatcher and exception-to-exit-code runner)
  - `f2m.py` (Entry point updated to delegate to `f2m.cli.runner`)
  - `tests/unit/test_cli_args.py` (Unit tests for parser and flag validation)
  - `tests/unit/test_formatters.py` (Unit tests for JSON and plain formatters)
  - `tests/e2e/test_cli_e2e.py` (E2E subprocess execution and stream isolation tests)
- **Error Handling**: Converts parsing and domain exceptions into semantic POSIX exit codes (`2`, `3`, `4`, `5`, `6`, `130`) with structured error output.

---

## 3. Constitution Check

*GATE: All 10 mandatory principles from `.specify/memory/constitution.md` evaluated.*

| Principle | Compliance Status | Implementation Strategy |
|---|---|---|
| **I. Professional CLI UX** | **PASS** | Adds `--json` and `--plain` for headless scripting; enforces strict `stdout` (data) vs `stderr` (diagnostics/spinners) separation; supports `NO_COLOR` and `--no-color`. |
| **II. Reliability Over Aesthetics** | **PASS** | Implements standard POSIX exit codes (`0` to `6`, `130`); replaces ad-hoc `sys.argv` slicing with robust typed parsing; suppresses spinner contamination. |
| **III. Backward Compatibility** | **PASS** | Bare `f2m` retains the interactive welcome banner and menu; `f2m search <query>` without flags retains the interactive picker; existing config syntax remains identical. |
| **IV. Testability & Testing** | **PASS** | Multi-layered testing: parser unit tests, formatter tests, E2E subprocess CLI tests, and regression tests. |
| **V. Documentation as Implementation** | **PASS** | `README.md` and `README.fa.md` updated in exact bilingual parity to document `--json`, `--plain`, `--no-color`, subcommands, and exit codes. |
| **VI. Incremental Delivery** | **PASS** | Scoped strictly to Phase 4 (CLI parsing and output formatting). Exactly one reviewable PR. Zero leakage into Phase 5 (Rich/TUI) or Phase 6 (Downloader security). |
| **VII. PR Ownership & Merge Control** | **PASS** | Enforced: Human repository owner alone merges. Automated agents halt after opening the PR. |
| **VIII. End-to-End Acceptance Gate** | **PASS** | All 45 existing tests pass + new Phase 4 unit and E2E subprocess tests + manual verification. |
| **IX. Scope Discipline** | **PASS** | Standard library only; zero external CLI dependencies added; zero UI redesign (deferred to Phase 5). |
| **X. Honest Claims** | **PASS** | Every claim verified via automated subprocess execution and JSON schema validation. |

---

## 4. Existing Architecture Inspection & Modernization Strategy

### 4.1 Current Architecture Analysis
In `f2m.py`:
- `argv = [a for a in sys.argv[1:] if a.strip()]`
- If `argv` is empty: enters `banner()`, `run_interactive(main_menu)`.
- If `argv` is not empty: passes to `cli(argv)` which tests `cmd = argv[0].lower()`:
  - `help` / `-h` -> prints `USAGE`.
  - `search` -> `run_interactive(search_flow, " ".join(argv[1:]) or None)`.
  - `url` -> `run_interactive(post_flow, argv[1].strip())`.
  - `categories` -> `run_interactive(categories_flow)`.
  - `config` -> `config set` or dump.
  - `test` -> `test_connection()`.
- Limitations:
  - No global flag handling (`--json` or `--plain` before subcommand fails).
  - No non-interactive search or URL link extraction.
  - `ok()`, `info()`, `warn()`, `err()`, and `Spinner` print directly to `stdout`.
  - Exit codes are `0` even on invalid command or network error.

### 4.2 Safe Modernization Strategy
The core business logic (`f2m/core/models.py`, `f2m/core/config.py`, `f2m/core/scraper.py`, `f2m/net/client.py`) remains 100% untouched.
We encapsulate CLI concerns into a dedicated package:
```text
f2m/cli/
├── __init__.py
├── models.py      # OutputFormat, CliCommand, CliArgs, JsonErrorPayload
├── parser.py      # Scans global flags, extracts subcommands, validates mutual exclusivity
├── formatters.py  # Formats SearchResult, MediaPost, Config, errors to JSON or plain TSV
└── runner.py      # Dispatches CliArgs to operations, isolates streams, sets POSIX exit codes
```
`f2m.py` becomes a thin entry point that initializes `f2m.cli.runner.run_cli(sys.argv[1:])` while preserving existing interactive flow functions.

---

## 5. Target Architecture & Module Specifications

```text
film2media-cli/
├── f2m/
│   ├── core/                      # Core business logic (Phases 2 & 3 - untouched)
│   │   ├── models.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── scraper.py
│   ├── net/                       # Network transport (Phase 3 - untouched)
│   │   ├── __init__.py
│   │   └── client.py
│   └── cli/                       # NEW: Phase 4 CLI Modernization
│       ├── __init__.py            # Public exports: parse_args, run_cli
│       ├── models.py              # OutputFormat, CliCommand, CliArgs, JsonErrorPayload
│       ├── parser.py              # Tokenizer, argument extraction, mutual exclusivity check
│       ├── formatters.py          # JsonFormatter, PlainFormatter, stream separation helpers
│       └── runner.py              # Command dispatcher & exit code orchestrator
├── f2m.py                         # Root entry point delegating to f2m.cli.runner
├── pyproject.toml
├── tests/
│   ├── unit/
│   │   ├── test_cli_args.py       # NEW: Parser & flag extraction unit tests
│   │   ├── test_formatters.py     # NEW: JSON & Plain formatters unit tests
│   │   ├── test_scraper.py
│   │   ├── test_client.py
│   │   └── ...
│   └── e2e/
│       ├── test_cli_e2e.py        # NEW: E2E subprocess CLI execution & isolation tests
│       └── ...
├── README.md
└── README.fa.md
```

---

## 6. Implementation Sequence & Detailed Tasks

### Task 1: CLI Data Models (`f2m/cli/models.py`)
- Define `OutputFormat` enum (`HUMAN`, `JSON`, `PLAIN`).
- Define `CliCommand` enum (`MENU`, `SEARCH`, `URL`, `CATEGORIES`, `CONFIG`, `TEST`, `HELP`, `VERSION`).
- Define `ConfigAction` enum (`SHOW`, `GET`, `SET`).
- Define `CliArgs` dataclass holding parsed command, options, positional parameters, and flags.
- Define `JsonErrorPayload` dataclass with `to_dict()` serialization.

### Task 2: CLI Argument Parser (`f2m/cli/parser.py`)
- Implement `parse_args(argv: list[str]) -> CliArgs`:
  - Handle bare invocation: return `CliArgs(command=CliCommand.MENU)`.
  - Extract global flags anywhere in `argv` (`--json`, `--plain`, `--no-color`, `--config <path>`).
  - Validate mutual exclusivity: if both `--json` and `--plain` are specified, raise `F2MCliError("Cannot combine --json and --plain", exit_code=2)`.
  - Extract primary subcommand with aliases (`search`/`s`, `categories`/`cat`/`c`, `config`/`cfg`, `test`/`t`, `help`/`-h`/`--help`, `version`/`-V`/`--version`).
  - Collect remaining positional arguments:
    - Join multiple tokens for `search` into a single query string.
    - Extract `config get <key>` vs `config set <key> <val>` vs `config`.
  - Enforce missing argument validation:
    - `url` without URL -> exit code `2`.
    - `search` without query in non-interactive mode -> exit code `2`.
    - `config get` without key -> exit code `2`.
    - `config set` without key or value -> exit code `2`.
  - Enforce unrecognized command validation -> exit code `2`.

### Task 3: Output Formatters (`f2m/cli/formatters.py`)
- Implement `JsonFormatter`:
  - `format_search(results: list[SearchResult]) -> str`
  - `format_post(post: MediaPost) -> str`
  - `format_categories(sections: list, genres: dict) -> str`
  - `format_config(profile: ConfigurationProfile) -> str`
  - `format_config_get(key: str, val: Any) -> str`
  - `format_config_set(key: str, val: Any, file_path: str) -> str`
  - `format_test(reachable: bool, base_url: str, final_host: str, sections: int, movie_genres: int, series_genres: int, error: str | None) -> str`
  - `format_error(error_code: str, message: str, exit_code: int) -> str`
- Implement `PlainFormatter`:
  - `format_search(results: list[SearchResult]) -> str` (TSV: `<kind>\t<title>\t<year>\t<rating>\t<url>`)
  - `format_post(post: MediaPost) -> str` (Newline-separated direct download links)
  - `format_categories(sections: list, genres: dict) -> str` (TSV: `<type>\t<name>\t<url>`)
  - `format_config(profile: ConfigurationProfile) -> str` (`key=value` lines)
  - `format_config_get(val: Any) -> str` (Raw value with trailing newline)
  - `format_config_set(key: str, val: Any) -> str` (`OK: <key>=<val>`)
  - `format_test(ok: bool, base_url: str, target_or_err: str) -> str`
- Stream Isolation Utilities:
  - Route data output to `sys.stdout`.
  - Route diagnostics, warnings, and errors to `sys.stderr`.
  - Update `Spinner` to check `OutputFormat` and `sys.stderr.isatty()`: completely inert in `--json` and `--plain` modes.

### Task 4: Command Dispatch & Runner (`f2m/cli/runner.py`)
- Implement `run_cli(argv: list[str]) -> int`:
  - Call `parse_args(argv)`.
  - Dispatch to operation handlers (`handle_search`, `handle_url`, `handle_categories`, `handle_config`, `handle_test`, `handle_help`, `handle_version`, `handle_menu`).
  - In non-interactive mode (`--json` or `--plain`): execute operation without launching interactive screens (`Screen.enter()`).
  - In default interactive mode: preserve legacy `run_interactive()` and menu flows.
  - Top-level exception handling:
    - `F2MConfigError` -> exit code `3`.
    - `F2MNetworkError` -> exit code `4`.
    - `F2MParseError` -> exit code `5`.
    - `F2MCliError` (invalid args) -> exit code `2`.
    - `KeyboardInterrupt` -> exit code `130`.
    - Unhandled exceptions -> exit code `1`.
  - Emit structured JSON error on `stderr` if format is `JSON`.
  - Emit clean diagnostic error on `stderr` if format is `HUMAN` or `PLAIN`.

### Task 5: Integration in `f2m.py`
- Update `f2m.py`:
  - Delegate `cli(argv)` and `main()` to `f2m.cli.runner.run_cli(argv)`.
  - Update `Spinner` to run inert in non-interactive modes and write only to `sys.stderr`.
  - Ensure `ok()`, `info()`, `warn()`, `err()` write to `sys.stderr` when in non-interactive modes.
  - Preserve all existing interactive menu and action helper functions (`movie_flow`, `series_flow`, `do_download`, `do_stream`, `copy_links`).

### Task 6: Unit Test Suites
- Create `tests/unit/test_cli_args.py`:
  - Test bare invocation defaults to `CliCommand.MENU`.
  - Test global flag placement before and after command.
  - Test mutual exclusivity rejection of `--json` and `--plain` with exit code `2`.
  - Test multi-token query parsing in `search`.
  - Test missing argument validation for `url`, `config get`, `config set`.
  - Test alias normalization (`s`, `cat`, `c`, `cfg`, `t`, `h`, `v`).
- Create `tests/unit/test_formatters.py`:
  - Test `JsonFormatter` with mock `SearchResult`, `MediaPost`, `ConfigurationProfile`.
  - Test `PlainFormatter` TSV and link list generation.
  - Test `JsonErrorPayload` serialization.

### Task 7: E2E Subprocess Test Suite (`tests/e2e/test_cli_e2e.py`)
- Implement offline deterministic tests executing `python3 f2m.py` via `subprocess.run`:
  - `test_e2e_cli_json_search`: Assert `stdout` parses with `json.loads()` and exit code is `0`.
  - `test_e2e_cli_json_empty_search`: Assert `stdout` is `[]` and exit code is `6`.
  - `test_e2e_cli_plain_url`: Assert `stdout` contains direct media URLs and exit code is `0`.
  - `test_e2e_cli_config_json_and_plain`: Assert `config --json` and `config get base_url --plain`.
  - `test_e2e_cli_mutual_exclusivity`: Assert exit code `2` on `--json --plain`.
  - `test_e2e_cli_stream_isolation`: Assert zero spinner or progress text on `stdout`.
  - `test_e2e_cli_exit_codes`: Test codes `0`, `2`, `3`, `4`, `5`, `6`, `130`.
  - `test_e2e_cli_backward_compatibility`: Test bare `f2m --help`, `f2m config`, `f2m test`.

### Task 8: Documentation Updates (`README.md` & `README.fa.md`)
- Document modern CLI options (`--json`, `--plain`, `--no-color`, `--config`).
- Document subcommands (`search`, `url`, `categories`, `config`, `test`).
- Document Unix pipeline examples (`f2m search ... --json | jq .`, `f2m url ... --plain | aria2c -i -`).
- Document exit codes table.
- Maintain 100% bilingual parity between English and Persian.

---

## 7. Verification Gates

Before concluding Phase 4 and preparing the PR, all 8 verification gates must pass:
1. **Gate 1 — Unit Tests**: `pytest tests/unit/test_cli_args.py tests/unit/test_formatters.py` passes 100%.
2. **Gate 2 — Regression Invariant**: `pytest tests/unit/test_legacy_baseline.py tests/unit/test_models.py tests/unit/test_config.py tests/unit/test_config_migration.py tests/unit/test_exceptions.py tests/unit/test_scraper.py tests/unit/test_client.py` passes 100% (all 37 prior unit tests).
3. **Gate 3 — E2E Suites**: `pytest tests/e2e/` passes 100% (including all prior and new CLI E2E tests).
4. **Gate 4 — Syntax & Compilation**: `python3 -m py_compile f2m.py f2m/__init__.py f2m/core/*.py f2m/net/*.py f2m/cli/*.py tests/**/*.py` succeeds with zero errors.
5. **Gate 5 — Static Analysis & Linting**: `ruff check f2m/ tests/` succeeds cleanly.
6. **Gate 6 — Documentation Parity**: `README.md` and `README.fa.md` have identical content updates.
7. **Gate 7 — Manual Verification**:
   - `python3 f2m.py --help`
   - `python3 f2m.py config --json`
   - `python3 f2m.py config get base_url --plain`
   - `python3 f2m.py test --json`
8. **Gate 8 — Scope Review**: Confirm zero UI changes (no `rich`), zero downloader modifications (no `sudo` touch), clean git diff on `feat/phase-4-cli-modernization`, halt and wait for human review and merge.
