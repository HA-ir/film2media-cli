# Contract: Terminal UI & RTL Rendering Contract

**Feature**: Phase 5 — Terminal UI & RTL Redesign with Rich  
**Date**: 2026-10-02  
**Status**: Authoritative Contract  

---

## 1. Stream Separation & Non-Interactive Invariants

1. **`stdout` Guarantee**:
   - In human interactive mode: Rich `Console(file=sys.stdout)` renders styled tables, panels, and prompts.
   - In `--json` mode: Strictly valid, unadorned JSON via `JsonFormatter`. Rich `Console` is **NEVER** used. Zero ANSI codes, zero Rich markup, zero spinner frames.
   - In `--plain` mode: Strictly unadorned TSV or newline text via `PlainFormatter`. Rich `Console` is **NEVER** used.
2. **`stderr` Guarantee**:
   - Status spinners, progress bars, informational notices, warnings, and error messages route strictly to `sys.stderr`.
   - In non-interactive modes (`--json`, `--plain`, non-TTY `stderr`), status spinners run inert (zero characters emitted).
3. **`NO_COLOR` and `--no-color`**:
   - When `NO_COLOR` environment variable is set or `--no-color` flag is present, Rich `Console` initializes with `no_color=True`. All ANSI escape sequences are omitted while structural alignment, borders, and text layout are preserved.

---

## 2. Component Rendering Specifications

### 2.1 Welcome Banner
- Rendered via Rich `Panel` with rounded border (`box.ROUNDED`).
- Displays application logo (`⚡ F2M`), version tag (`v1.1.0`), active base URL, and short description.
- Width adapts automatically to `console.width`, clamped to a maximum of 60 columns to prevent excessive stretching on ultra-wide screens.

### 2.2 Search Results Table (`render_search_table`)
- Rendered via Rich `Table(box=box.ROUNDED, expand=True)`.
- **Columns (in order)**:
  1. `#` (Index, right-aligned, cyan)
  2. `Type` (Icon badge: `🎞 Movie` / `📺 Series`, styled)
  3. `Persian Title` (`title_fa`, natural reading order, escaped)
  4. `Original Title` (`title`, LTR, bold white, escaped)
  5. `Year` (Numeric, dim, center-aligned)
  6. `Rating` (`★ rating`, bold yellow)
  7. `Badges` (`[Dubbed]`, `[Hardsub]`, styled tags)
- **Narrow Terminal Fallback**:
  - If `console.width < 65`, switches to vertical card listing to prevent column wrapping and border breakage.

### 2.3 Media Post Details Panel (`render_post_header`)
- Rendered via Rich `Panel(box=box.ROUNDED)`.
- Displays movie/series title, Persian title, release year, IMDb ID, star rating, and trailer status badge.

### 2.4 Selection Menus (`render_menu`)
- Displays choices in an aligned, numbered list with icons.
- Displays standard selection prompt `❯ ` with styled shortcut guide (e.g. `1-N`, `0` or `b` to go back).

---

## 3. BiDi & Machine Token Protection Contract

1. **Directional Boundary Isolation**:
   - Discrete metadata elements (Persian title, English title, numeric year, rating) are placed in separate table columns.
2. **Strict LTR Protection**:
   - URLs, filesystem paths, filenames, quality tokens (`1080p.BluRay.x265`), episode numbers (`S01E02`), and command options MUST NEVER be reshaped or bidirectionalized. They remain strictly LTR.
3. **Copyability Fidelity**:
   - URLs and paths printed to the terminal for copying or streaming are printed as raw, intact LTR strings without phantom directional characters (`‎`/`‏`), ensuring 100% copy-paste fidelity.
4. **Rich Markup Escaping**:
   - All external strings pass through `rich.markup.escape()` before being interpolated into Rich renderables.

---

## 4. Exit Code & Interrupt Preservation

All Phase 4 exit codes are strictly preserved:
- `0`: Success
- `1`: Operational error
- `2`: Invalid argument / syntax error
- `3`: Configuration error (`F2MConfigError`)
- `4`: Network error (`F2MNetworkError`)
- `5`: Parse error (`F2MParseError`)
- `6`: Resource not found (empty search results, HTTP 404)
- `130`: Interrupted (`SIGINT` / `Ctrl+C`)
