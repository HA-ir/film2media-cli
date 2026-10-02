# Phase 5 Quality Checklist: Terminal UI & RTL Redesign with Rich

**Purpose**: Validate requirement completeness, visual testability, BiDi safety, and Phase 4 compatibility for Phase 5 before implementation  
**Created**: 2026-10-02  
**Feature**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md) | **Tasks**: [tasks.md](../tasks.md) | **Contract**: [terminal-ui-contract.md](../contracts/terminal-ui-contract.md)  

**Review Ownership**: Reviewer-owned quality review artifact. Mark an item `[x]` only when the reviewer confirms the requirement-quality criterion is satisfied.  
**Marker Semantics**: `[x]` means the criterion has been reviewed and satisfied for requirements quality. It does not mean implementation work is complete.  

---

## 1. Architectural Isolation & Decoupling Quality

- [ ] CHK001 Is the Rich terminal presentation layer strictly isolated in `f2m/ui/` with zero coupling to core scraping or network transport logic? [Completeness, Spec §FR-002, Plan §2]
- [ ] CHK002 Does the design prevent introducing a second command dispatcher, leaving `f2m.cli.runner.CliRunner` as the authoritative dispatcher? [Consistency, Plan §1, Spec §FR-018]
- [ ] CHK003 Are Phase 2 domain entities (`SearchResult`, `MediaPost`, `ConfigurationProfile`) consumed directly without defining duplicate presentation models? [Reusability, Plan §3, Data-Model §3]
- [ ] CHK004 Does the plan leave `f2m/core/models.py`, `f2m/core/config.py`, `f2m/core/scraper.py`, and `f2m/net/client.py` completely untouched? [Scope Discipline, Constitution Principle IX]

---

## 2. Interactive UI Component Coverage & Ergonomics

- [ ] CHK005 Are all existing interactive flows (welcome banner, selection menus, search results, categories, post details, quality/episode pickers) explicitly accounted for? [Completeness, Spec §2.1, Tasks §T008–T020]
- [ ] CHK006 Is the welcome banner specified as a styled Rich `Panel` with logo, version tag, active base URL, and description? [Clarity, Spec §2.1, Contract §2.1]
- [ ] CHK007 Are search results specified to render in an aligned Rich `Table` with distinct columns for index, type, Persian title, English title, year, rating, and badges? [Clarity, Spec §FR-004, Contract §2.2]
- [ ] CHK008 Are post details specified inside a styled Rich `Panel` presenting metadata, IMDb ID, rating, and trailer availability? [Clarity, Spec §FR-005, Contract §2.3]
- [ ] CHK009 Are version and quality hierarchies specified with resolution labels, encoder badges (`F2M`, `PSA`), and episode counts? [Clarity, Spec §FR-006, Tasks §T010]
- [ ] CHK010 Are interactive menus specified with clear selection prompts (`❯ `) and keyboard shortcut guidance (`1-N`, `0`/`b` for back)? [Clarity, Spec §2.1, Contract §2.4]

---

## 3. Terminal BiDi, RTL Safety & Token Protection

- [ ] CHK011 Is structural column segregation specified in tables to isolate Persian titles from English titles and numeric metadata? [BiDi Safety, Spec §2.3, Contract §3.1]
- [ ] CHK012 Are URLs, magnet links, filesystem paths, filenames, quality tokens (`1080p`), and episode tags (`S01E02`) strictly protected as LTR strings? [Token Protection, Spec §FR-016, Contract §3.2]
- [ ] CHK013 Is a copyability guarantee established ensuring URLs and paths printed to the terminal contain zero phantom directional formatting characters (`‎`/`‏`)? [Fidelity, Spec §2.3, Contract §3.3]
- [ ] CHK014 Is visual cell width calculation required to use `rich.cells.cell_len()` to accurately measure Persian characters and ZWNJ (`‌`), preventing broken borders? [Border Alignment, Spec §FR-014, Tasks §T006]
- [ ] CHK015 Are all external and scraped strings required to be sanitized via `rich.markup.escape()` before rendering to prevent BBCode injection crashes? [Security, Spec §2.4, Tasks §T006]
- [ ] CHK016 Is a responsive narrow-terminal fallback (< 65 columns) specified for search tables to prevent line wrapping and border corruption? [Geometry, Spec §2.5, Tasks §T021]

---

## 4. Phase 4 CLI Compatibility & Stream Purity

- [ ] CHK017 Is `--json` output guaranteed to remain 100% pure and machine-readable on `stdout`, completely free of Rich markup or ANSI escape sequences? [Purity, Spec §FR-009, Contract §1.1]
- [ ] CHK018 Is `--plain` output guaranteed to remain 100% pure tab- or newline-delimited text on `stdout`, completely free of Rich formatting? [Purity, Spec §FR-010, Contract §1.1]
- [ ] CHK019 Are transient status spinners (`Console.status()`), progress bars, and diagnostics strictly routed to `sys.stderr`? [Stream Isolation, Spec §FR-011, Contract §1.2]
- [ ] CHK020 Are status spinners and progress indicators specified to run completely inert (zero output) when `--json` or `--plain` is active or when `stderr` is not a TTY? [Contamination Guard, Spec §FR-012, Tasks §T019]
- [ ] CHK021 Is `NO_COLOR` environment variable and `--no-color` flag support explicitly required to strip colors while preserving table structure? [Compliance, Spec §2.5, Contract §1.3]
- [ ] CHK022 Are all Phase 4 POSIX exit codes (`0`, `1`, `2`, `3`, `4`, `5`, `6`, `130`) strictly preserved across all interactive and non-interactive workflows? [Exit Codes, Spec §FR-018, Contract §4]
- [ ] CHK023 Is clean keyboard interrupt (`Ctrl+C`) handling specified to restore terminal screens, print to `stderr`, and exit with code `130` without tracebacks? [Interruption, Spec §2.6, Tasks §T020]

---

## 5. Test Strategy & Verification Coverage

- [ ] CHK024 Are unit tests specified for `Console` initialization under color, `NO_COLOR`, and non-TTY modes in `tests/unit/test_ui_rendering.py`? [Coverage, Tasks §T007]
- [ ] CHK025 Are unit tests specified for `escape_text` with bracketed tokens (`[1080p]`, `[Dubbed]`)? [Coverage, Tasks §T007]
- [ ] CHK026 Are unit tests specified verifying visual cell width calculation for Persian text and ZWNJ (`‌`)? [Coverage, Tasks §T007]
- [ ] CHK027 Are unit tests specified verifying `render_search_table` and `render_post_header` using in-memory `Console(record=True)`? [Coverage, Tasks §T013]
- [ ] CHK028 Are geometry unit tests specified verifying table rendering at 80 columns, narrow width (< 65 cols), and wide width (120 cols) in `tests/unit/test_ui_geometry.py`? [Coverage, Tasks §T022]
- [ ] CHK029 Are subprocess-based E2E tests specified verifying `--json` validity, `--plain` link structure, and exit codes in `tests/e2e/test_ui_e2e.py`? [Coverage, Tasks §T024–T027]
- [ ] CHK030 Is the 100% pass invariant for all 72 existing Phase 1–4 regression tests enforced as a mandatory verification gate? [Regression, Tasks §T031]

---

## 6. Documentation & Scope Governance

- [ ] CHK031 Are bilingual documentation updates required in `README.md` and `README.fa.md` showcasing the modernized Rich terminal interface and Persian layout? [Parity, Constitution Principle V, Tasks §T028–T029]
- [ ] CHK032 Are scope boundaries enforced strictly prohibiting Phase 6 downloader security changes and Phase 7 packaging/CI workflows? [Scope Discipline, Spec §7, Tasks §T037]
- [ ] CHK033 Is human-only merge authority explicitly enforced with mandatory agent halting instructions upon PR creation? [Governance, Constitution Principle VII, Tasks §T037]

---

## Notes

- Mark items `[x]` only after reviewer evaluation confirms the requirement-quality criterion is satisfied.
- Leave items unchecked when they still require clarification, correction, or reviewer evaluation.
- `/speckit-implement` reads checklist checkbox state as a quality gate and must not modify markers.
