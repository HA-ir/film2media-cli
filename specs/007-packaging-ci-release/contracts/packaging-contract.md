# Contract: Packaging, CI & Release Automation

**Feature**: Phase 7 — Packaging, CI/CD & Release Automation  
**Date**: 2026-10-02  
**Status**: Authoritative Contract  

---

## 1. Package Installation Contract

### 1.1 Console Script Execution
When installed via `pip install .` or `pipx install film2media-cli`:
- The command `f2m` is available on the user's `$PATH`.
- Invoking `f2m [args...]` executes the identical application logic as `python f2m.py [args...]`.
- Exit codes:
  - `0`: Success.
  - `1`: Operational error / download failure.
  - `2`: Invalid CLI invocation / syntax conflict.
  - `3`: Configuration error.
  - `4`: Network failure.
  - `5`: Parser failure.
  - `6`: Not found.
  - `130`: User interrupt (`SIGINT`).

### 1.2 Direct Script Execution
- Running `python f2m.py [args...]` directly from the source checkout remains 100% supported without requiring package installation.

---

## 2. CI Automation Contract (`.github/workflows/ci.yml`)

### 2.1 Trigger Events
- Runs on:
  - `push` to `master` branch.
  - `pull_request` targeting `master` branch.

### 2.2 Matrix & Execution Contract
- All jobs MUST pass before a pull request can be merged:
  - **Linux Matrix**: Python 3.8, 3.9, 3.10, 3.11, 3.12 on `ubuntu-latest`.
  - **Cross-Platform Matrix**: Python 3.12 on `macos-latest` and `windows-latest`.
- **Quality Checks**:
  - `ruff check .` passes with 0 errors.
  - `python3 -m compileall f2m f2m.py tests` succeeds.
- **Test Suite**:
  - 100% of the 105+ existing tests pass in offline mode (`pytest tests/unit tests/e2e -v`).
- **Package Integrity Gate**:
  - `python -m build` builds wheel and sdist with 0 errors.
  - `twine check --strict dist/*` passes.
  - Wheel installs into a clean virtual environment and `f2m --version` exits with code `0`.

---

## 3. Release Automation Contract (`.github/workflows/release.yml`)

### 3.1 Trigger Events & Permissions
- Triggered strictly on:
  - `push: tags: ["v*"]`
- Security permissions:
  - Top-level: `permissions: contents: read`
  - Release job: `permissions: contents: write`
  - Zero access to release permissions on untrusted PRs.

### 3.2 Release Artifacts
Every release MUST attach:
1. `film2media_cli-<version>-py3-none-any.whl` (Python Wheel)
2. `film2media_cli-<version>.tar.gz` (Source Distribution)
3. `f2m-linux-x64` (Standalone Linux Executable)
4. `f2m-windows-x64.exe` (Standalone Windows Executable)
5. `SHA256SUMS.txt` (Cryptographic verification checksums)
