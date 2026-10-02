# Quickstart Validation Guide: Phase 4 — CLI Argument & Output Modernization

**Feature**: Phase 4 — CLI Argument & Output Modernization  
**Date**: 2026-10-02  
**Status**: Authoritative Validation Guide  

---

## 1. Prerequisites

Ensure dependencies and virtual environment are configured:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## 2. Validation Scenarios

### Scenario 1: Machine-Readable JSON Search (`--json`)
Verify that search output produces valid JSON without spinner contamination:
```bash
# Execute search in JSON mode and pipe directly into jq
python3 f2m.py search "Inception" --json | jq .

# Verify exit code is 0
echo "Exit Code: $?"
```
*Expected Outcome*: `jq` parses an array of search result objects without syntax errors. Zero spinner characters or ANSI codes appear on `stdout`. Exit code is `0`.

---

### Scenario 2: Unix Pipeline Integration (`--plain`)
Verify that direct download links can be extracted cleanly:
```bash
# Extract links from a post URL using plain mode
python3 f2m.py url "https://www.myf2ms.top/movies/inception-2010/" --plain

# Test piping into head/wc
python3 f2m.py url "https://www.myf2ms.top/movies/inception-2010/" --plain | wc -l
```
*Expected Outcome*: Outputs direct media download URLs (`.mkv`, `.mp4`) one per line. No headers, box-drawing characters, or ANSI codes.

---

### Scenario 3: Programmatic Configuration Inspection
Verify that configuration values can be extracted cleanly for shell scripting:
```bash
# Dump entire configuration as JSON
python3 f2m.py config --json | jq .base_url

# Extract a single configuration key value cleanly
BASE_URL=$(python3 f2m.py config get base_url --plain)
echo "Current base URL is: $BASE_URL"
```
*Expected Outcome*: `config --json` outputs a valid JSON object. `config get base_url --plain` prints only the raw URL string followed by a newline.

---

### Scenario 4: Mutual Exclusivity Enforcement
Verify that conflicting flags are rejected with exit code `2`:
```bash
# Attempt to run with both --json and --plain
python3 f2m.py search "Inception" --json --plain

echo "Exit Code: $?"
```
*Expected Outcome*: Process terminates immediately with exit code `2`. An informative error message is displayed on `stderr`. `stdout` remains completely empty.

---

### Scenario 5: Error Handling & Stream Isolation in JSON Mode
Verify that errors emit a structured JSON error object to `stderr` while keeping `stdout` empty:
```bash
# Attempt to query with an unreachable domain or invalid key
python3 f2m.py config set invalid_key "test" --json 1>out.json 2>err.json

echo "Exit Code: $?"
cat err.json | jq .
cat out.json  # Must be empty!
```
*Expected Outcome*: Exit code is `3`. `out.json` is empty (0 bytes). `err.json` contains valid JSON with `"error": true`, `"code": "CONFIG_ERROR"`, and `"exit_code": 3`.

---

### Scenario 6: Backward Compatibility (Interactive Invocations)
Verify that existing commands without flags preserve their full interactive behavior:
```bash
# View configuration in colored human-readable mode
python3 f2m.py config

# Connectivity test
python3 f2m.py test

# Usage help
python3 f2m.py help
```
*Expected Outcome*: All legacy commands produce their established human-readable, colored output with exit code `0`.
