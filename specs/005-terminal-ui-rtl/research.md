# Research & Architectural Decisions: Phase 5 — Terminal UI & RTL Redesign with Rich

**Feature**: Phase 5 — Terminal UI & RTL Redesign with Rich  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Rich Library Integration & Version Baseline

### Context & Challenge
`rich` is currently present in the system environment (`rich 13.7.1` on Python 3.12), but it is not formally declared in `pyproject.toml` runtime dependencies.
`film2media-cli` must run across Python 3.8+ on Linux, macOS, and Windows.

### Decision
- Add `rich>=13.0.0` to `dependencies` in `pyproject.toml`.
- Version 13+ provides stable APIs for:
  - `rich.console.Console`
  - `rich.table.Table`
  - `rich.panel.Panel`
  - `rich.text.Text`
  - `rich.status.Status`
  - `rich.markup.escape`
  - `rich.cells.cell_len`
- Standard library fallback: In non-interactive modes (`--json`, `--plain`) or when Rich fails to initialize, the CLI falls back to plain unformatted text.

---

## 2. Terminal UI Subsystem Architecture (`f2m/ui/`)

### Context & Challenge
The legacy CLI presentation code in `f2m.py` mixes terminal escape sequences (`\033[...]`), curses-like screen calls (`Screen.enter()`), raw `print()`, and terminal formatting directly inside flow functions (`search_flow`, `post_flow`, `categories_flow`).
In Phase 4, we introduced `f2m/cli/runner.py` which delegates to interactive flow callbacks.
We must structure Phase 5 so that:
1. UI components are modular, reusable, and unit-testable without launching full interactive screen loops.
2. Presentation code is strictly decoupled from scraping and networking.
3. No duplicate command dispatchers or domain models are created.

### Decision
Establish `f2m/ui/` with clean functional separation:
```text
f2m/ui/
├── __init__.py      # Public exports: get_console, render_search_table, render_post_panel, etc.
├── console.py       # Rich Console singletons managing stdout/stderr, TTY, NO_COLOR, and widths
├── theme.py         # Unified Theme and style constants (accents, ratings, badges, borders)
├── bidi.py          # BiDi text utilities, cell width calculation, and safe token escaping
└── views.py         # View renderers: Banner, SearchTable, PostPanel, SelectionMenu, StatusSpinner
```

`f2m/cli/runner.py` and `f2m.py` consume `f2m/ui/` view renderers when running in human-interactive mode.

---

## 3. Practical BiDi & Persian/Arabic Terminal Layout Strategy

### Context & Challenge
Bidirectional text handling in terminal emulators is notoriously fragmented:
- Some modern terminals (e.g. Windows Terminal, Alacritty with BiDi plugins, modern VTE) support basic Unicode Bidirectional Algorithm (UBA) reordering.
- Traditional terminals (e.g. basic xterm, Linux console, macOS Terminal.app) display characters in simple LTR storage order or invert numbers and brackets.
- Reversing text programmatically using libraries like `python-bidi` causes severe issues:
  1. Terminals with native UBA engines display the text double-reversed (backward).
  2. Numbers inside Persian strings (e.g. `2010`) get flipped (`0102`).
  3. English words in mixed titles (e.g. `فیلم Inception 2010`) get scrambled.
  4. URLs and paths are completely mangled and become unclickable/uncopyable.

### Decision
Adopt a **Structural Isolation & Boundary Protection** strategy:
1. **Column Segregation in Tables**:
   - Instead of packing `فیلم Inception 2010 (8.8/10) [دوبله فارسی]` into a single string with ad-hoc padding, Rich `Table` separates discrete attributes into columns:
     - `Index`: Right-aligned numbers (`1`, `2`, `3`).
     - `Type`: Icon badge (`🎞 Movie`, `📺 Series`).
     - `Persian Title`: `title_fa` rendered naturally.
     - `English Title`: `title` rendered LTR.
     - `Year`: Numeric column (`2010`).
     - `Rating`: Styled star column (`★ 8.8/10`).
     - `Badges`: Tags (`[Dub]`, `[Hardsub]`).
   - This ensures each column cell has a uniform text direction, preventing visual BiDi collisions.
2. **Strict LTR Protection for Machine Tokens**:
   - URLs, filesystem paths, filenames, quality tokens (`1080p.BluRay.x265`), episode numbers (`S01E02`), and command options MUST NEVER be reshaped or bidirectionalized.
   - When printing URLs or paths for copying or streaming, they are emitted as pure LTR strings with zero directional control characters (`‎`/`‏`), ensuring 100% copy-paste fidelity.
3. **Accurate Character Cell Width Calculation**:
   - Persian text and Zero-Width Non-Joiners (`‌` / ZWNJ) can cause terminal column drift if measured with `len()`.
   - Use `rich.cells.cell_len()` to compute visual terminal width, guaranteeing that table borders (`│`, `─`) remain perfectly aligned.

---

## 4. Rich Markup Injection Defense

### Context & Challenge
Rich supports BBCode-like syntax tags such as `[bold]`, `[green]`, and `[link]`.
Upstream media titles and metadata scraped from the web frequently contain brackets:
- `Inception 2010 [1080p] [F2M]`
- `Loki S02 [Dubbed]`
If passed directly to `console.print(title)`, Rich attempts to parse `[1080p]` as a markup tag, raising `MarkupError` or mangling the text.

### Decision
- All untrusted or upstream dynamic strings (scraped titles, synopses, URLs, filenames, error messages) MUST pass through `rich.markup.escape()` before rendering.
- Reusable helper: `escape_text(text: str) -> str` in `f2m/ui/bidi.py`.

---

## 5. Stream Isolation & Status Spinner Architecture

### Context & Challenge
Phase 4 established strict stream separation:
- `stdout`: Pure data payloads.
- `stderr`: Status spinners, progress notices, warnings, and errors.
In `--json` and `--plain` modes, `stdout` must remain 100% free of Rich formatting and spinner artifacts.

### Decision
1. **Dedicated Consoles**:
   - `UiConsole.stdout_console`: Rich `Console(file=sys.stdout)` for human interactive screens.
   - `UiConsole.stderr_console`: Rich `Console(file=sys.stderr)` for status messages, spinners, and diagnostics.
2. **Transient Status Spinner (`rich.status.Status`)**:
   - Replaces the legacy multi-threaded `Spinner` in `f2m.py` with `stderr_console.status(...)`.
   - When `--json` or `--plain` is active, or when `sys.stderr` is not a TTY, the status spinner is inert (no-op context manager).
   - Guarantees zero carriage return (`\r`) or frame leakage onto `stdout`.

---

## 6. Responsive Terminal Geometry & Narrow Terminal Fallback

### Context & Challenge
Users run `f2m` in terminal windows of varying sizes:
- Standard 80x24 terminals.
- Wide 120+ column monitors.
- Narrow mobile or split panes (< 60 columns).

### Decision
- Tables use `expand=True`, `box=box.ROUNDED`, and specify explicit column constraints (`ratio`, `no_wrap`, `overflow="ellipsis"`).
- In terminals with width < 65 columns, `render_search_table` dynamically switches to a compact vertical card/list layout to prevent horizontal wrapping and border corruption.
- Panels clamp their maximum width to `console.width`, ensuring no line wraparound artifacts.
