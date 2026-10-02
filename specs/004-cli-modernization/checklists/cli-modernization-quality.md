# Phase 4 Quality Checklist: CLI Argument & Output Modernization

**Purpose**: Validate requirement completeness, testability, stream isolation, and backward compatibility for Phase 4 before implementation  
**Created**: 2026-10-02  
**Feature**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md) | **Tasks**: [tasks.md](../tasks.md) | **Contract**: [cli-interface-contract.md](../contracts/cli-interface-contract.md)  

**Review Ownership**: Reviewer-owned quality review artifact. Mark an item `[x]` only when the reviewer confirms the requirement-quality criterion is satisfied.  
**Marker Semantics**: `[x]` means the criterion has been reviewed and satisfied for requirements quality. It does not mean implementation work is complete.  

---

## 1. Requirement Completeness & CLI Command Coverage

- [ ] CHK001 Are syntax definitions, arguments, and options explicitly specified for all primary subcommands (`search`, `url`, `categories`, `config`, `test`, `help`, `version`)? [Completeness, Spec §2.1, Contract §2]
- [ ] CHK002 Is bare invocation (`f2m` with no arguments) specified to launch the interactive welcome banner and main navigation menu? [Completeness, Spec §FR-002, Tasks §T026]
- [ ] CHK003 Are command aliases (`s`, `cat`, `c`, `cfg`, `t`, `h`, `v`) explicitly enumerated and mapped to their respective operations? [Completeness, Spec §2.1, Contract §2]
- [ ] CHK004 Are multi-word positional search queries (e.g., `f2m search breaking bad`) explicitly specified to be joined with spaces to preserve legacy convenience? [Clarity, Spec §2.1, Tasks §T003]

---

## 2. Argument Validation & Flag Combinations

- [ ] CHK005 Is mutual exclusivity between `--json` and `--plain` explicitly enforced with exit code `2` and an error message on `stderr`? [Consistency, Spec §FR-006, Contract §1]
- [ ] CHK006 Are global flag positions specified to be valid both preceding and following the subcommand (e.g., `f2m --json search` vs `f2m search --json`)? [Clarity, Spec §2.2, Tasks §T003]
- [ ] CHK007 Are error behaviors and exit codes explicitly defined for missing required arguments (`url` without URL, `config set` without value)? [Coverage, Spec §2.1, Contract §3]
- [ ] CHK008 Are unrecognized commands or unknown options required to emit a clean diagnostic to `stderr` and terminate with exit code `2` without stack traces? [Clarity, Spec §2.1, Contract §3]

---

## 3. Output Format Correctness & Deterministic Schemas

- [ ] CHK009 Is the `--json` output schema for `search` specified to produce a valid JSON array of `SearchResult` objects matching domain `.to_dict()`? [Consistency, Spec §2.3, Contract §2.1]
- [ ] CHK010 Is the `--json` output schema for `url` specified to produce a complete `MediaPost` JSON object with all versions, qualities, and episodes? [Consistency, Spec §2.3, Contract §2.2]
- [ ] CHK011 Is the `--json` output schema for `categories` and `test` fully specified with deterministic field names and data types? [Completeness, Spec §2.3, Contract §2.3–2.5]
- [ ] CHK012 Is `--plain` output specified as unadorned, non-colored, tab-separated or newline-delimited text without headers or box characters? [Clarity, Spec §FR-005, Contract §2]
- [ ] CHK013 Is `f2m url <url> --plain` specifically defined to output direct media download URLs one per line for piping to download accelerators (`aria2c -i -`)? [Clarity, Spec §3 (US2), Contract §2.2]
- [ ] CHK014 Is `f2m config get <key> --plain` specified to output the raw value string followed by a newline without a `key=` prefix? [Clarity, Spec §2.1, Contract §2.4]

---

## 4. Stream Isolation & Progress Contamination Guards

- [ ] CHK015 Is `stdout` strictly reserved for data payloads, guaranteeing zero ANSI escape codes, zero banner greetings, and zero progress text in `--json` and `--plain` modes? [Purity, Spec §FR-004, Contract §4]
- [ ] CHK016 Are all diagnostics, informational notices, warnings, and errors strictly required to be routed to `stderr`? [Stream Isolation, Spec §FR-008, Contract §4]
- [ ] CHK017 Is `Spinner` specified to write exclusively to `stderr` and operate in an inert (zero output) state when `--json` or `--plain` is active or `stderr` is not a TTY? [Contamination Guard, Spec §2.5, Tasks §T006]
- [ ] CHK018 In `--json` mode during an error, is `stdout` required to remain completely empty while `stderr` receives a structured JSON error object? [Error Contract, Spec §FR-012, Research §3]

---

## 5. Exit Code Standards & Error Handling

- [ ] CHK019 Are the 8 standard exit codes (`0`, `1`, `2`, `3`, `4`, `5`, `6`, `130`) mapped explicitly to their operational triggers and exception classes? [Completeness, Spec §2.4, Contract §3]
- [ ] CHK020 Is the structured JSON error schema (`error: bool`, `code: str`, `message: str`, `exit_code: int`) explicitly defined for `stderr`? [Clarity, Spec §2.3, Contract §4]
- [ ] CHK021 Is empty search result behavior explicitly specified to emit `[]` on `stdout` and exit with code `6` (`NOT_FOUND`)? [Edge Case, Spec §3 (US1), Contract §2.1]
- [ ] CHK022 Is user interruption (`SIGINT` / `Ctrl+C`) specified to restore terminal screens, print a cancellation message, and exit with code `130` without leaking tracebacks? [Resilience, Spec §2.4, Tasks §T029]

---

## 6. Backward Compatibility & Architectural Integration

- [ ] CHK023 Are legacy command invocations (`f2m search`, `f2m url`, `f2m categories`, `f2m config`, `f2m test`) guaranteed to operate identically in default interactive mode? [Compatibility, Spec §8, Plan §3]
- [ ] CHK024 Does the CLI plan reuse Phase 2 domain entity `.to_dict()` methods without duplicating data structures or schemas? [Reusability, Plan §1, Research §3]
- [ ] CHK025 Does the CLI plan reuse Phase 2 XDG configuration precedence and atomic persistence without altering config engine logic? [Preservation, Spec §8, Plan §4.2]
- [ ] CHK026 Does the CLI plan preserve Phase 3 BeautifulSoup DOM scraper and resilient network client behavior without modifying scraper internals? [Preservation, Spec §8, Plan §4.2]

---

## 7. Test Strategy & Verification Coverage

- [ ] CHK027 Are dedicated unit tests specified for argument tokenization, flag extraction, and alias resolution in `tests/unit/test_cli_args.py`? [Coverage, Tasks §T008]
- [ ] CHK028 Are unit tests specified for `JsonFormatter` and `PlainFormatter` output serialization in `tests/unit/test_formatters.py`? [Coverage, Tasks §T009]
- [ ] CHK029 Are subprocess-based E2E tests specified executing `f2m.py` across all exit codes, stream isolation assertions, and pipeline outputs in `tests/e2e/test_cli_e2e.py`? [Coverage, Tasks §T030–T035]
- [ ] CHK030 Are offline test execution and the network-blocking fixture enforced for all new CLI test suites? [Offline Integrity, Plan §3, Constitution Principle IV]
- [ ] CHK031 Is the 100% pass invariant for all 45 existing Phase 1, 2, and 3 regression tests enforced as a mandatory verification gate? [Regression, Tasks §T039]

---

## 8. Documentation & Scope Governance

- [ ] CHK032 Are bilingual documentation updates required in `README.md` and `README.fa.md` covering subcommands, `--json`, `--plain`, and the exit codes matrix? [Parity, Constitution Principle V, Tasks §T036–T037]
- [ ] CHK033 Are scope boundaries enforced strictly prohibiting Phase 5 Rich/TUI design, Phase 6 downloader security, and Phase 7 packaging? [Scope Discipline, Spec §6, Plan §Technical Context]
- [ ] CHK034 Is human-only merge authority explicitly enforced with mandatory agent halting instructions upon PR creation? [Governance, Constitution Principle VII, Tasks §T045]

---

## Notes

- Mark items `[x]` only after reviewer evaluation confirms the requirement-quality criterion is satisfied.
- Leave items unchecked when they still require clarification, correction, or reviewer evaluation.
- `/speckit-implement` reads checklist checkbox state as a quality gate and must not modify markers.
