# Quickstart Validation Guide: Phase 5 — Terminal UI & RTL Redesign with Rich

**Feature**: Phase 5 — Terminal UI & RTL Redesign with Rich  
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

### Scenario 1: Interactive Search Rendering (Rich Table)
Verify that interactive search results render in an aligned Rich `Table`:
```bash
# Run interactive search in standard terminal
python3 f2m.py search "Inception"
```
*Expected Outcome*: Search results appear in an aligned Rich table with rounded borders (`box.ROUNDED`), distinct columns for `#`, `Type`, `Persian Title`, `Original Title`, `Year`, `Rating`, and `Badges`. Zero broken borders.

---

### Scenario 2: Machine-Readable Isolation (`--json` & `--plain`)
Verify that Phase 4 machine streams remain 100% free of Rich markup or formatting:
```bash
# JSON output must parse directly with jq with zero ANSI codes
python3 f2m.py search "Inception" --json | jq .

# Plain output must contain only raw TSV text
python3 f2m.py search "Inception" --plain
```
*Expected Outcome*: `jq` parses search results without syntax errors. `stdout` contains zero ANSI escape sequences (`\033[...]`) and zero Rich markup.

---

### Scenario 3: `NO_COLOR` Environment Compliance
Verify that colors are cleanly stripped when `NO_COLOR` is present:
```bash
# Execute with NO_COLOR=1
NO_COLOR=1 python3 f2m.py search "Inception" --help
```
*Expected Outcome*: Rich output retains table borders and structural layout, but contains zero ANSI color escape sequences.

---

### Scenario 4: Narrow Terminal Width Adaptation (< 65 Columns)
Verify that narrow terminals adapt gracefully without horizontal text corruption:
```bash
# Force terminal columns to 60 columns
COLUMNS=60 python3 f2m.py config
```
*Expected Outcome*: Content wraps cleanly within 60 columns without visual truncation or horizontal line wraparound.

---

### Scenario 5: Persian Text & LTR Protection
Verify that Persian titles render cleanly and URLs remain pure LTR:
```bash
# Inspect a post in interactive mode
python3 f2m.py url "https://www.myf2ms.top/movies/inception-2010/"
```
*Expected Outcome*: Persian and English titles appear in their designated panel fields. Download links and URLs remain in verbatim LTR format and can be copied cleanly without mangled characters.

---

### Scenario 6: Transient Spinner on `stderr`
Verify that loading indicators use Rich status on `stderr` and clear cleanly:
```bash
# Run connectivity test in human mode
python3 f2m.py test
```
*Expected Outcome*: Transient loading spinner appears on `stderr` while fetching and clears completely upon completion, leaving clean diagnostic text.
