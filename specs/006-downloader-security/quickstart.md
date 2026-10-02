# Quickstart & Verification Guide: Phase 6 Downloader Security

**Feature**: Phase 6 — Downloader Security & Sudo Removal  
**Date**: 2026-10-02  
**Status**: Authoritative Guide  

---

## 1. Prerequisites

- Python 3.8+
- System packages installed: `pytest`
- Optional tools for fallback testing: `curl`, `aria2c`

---

## 2. Automated Test Execution

### 2.1 Run Full Unit & Regression Test Suite
```bash
python -m pytest tests/unit -v
```
*Expected Outcome*: All unit tests pass, including new `test_downloader_security.py` tests covering sanitization, path containment, and pre-flight write validation.

### 2.2 Run Full End-to-End Test Suite
```bash
python -m pytest tests/e2e -v
```
*Expected Outcome*: All E2E tests pass, including Phase 6 tests `test_downloader_e2e.py` verifying read-only destination failure, absence of `sudo`, and exit code preservation.

---

## 3. Manual Verification Scenarios

### Scenario 1: Missing `aria2c` Graceful Guidance & Fallback
**Goal**: Verify that when `aria2c` is not on `$PATH`, `f2m` displays copy-paste installation instructions and falls back to `curl` or links without privilege escalation.
1. Temporarily shadow `aria2c` from `$PATH`:
   ```bash
   PATH=$(echo "$PATH" | tr ':' '\n' | grep -v aria2 | tr '\n' ':') python f2m.py search "Inception"
   ```
2. Select a movie version and trigger download.
3. **Verify**:
   - Terminal shows platform-specific installation command (e.g. `sudo apt install aria2`).
   - `sudo` is **NOT** invoked by `f2m`.
   - No password prompt appears.
   - Download proceeds using `curl` or offers link copying.

---

### Scenario 2: Unwritable Destination Rejection
**Goal**: Verify that downloading to a read-only directory terminates cleanly with exit code `1` and no traceback.
1. Create a read-only test directory:
   ```bash
   mkdir -p /tmp/f2m_ro_test
   chmod 555 /tmp/f2m_ro_test
   ```
2. Configure `f2m` to use this directory:
   ```bash
   python f2m.py config set download_dir /tmp/f2m_ro_test
   ```
3. Attempt to download or export links:
   ```bash
   python f2m.py url "https://example.com/test.mp4"
   ```
4. **Verify**:
   - `stderr` outputs an informative error message: `Destination directory '/tmp/f2m_ro_test' is not writable`.
   - Process exits cleanly with code `1`.
   - Zero raw Python tracebacks appear on the terminal.
5. Cleanup:
   ```bash
   chmod 755 /tmp/f2m_ro_test && rm -rf /tmp/f2m_ro_test
   python f2m.py config set download_dir ~/Downloads/f2m
   ```

---

### Scenario 3: Traversal Attack Defense
**Goal**: Verify that malicious titles or URL components cannot write outside `download_dir`.
1. Run pytest unit test for traversal validation:
   ```bash
   python -m pytest tests/unit/test_downloader_security.py -k "test_path_traversal" -v
   ```
2. **Verify**: Path containment logic catches `../../etc/cron.d` and raises `F2MDownloadError`.

---

### Scenario 4: Atomic `.part` Staging & Interruption Cleanup
**Goal**: Verify that partial downloads using `curl` do not leave orphaned corrupt files.
1. Run pytest test for partial download cleanup:
   ```bash
   python -m pytest tests/unit/test_downloader_security.py -k "test_curl_atomic_part" -v
   ```
2. **Verify**: Files are written to `.part` and only renamed upon exit code `0`.
