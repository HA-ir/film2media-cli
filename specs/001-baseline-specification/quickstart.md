# Validation & Quickstart Guide: film2media-cli Modernization

**Feature**: `001-baseline-specification`  
**Date**: 2026-10-01  
**Status**: Completed  

---

## 1. Prerequisites & Test Environment

- **Python Version**: Python 3.8+ (tested on 3.8, 3.10, 3.12).
- **Core Dependencies (Virtual Environment)**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e ".[dev]"
  ```
- **Optional External Tools**:
  - `aria2c` (for fast multi-connection downloads)
  - `mpv` or `vlc` (for media streaming)

---

## 2. Test Execution & Quality Gates

### 2.1 Automated Test Suite
Run the full test suite across unit, contract, and offline integration layers:
```bash
# Run all tests with coverage report
pytest --cov=f2m tests/

# Run fast unit tests only (offline, mock fixtures)
pytest tests/unit/

# Run CLI contract validation tests
pytest tests/contract/
```

### 2.2 Formatting & Linting Checks
```bash
# Verify code formatting and linting
ruff check f2m/ tests/
ruff format --check f2m/ tests/
```

---

## 3. End-to-End Verification Scenarios

### Scenario 1: Non-Interactive Search with JSON Output
Tests that headless querying outputs structured data to `stdout` and logs to `stderr` without entering TUI mode.
```bash
# Execute search headlessly and pipe into jq
f2m search "Matrix" --format json | jq '.[0].title'

# Expected Output:
# "The Matrix"
# Exit Code: 0
```

### Scenario 2: Direct Link Resolution & Piping
Tests extracting download links headlessly for external download managers.
```bash
# Resolve 1080p links directly to stdout
f2m resolve "https://www.myf2ms.top/movies/the-matrix-1999/" --quality 1080p --format urls > matrix_links.txt

# Expected Outcome:
# matrix_links.txt contains direct .mkv/.mp4 download URLs
# Exit Code: 0
```

### Scenario 3: Clean Signal Trapping (`Ctrl+C`)
Tests that interrupting the interactive menu does not corrupt the terminal or leave cursor hidden.
```bash
# Launch interactive menu in terminal
f2m

# Press Ctrl+C immediately at the prompt
# Expected Outcome:
# Screen returns to normal terminal scrollback
# Terminal cursor remains visible
# Clean message: "interrupted" (no unhandled traceback)
# Exit Code: 130
```

### Scenario 4: Missing `aria2c` Guidance & Fallback
Tests safe dependency handling without unauthorized privilege escalation.
```bash
# Run download dispatch in an environment where aria2c is removed from PATH
PATH=$(echo "$PATH" | sed -e 's/:\/usr\/bin//') f2m resolve <url> --download

# Expected Outcome:
# Displays: "aria2c not found. To install: sudo apt install aria2 (or brew/winget)"
# Offers immediate fallback: "Falling back to curl (single connection)..."
# ZERO attempts to execute `sudo` or download arbitrary binaries.
```

### Scenario 5: XDG Configuration Hierarchy & Migration
Tests that legacy `f2m.conf` migrates cleanly to the standard user config path.
```bash
# Run with a legacy f2m.conf in working directory
f2m config path

# Expected Outcome:
# Prints active config path: ~/.config/f2m/config.ini (or %APPDATA%\f2m\config.ini)
# Legacy settings imported successfully.
```
