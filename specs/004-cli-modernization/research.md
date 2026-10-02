# Research & Architectural Decisions: Phase 4 — CLI Argument & Output Modernization

**Feature**: Phase 4 — CLI Argument & Output Modernization  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Argument Parsing Strategy: `argparse` vs Custom Lexer/Parser

### Context & Challenge
The legacy client in `f2m.py` performs manual slicing on `sys.argv[1:]`:
```python
cmd = argv[0].lower()
if cmd == "search":
    run_interactive(search_flow, " ".join(argv[1:]) or None)
```
This enables convenient multi-token queries without quotes, such as `f2m search breaking bad 2008` becoming `"breaking bad 2008"`.
However, modern CLI requirements mandate:
- Global flags (`f2m --json search ...` as well as `f2m search ... --json`).
- Mutual exclusivity (`--json` vs `--plain`).
- Subcommands with specific options (`config get`, `config set`).
- POSIX exit code `2` on syntax errors or invalid flag combinations.
- Preserving bare invocation `f2m` entering interactive `main_menu()`.

### Options Evaluated
1. **Standard Library `argparse` with Subparsers**:
   - *Pros*: Built-in, automatic help text generation, standard flag parsing.
   - *Cons*: By default, `argparse` parses subcommands strictly after the command name. Interleaved global flags before and after subcommands require complex multi-pass parsing or `parse_known_args`. Default error handling writes to `stderr` and calls `sys.exit(2)` with rigid GNU-style messages. Handling unquoted multi-word positional arguments (`f2m search breaking bad`) requires `nargs="+"`.
2. **Third-Party Libraries (`click`, `typer`)**:
   - *Pros*: Declarative decorators, type hints.
   - *Cons*: Violates Constitution Principle IX (Scope Discipline & Minimal Dependencies). Project philosophy is minimal external dependencies.
3. **Custom Pre-Tokenizing Wrapper + Dedicated `ArgumentParser`**:
   - *Pros*: Full control over token extraction. Can extract global flags (`--json`, `--plain`, `--no-color`, `--config`) from anywhere in the argument vector, validate mutual exclusivity, normalize multi-token positional arguments, and route to dedicated subcommand dispatchers. Preserves 100% legacy compatibility while enforcing strict POSIX validation.
   - *Cons*: Requires writing ~100 lines of robust tokenizing logic.

### Decision
**Adopt Option 3 (Custom Parser in `f2m/cli/parser.py`)**.
A lightweight, typed parser parses `sys.argv[1:]`:
- Scans and extracts global flags (`--json`, `--plain`, `--no-color`, `--config <path>`).
- Validates mutual exclusivity (`--json` and `--plain` cannot coexist; raises exit code `2`).
- Identifies the primary command (`search`, `url`, `categories`, `config`, `test`, `help`, `version`, or default `MENU` when empty).
- Collects remaining arguments per subcommand, joining unquoted tokens for `search` and `config set`.
- Returns a strongly-typed `CliArgs` dataclass.

---

## 2. Stream Isolation & Progress Contamination Guards

### Context & Challenge
In `f2m.py`, `ok()`, `info()`, `warn()`, `err()`, and `Spinner` write to `sys.stdout`:
```python
def info(msg): print(f"{C.blue('ℹ')} {msg}")
class Spinner:
    def _spin(self):
        sys.stdout.write(f"\r{C.cyan(self.FRAMES[i % len(self.FRAMES)])} {self.text}…  ")
```
When running `f2m search "Inception" --json | jq .`, any carriage returns (`\r`) or status lines written to `stdout` break JSON deserialization with syntax errors.

### Decision
1. **Strict Stream Separation**:
   - `stdout`: Reserved exclusively for data payloads (formatted text in default mode, valid JSON string in `--json` mode, TSV/lines in `--plain` mode).
   - `stderr`: Reserved exclusively for diagnostics, logs, error messages, and progress spinners.
2. **Inert Spinner in Non-Interactive Modes**:
   - `Spinner` is updated to check active output format (`OutputFormat.JSON` or `OutputFormat.PLAIN`) and `sys.stderr.isatty()`.
   - In `--json` or `--plain` mode, or when `sys.stderr` is not a TTY, `Spinner.__enter__` does not start the background thread and emits zero characters.
3. **Zero Contamination Verification**:
   - An automated test will assert that piping `f2m search ... --json` produces valid JSON directly parsable by `json.loads(stdout)` with zero cleaning or regex stripping required.

---

## 3. JSON Serialization Strategy & Error Contract

### Context & Challenge
Phase 2 domain models (`f2m.core.models`) already provide `.to_dict()` serialization for:
- `SearchResult`
- `Card`
- `Episode`
- `Quality`
- `MediaVersion`
- `Season`
- `MediaPost`
- `ConfigurationProfile`

We must avoid duplicating schema definitions or creating separate serialization logic.

### Decision
1. **Reuse Existing Domain Model Serialization**:
   - `JsonFormatter` delegates directly to model `.to_dict()` methods.
   - For lists (e.g. search results), formats as `[result.to_dict() for result in results]`.
   - For posts, formats as `post.to_dict()`.
   - For config, formats as `config_mgr.profile().to_dict()`.
2. **Error Representation in `--json` Mode**:
   - When an operation fails in `--json` mode:
     - `stdout` remains completely empty.
     - `stderr` receives a single, valid JSON error object:
       ```json
       {
         "error": true,
         "code": "<ERROR_CODE>",
         "message": "<DIAGNOSTIC_MESSAGE>",
         "exit_code": <INT>
       }
       ```
     - Process exits with the designated non-zero exit code.
   - This ensures downstream pipes (`f2m ... --json | jq .`) fail cleanly at the shell level rather than ingesting error objects as valid search or post data.

---

## 4. Standardized POSIX Exit Codes & Exception Translation

### Context & Challenge
The legacy implementation returned `0` almost universally, or called `sys.exit(1)` inside helper functions.
Constitution Principle X and Technical Constraints require explicit POSIX exit codes:
- `0`: Success.
- `1`: Operational error.
- `2`: Invalid CLI invocation.
- `130`: User interrupt.

Furthermore, programmatic automation benefits from fine-grained codes for configuration, network, and parse errors.

### Decision
Establish an explicit exception-to-exit-code mapping in `f2m.cli.runner`:

| Exception Class / Condition | Exit Code | Error Code Identifier |
|---|---|---|
| Normal completion | `0` | `SUCCESS` |
| Unknown command, missing argument, `--json` + `--plain` | `2` | `INVALID_ARGUMENT` |
| `F2MConfigError` | `3` | `CONFIG_ERROR` |
| `F2MNetworkError` | `4` | `NETWORK_ERROR` |
| `F2MParseError` | `5` | `PARSE_ERROR` |
| Empty search results or 404 URL | `6` | `NOT_FOUND` |
| Generic `F2MError` / unhandled exception | `1` | `RUNTIME_ERROR` |
| `KeyboardInterrupt` (`SIGINT`) | `130` | `SIGINT` |

All command dispatchers catch these exceptions at the top-level runner boundary, format the appropriate error message (or JSON error object on `stderr`), and call `sys.exit(exit_code)` without leaking raw tracebacks.
