# Contract: CLI Interface, Stream Separation & Exit Codes

**Feature**: Phase 4 — CLI Argument & Output Modernization  
**Date**: 2026-10-02  
**Status**: Authoritative Contract  

---

## 1. Command Syntax & Argument Grammar

```text
f2m [GLOBAL_OPTIONS] [COMMAND] [COMMAND_OPTIONS] [ARGS...]
```

### Global Options

| Option | Shorthand | Type | Description |
|---|---|---|---|
| `--json` | - | Flag | Format output as machine-readable JSON on `stdout`. Enforces non-interactive mode. |
| `--plain` | - | Flag | Format output as unadorned tab- or newline-delimited text on `stdout`. Enforces non-interactive mode. |
| `--no-color` | - | Flag | Strip ANSI color escape codes from output. Also enabled if `NO_COLOR` env var is present or `stdout` is not a TTY. |
| `--config` | - | String | Path to custom configuration INI file. Takes highest precedence over defaults and `F2M_CONFIG`. |
| `--help` | `-h` | Flag | Display CLI usage information and exit `0`. |
| `--version` | `-V` | Flag | Display application version (`f2m 1.1.0`) and exit `0`. |

---

## 2. Subcommand Specifications

### 2.1 `search` (Alias: `s`)
- **Interactive Invocation**: `f2m search <query...>`
  - Launches interactive terminal picker (`search_flow`).
- **Non-Interactive JSON**: `f2m search <query...> --json` (or `f2m --json search <query...>`)
  - Streams JSON array of `SearchResult` objects to `stdout`.
- **Non-Interactive Plain**: `f2m search <query...> --plain`
  - Streams TSV rows (`<kind>\t<title>\t<year>\t<rating>\t<url>`) to `stdout`.
- **Exit Codes**:
  - `0`: 1 or more results returned successfully.
  - `6`: Query returned 0 results. Emits `[]` on `stdout` in `--json` mode; empty `stdout` in `--plain` mode.
  - `4`: Network failure.

### 2.2 `url`
- **Interactive Invocation**: `f2m url <post-url>`
  - Launches interactive post menu (`post_flow`).
- **Non-Interactive JSON**: `f2m url <post-url> --json`
  - Streams complete `MediaPost` JSON object to `stdout`.
- **Non-Interactive Plain**: `f2m url <post-url> --plain`
  - Streams all available direct media download URLs, one per line, to `stdout`.
- **Exit Codes**:
  - `0`: Post parsed and emitted successfully.
  - `2`: Missing URL argument.
  - `4`: Network failure / post unreachable.
  - `5`: Malformed HTML / unparseable post structure.
  - `6`: Post not found (HTTP 404).

### 2.3 `categories` (Aliases: `cat`, `c`)
- **Interactive Invocation**: `f2m categories`
  - Launches interactive categories navigation menu.
- **Non-Interactive JSON**: `f2m categories --json`
  - Streams JSON taxonomy object containing `sections` and `genres` to `stdout`.
- **Non-Interactive Plain**: `f2m categories --plain`
  - Streams tab-delimited taxonomy rows (`<type>\t<name>\t<url>`) to `stdout`.
- **Exit Codes**:
  - `0`: Categories retrieved and formatted successfully.
  - `4`: Network failure.

### 2.4 `config` (Alias: `cfg`)
- **Show All**: `f2m config`
  - Default: Formatted key-value table.
  - `--json`: JSON object of all active configuration keys and values.
  - `--plain`: `key=value` on each line.
- **Get Key**: `f2m config get <key>`
  - Default: Formatted display of key and value.
  - `--json`: `{"key": "<key>", "value": "<val>"}`.
  - `--plain`: Raw value string followed by newline.
- **Set Key**: `f2m config set <key> <value...>`
  - Default: Green `✔ <key> saved` confirmation.
  - `--json`: `{"success": true, "key": "<key>", "value": "<val>", "file_path": "<path>"}`.
  - `--plain`: `OK: <key>=<value>`.
- **Exit Codes**:
  - `0`: Success.
  - `2`: Missing key or value arguments.
  - `3`: Configuration validation failure or write error.

### 2.5 `test` (Alias: `t`)
- **Invocation**: `f2m test`
  - Default: Formatted connectivity test display on `stdout`.
  - `--json`: Connectivity JSON object on `stdout`.
  - `--plain`: `OK\t<base_url>\t<final_host>` on success; `FAIL\t<base_url>\t<error>` on failure.
- **Exit Codes**:
  - `0`: Primary host or mirror reached.
  - `4`: All hosts unreachable.

---

## 3. Exit Code Standards

The application strictly guarantees the following exit codes:

```text
 0  = SUCCESS            Command completed successfully
 1  = RUNTIME_ERROR      Unclassified operational error
 2  = INVALID_ARGUMENT   Syntax error, unknown command, conflicting flags, missing argument
 3  = CONFIG_ERROR       F2MConfigError (bad key, invalid type, write failure)
 4  = NETWORK_ERROR      F2MNetworkError (timeout, DNS failure, all mirrors exhausted)
 5  = PARSE_ERROR        F2MParseError (unparseable upstream HTML/JSON)
 6  = NOT_FOUND          Empty search result, or post 404
130  = SIGINT             Script interrupted by user (Ctrl+C)
```

---

## 4. Output Stream Isolation Contract

1. **`stdout` Guarantee**:
   - In `--json` mode: Contains **only** valid, parsable JSON text.
   - In `--plain` mode: Contains **only** unadorned text (TSV or newline-delimited).
   - In `--json` or `--plain` mode, zero ANSI color escape codes, zero spinner frames (`\r`), and zero banner lines may be emitted on `stdout`.
2. **`stderr` Guarantee**:
   - Progress spinners, informative logs, warnings, and errors MUST be routed exclusively to `stderr`.
   - In `--json` and `--plain` modes, spinners run inert (zero characters written) to avoid polluting logs or terminal redraws.
3. **Error Reporting in `--json` Mode**:
   - When any command fails in `--json` mode:
     - `stdout` MUST be completely empty.
     - `stderr` MUST emit a single valid JSON error object:
       ```json
       {
         "error": true,
         "code": "NETWORK_ERROR",
         "message": "Connection to https://example.com timed out after 25s",
         "exit_code": 4
       }
       ```
     - The process terminates with the non-zero exit code.
