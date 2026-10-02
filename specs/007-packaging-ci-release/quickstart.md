# Quickstart & Verification Guide: Phase 7 Packaging & CI

**Feature**: Phase 7 — Packaging, CI/CD & Release Automation  
**Date**: 2026-10-02  
**Status**: Authoritative Guide  

---

## 1. Local Package Build & Installation Verification

### 1.1 Test Package Build
Build source distribution and wheel locally:
```bash
python3 -m pip install --upgrade build twine
python3 -m build
```
*Expected Outcome*: Generates `.whl` and `.tar.gz` in `dist/`.

### 1.2 Validate Package Metadata
```bash
twine check --strict dist/*
```
*Expected Outcome*: `Checking dist/...: PASSED`. 0 warnings, 0 errors.

### 1.3 Smoke Test Wheel in Isolated Virtual Environment
```bash
# Create and activate clean test environment
python3 -m venv /tmp/f2m_clean_env
source /tmp/f2m_clean_env/bin/activate

# Install freshly built wheel
pip install dist/*.whl

# Verify CLI console script
f2m --version
f2m help
f2m config --json

# Deactivate and clean up
deactivate
rm -rf /tmp/f2m_clean_env
```
*Expected Outcome*: `f2m` executes cleanly, displays `f2m v1.1.0`, outputs valid JSON in config mode, and exits with code `0`.

---

## 2. Automated Test Suite Verification

Run the full automated test suite:
```bash
pytest tests/unit tests/e2e -v
```
*Expected Outcome*: All 105+ tests pass with zero regressions.

---

## 3. GitHub Actions CI Verification

1. On push or PR to `master`, GitHub Actions triggers `.github/workflows/ci.yml`.
2. Inspect the Actions matrix:
   - `test (ubuntu-latest, 3.8)` -> PASS
   - `test (ubuntu-latest, 3.9)` -> PASS
   - `test (ubuntu-latest, 3.10)` -> PASS
   - `test (ubuntu-latest, 3.11)` -> PASS
   - `test (ubuntu-latest, 3.12)` -> PASS
   - `test (macos-latest, 3.12)` -> PASS
   - `test (windows-latest, 3.12)` -> PASS
   - `build-and-smoke-test` -> PASS
