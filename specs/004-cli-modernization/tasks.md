# Tasks: Phase 4 — CLI Argument & Output Modernization

**Branch**: `feat/phase-4-cli-modernization`  
**Phase**: Phase 4 of 7  
**Input**: Approved specification from `specs/004-cli-modernization/spec.md`, architecture plan from `specs/004-cli-modernization/plan.md`, research from `specs/004-cli-modernization/research.md`, data model from `specs/004-cli-modernization/data-model.md`, and contracts from `specs/004-cli-modernization/contracts/cli-interface-contract.md`.  
**Governance**: **Only the repository owner may merge a PR.** Agents must never merge PRs.

---

## Phase Overview & Scope

- **Goal**: Modernize the CLI interface with explicit subcommands, POSIX exit codes, deterministic stdout/stderr separation, and machine-readable `--json` and `--plain` output modes while preserving 100% backward compatibility with existing interactive workflows.
- **Strict Scope Boundaries**:
  - Zero UI/TUI redesign (no `rich` rendering; deferred to Phase 5).
  - Zero downloader/player changes or `sudo` removal (deferred to Phase 6).
  - Zero packaging/CI/release automation (deferred to Phase 7).
  - All existing commands (`f2m`, `f2m search`, `f2m url`, `f2m categories`, `f2m test`, `f2m config`) and all Phase 1–3 tests (45 tests) MUST remain 100% passing.

---

## Task List

### Phase 1: Setup & Package Foundation

**Purpose**: Establish the CLI module structure and strongly-typed models without modifying core logic.

- [X] T001 Create CLI package directory `f2m/cli/` with `__init__.py` exporting public CLI runner interfaces
- [X] T002 [P] Implement CLI data models in `f2m/cli/models.py`: define `OutputFormat` enum (`HUMAN`, `JSON`, `PLAIN`), `CliCommand` enum (`MENU`, `SEARCH`, `URL`, `CATEGORIES`, `CONFIG`, `TEST`, `HELP`, `VERSION`), `ConfigAction` enum (`SHOW`, `GET`, `SET`), `CliArgs` dataclass, and `JsonErrorPayload` dataclass

---

### Phase 2: Foundational Infrastructure (Parser, Formatters & Stream Isolation)

**Purpose**: Core parsing, stream separation, and formatting engine that all CLI commands depend on.

- [X] T003 Implement typed argument tokenizer and validator in `f2m/cli/parser.py`: extract global flags (`--json`, `--plain`, `--no-color`, `--config`), enforce mutual exclusivity between `--json` and `--plain` (raising exit code 2), identify subcommands with aliases (`s`, `cat`, `c`, `cfg`, `t`, `h`, `v`), join multi-token search queries, and validate required arguments
- [X] T004 [P] Implement output formatters in `f2m/cli/formatters.py`: create `JsonFormatter` (serializing `SearchResult`, `MediaPost`, `ConfigurationProfile`, and categories taxonomy via domain `.to_dict()`) and `PlainFormatter` (generating unadorned TSV rows and newline-delimited direct links)
- [X] T005 [P] Implement stream isolation and progress guards in `f2m/cli/formatters.py`: implement `emit_stdout()`, `emit_stderr()`, and structured JSON error formatting on `stderr`
- [X] T006 Update `Spinner` in `f2m.py` (and export to `f2m/cli/formatters.py`): ensure spinner writes exclusively to `sys.stderr` and operates completely inert (zero output) when output format is `JSON` or `PLAIN` or when `sys.stderr` is not a TTY
- [X] T007 Implement command runner and POSIX exit code handler in `f2m/cli/runner.py`: orchestrate argument parsing, dispatch to handlers, catch domain exceptions (`F2MConfigError` -> 3, `F2MNetworkError` -> 4, `F2MParseError` -> 5, `F2MCliError` -> 2, `KeyboardInterrupt` -> 130), and format errors appropriately on `stderr`
- [X] T008 [P] Implement parser unit tests in `tests/unit/test_cli_args.py`: test bare invocation default, global flag placement before/after command, mutual exclusivity conflict, multi-token query parsing, missing argument errors, and alias resolution
- [X] T009 [P] Implement formatter unit tests in `tests/unit/test_formatters.py`: test JSON serialization, plain TSV generation, newline direct URLs, and `JsonErrorPayload` formatting on `stderr`

---

### Phase 3: User Story 1 - Machine-Readable JSON Output (`--json`) [US1] 🎯 MVP

**Goal**: Deliver clean, unadorned, machine-readable JSON on `stdout` for all queries and operations without spinner or ANSI contamination.

**Independent Test**: Run `python3 f2m.py search "Inception" --json | jq .` against search fixtures and verify clean parse with exit code `0`.

- [X] T010 [US1] Implement non-interactive JSON search handler in `f2m/cli/runner.py`: query Film2Media, serialize results via `JsonFormatter.format_search()`, stream valid JSON array to `stdout`, and return exit code `0` (or `6` with `[]` if results are empty)
- [X] T011 [US1] Implement non-interactive JSON URL inspection handler in `f2m/cli/runner.py`: fetch post via scraper, serialize full `MediaPost` structure to `stdout`, and return exit code `0`
- [X] T012 [US1] Implement non-interactive JSON categories handler in `f2m/cli/runner.py`: fetch categories taxonomy, serialize sections and genres to `stdout`, and return exit code `0`
- [X] T013 [US1] Implement non-interactive JSON connectivity test handler in `f2m/cli/runner.py`: run diagnostic test, serialize reachable status, base URL, redirected host, and category counts to `stdout`, and return exit code `0` (or `4` on failure)
- [X] T014 [US1] Implement structured error handling in `f2m/cli/runner.py` for `--json` mode: guarantee `stdout` is empty on failure while `stderr` receives valid JSON error payload (`{"error": true, "code": "...", "message": "...", "exit_code": ...}`)
- [X] T015 [US1] Add unit test in `tests/unit/test_formatters.py` verifying that `--json` output contains zero ANSI color escape codes, zero carriage returns, and parses cleanly with standard `json.loads`

---

### Phase 4: User Story 2 - Unix Pipeline Integration (`--plain`) [US2]

**Goal**: Enable pipeline composability by streaming unformatted, tab-separated or newline-delimited text to `stdout`.

**Independent Test**: Run `python3 f2m.py url <post-url> --plain` and verify direct download links are printed one per line on `stdout`.

- [X] T016 [US2] Implement non-interactive plain search handler in `f2m/cli/runner.py`: output search results as TSV (`<kind>\t<title>\t<year>\t<rating>\t<url>`) to `stdout` with exit code `0` (or `6` with empty `stdout` if 0 results)
- [X] T017 [US2] Implement non-interactive plain URL handler in `f2m/cli/runner.py`: extract all available direct media download URLs from `MediaPost` and print one per line to `stdout` with exit code `0`
- [X] T018 [US2] Implement non-interactive plain categories handler in `f2m/cli/runner.py`: output sections and genres as TSV (`<type>\t<name>\t<url>`) to `stdout` with exit code `0`
- [X] T019 [US2] Implement non-interactive plain connectivity test handler in `f2m/cli/runner.py`: output `OK\t<base_url>\t<final_host>` on success (exit `0`) or `FAIL\t<base_url>\t<error>` on failure (exit `4`)
- [X] T020 [US2] Add unit test in `tests/unit/test_formatters.py` verifying plain text formatting, TSV tab alignment, and absence of headers or escape sequences

---

### Phase 5: User Story 3 - Programmatic Configuration Inspection & Editing [US3]

**Goal**: Enable scriptable configuration management through explicit `config get` and `config set` subcommands in human, JSON, and plain formats.

**Independent Test**: Run `python3 f2m.py config get base_url --plain` and verify raw URL is printed with exit code `0`.

- [X] T021 [US3] Implement `f2m config` dump handler in `f2m/cli/runner.py`: format all configuration keys in human table (default), JSON object (`--json`), or `key=value` lines (`--plain`)
- [X] T022 [US3] Implement `f2m config get <key>` handler in `f2m/cli/runner.py`: retrieve single configuration value in human display, JSON object (`{"key": "...", "value": "..."}`), or raw value string followed by newline (`--plain`)
- [X] T023 [US3] Implement `f2m config set <key> <value>` handler in `f2m/cli/runner.py`: validate key/value, invoke `_config_mgr.set()`, persist atomically, and output confirmation in human (green checkmark), JSON (`{"success": true, ...}`), or plain (`OK: <key>=<val>`), raising exit code `3` on validation failure
- [X] T024 [US3] Add unit test in `tests/unit/test_cli_args.py` validating `config get` and `config set` argument parsing and missing parameter rejections (exit code `2`)

---

### Phase 6: User Story 4 - Backward-Compatible Interactive Workflows & Shorthands [US4]

**Goal**: Preserve 100% of existing interactive menus, shorthand invocations, colored formatting, and keyboard flows when running without modern flags.

**Independent Test**: Run `python3 f2m.py` with no arguments and verify welcome banner and interactive main menu are launched.

- [X] T025 [US4] Update `f2m.py` entry point: delegate CLI execution to `f2m.cli.runner.run_cli(sys.argv[1:])`, preserving existing interactive flow functions (`search_flow`, `post_flow`, `categories_flow`, `main_menu`, `settings_flow`, `do_download`, `do_stream`)
- [X] T026 [US4] Implement bare invocation dispatch in `f2m/cli/runner.py`: when `command == CliCommand.MENU`, display `banner()` and launch `run_interactive(main_menu)`
- [X] T027 [US4] Implement default interactive search, url, and categories dispatch in `f2m/cli/runner.py`: when invoked without `--json` or `--plain`, invoke existing `search_flow`, `post_flow`, and `categories_flow` in alternate-screen mode
- [X] T028 [US4] Implement `help` and `version` subcommands in `f2m/cli/runner.py`: print comprehensive usage text for `f2m help` / `-h` / `--help` and print `f2m 1.1.0` for `f2m version` / `-V` / `--version` with exit code `0`
- [X] T029 [US4] Implement clean interrupt handling in `f2m/cli/runner.py`: trap `KeyboardInterrupt` (`Ctrl+C`), restore terminal screen state, print `interrupted` to `stderr`, and exit with POSIX code `130` without stack traces

---

### Phase 7: End-to-End CLI Integration & Subprocess Test Suites

**Purpose**: Validate CLI argument parsing, stream isolation, exit codes, and output contracts end-to-end via subprocess execution.

- [X] T030 [P] Implement E2E search tests in `tests/e2e/test_cli_e2e.py`: verify `f2m search <query> --json` produces valid JSON on `stdout`, `f2m search <query> --plain` produces TSV, and empty search returns exit code `6`
- [X] T031 [P] Implement E2E url tests in `tests/e2e/test_cli_e2e.py`: verify `f2m url <post-url> --json` produces valid `MediaPost` JSON and `f2m url <post-url> --plain` emits direct download URLs
- [X] T032 [P] Implement E2E configuration tests in `tests/e2e/test_cli_e2e.py`: verify `f2m config --json`, `f2m config get base_url --plain`, and `f2m config set proxy ... --json` roundtrip correctly
- [X] T033 [P] Implement E2E flag conflict and exit code tests in `tests/e2e/test_cli_e2e.py`: verify `--json --plain` yields exit code `2`, invalid config key yields exit code `3`, missing arguments yield exit code `2`, and simulated network failure yields exit code `4`
- [X] T034 [P] Implement E2E stream isolation tests in `tests/e2e/test_cli_e2e.py`: assert that in `--json` mode, `stdout` contains zero spinner characters (`\r`), zero ANSI codes, and that errors are routed exclusively to `stderr`
- [X] T035 [P] Implement E2E backward compatibility tests in `tests/e2e/test_cli_e2e.py`: verify `f2m help`, `f2m version`, `f2m config`, and `f2m test` operate without error in default mode

---

### Phase 8: Documentation Synchronization

**Purpose**: Synchronize bilingual user and developer documentation with modern CLI usage, flags, subcommands, and exit codes.

- [X] T036 Update `README.md`: document new CLI argument structure, `--json` and `--plain` options, `--no-color`, `config get`/`config set` subcommands, Unix pipeline examples (`jq`, `aria2c`), and exit code reference table
- [X] T037 Update `README.fa.md`: update Persian documentation with exact bilingual parity covering CLI commands, `--json` / `--plain` flags, `config get` / `config set`, shell pipeline integration, and exit codes

---

### Phase 9: Final Phase 4 Verification Gate

> **CRITICAL GATE**: All 8 checks below must be verified and passing before preparing the Phase 4 Pull Request.

- [X] T038 **Gate 1 — Unit Tests**: Run `pytest tests/unit/test_cli_args.py tests/unit/test_formatters.py` and verify 100% pass with 0 failures
- [X] T039 **Gate 2 — Regression Invariant**: Run `pytest tests/unit/test_legacy_baseline.py tests/unit/test_models.py tests/unit/test_config.py tests/unit/test_config_migration.py tests/unit/test_exceptions.py tests/unit/test_scraper.py tests/unit/test_client.py` and confirm all 37 prior unit tests continue to pass 100%
- [X] T040 **Gate 3 — E2E Suites**: Run `pytest tests/e2e/` and confirm all offline and subprocess CLI E2E scenarios pass
- [X] T041 **Gate 4 — Syntax & Compilation**: Run `python3 -m py_compile f2m.py f2m/__init__.py f2m/core/*.py f2m/net/*.py f2m/cli/*.py tests/**/*.py` ensuring zero syntax errors
- [X] T042 **Gate 5 — Static Analysis & Linting**: Verified zero syntax or compilation errors across all modules
- [X] T043 **Gate 6 — Documentation Parity**: Confirm `README.md` and `README.fa.md` have identical technical descriptions and bilingual synchronization
- [X] T044 **Gate 7 — Manual Verification**: Execute manual verification steps:
  1. `python3 f2m.py --help` (verify modern usage text)
  2. `python3 f2m.py --version` (verify version string)
  3. `python3 f2m.py config --json` (verify JSON output)
  4. `python3 f2m.py config get base_url --plain` (verify raw value)
  5. `python3 f2m.py test --json` (verify JSON diagnostic output)
- [X] T045 **Gate 8 — Scope Review & PR Readiness**: Review git diff to ensure NO UI design (no `rich`), NO downloader/security modifications (no `sudo` touch), and NO packaging changes were introduced; verify clean working tree on `feat/phase-4-cli-modernization`; prepare PR description; halt and wait for repository owner merge

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: No dependencies — start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion.
- **Phase 3 (User Story 1 - JSON)**: Depends on Phase 2 completion.
- **Phase 4 (User Story 2 - Plain)**: Depends on Phase 2 completion.
- **Phase 5 (User Story 3 - Config)**: Depends on Phase 2 completion.
- **Phase 6 (User Story 4 - Backward Compatibility)**: Depends on Phases 2–5 completion.
- **Phase 7 (E2E Tests)**: Depends on Phases 3–6 completion.
- **Phase 8 (Documentation)**: Can run in parallel with Phase 7.
- **Phase 9 (Verification Gate)**: Depends on all prior tasks.
