# Phase 0: Research & Packaging Decisions

**Feature**: Phase 7 — Packaging, CI/CD & Release Automation  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Build Backend & Package Layout Configuration

### Decision: Retain `setuptools>=61.0` with Explicit Discovery Directive
- **Approach**: Retain existing `setuptools` build backend in `pyproject.toml` (`build-backend = "setuptools.build_meta"`). Fix the flat-layout discovery failure by adding:
  ```toml
  [tool.setuptools.packages.find]
  where = ["."]
  include = ["f2m*"]
  exclude = ["specs*", "tests*", "assets*"]

  [tool.setuptools]
  py-modules = ["f2m"]
  ```
- **Rationale**:
  - `setuptools>=61.0` is already declared in `pyproject.toml` and supports PEP 517/518 and PEP 621.
  - The build failure in `pip install -e .` was caused by setuptools discovering `specs` and `assets` as additional top-level packages. Explicitly constraining package discovery to `f2m*` and `py-modules = ["f2m"]` completely resolves this without changing project structure.
  - Avoids introducing new build tooling (Hatch, Poetry, Flit) which would violate Principle IX (Scope Discipline).
- **Alternatives Considered**:
  - *Migrating to `src/` layout (`src/f2m`)*: Rejected. Moving `f2m` into `src/` would break backward compatibility for direct source checkout execution (`python f2m.py` and local git checkouts) without providing practical benefit.
  - *Migrating to Hatch or Flit*: Rejected. Speculative tool churn. `setuptools` is standard, robust, and already in place.

---

## 2. Console Entry Point & Execution Parity

### Decision: Console Script `f2m = "f2m:main"`
- **Approach**: Register the console entry point under `[project.scripts]` as:
  ```toml
  [project.scripts]
  f2m = "f2m:main"
  ```
  `f2m:main` sets up Windows VT emulation (if on Windows), ensures configuration exists, parses `sys.argv`, and dispatches to `get_runner().run(argv)`.
- **Rationale**:
  - Guarantees 100% execution parity whether the user runs the installed command `f2m`, or invokes `python f2m.py` from source checkout.
  - Ensures all Phase 4 commands, options (`--json`, `--plain`, `--no-color`), exit codes, Phase 5 Rich UI, and Phase 6 downloader security invariants are identically preserved.
- **Alternatives Considered**:
  - *Pointing directly to `f2m.cli.runner:main`*: Rejected. Bypasses Windows VT initialization and configuration bootstrap logic present in `f2m:main`.

---

## 3. Dependency Management & Version Synchronization

### Decision: Minimal Runtime Dependencies with Single Version Authority
- **Approach**:
  - **Runtime**: Strictly `beautifulsoup4>=4.11.0` and `rich>=13.0.0`.
  - **Development**: Under `[project.optional-dependencies] dev`: `pytest>=7.0.0`, `pytest-cov>=4.0.0`, `pytest-mock>=3.10.0`, `ruff>=0.1.0`, `build>=1.0.0`, `twine>=5.0.0`.
  - **Version Source**: Authoritative version in `pyproject.toml` (`version = "1.1.0"`). `VERSION = "1.1.0"` in `f2m.py` and `f2m/cli/runner.py` is kept in sync and verified via automated test.
- **Rationale**:
  - Eliminates unneeded dependencies. The standard library provides all networking, subprocess, and configuration management needed.
  - Keeps package installation lightweight, secure, and fast.

---

## 4. Multi-Platform & Multi-Python CI Workflow

### Decision: Dedicated GitHub Actions CI Matrix (`.github/workflows/ci.yml`)
- **Approach**:
  - **Trigger**: Runs on `push` to `master` and all `pull_request` events.
  - **Matrix**:
    - Linux (`ubuntu-latest`): Python 3.8, 3.9, 3.10, 3.11, 3.12.
    - macOS (`macos-latest`): Python 3.12.
    - Windows (`windows-latest`): Python 3.12.
  - **Steps**:
    1. Checkout repository.
    2. Setup Python version.
    3. Install dependencies (`pip install -e ".[dev]"`).
    4. Code quality: `ruff check .` and syntax compilation.
    5. Test execution: `pytest tests/unit tests/e2e -v` (105+ tests).
    6. Build verification (on Python 3.12): `python -m build` followed by `twine check --strict dist/*`.
    7. Smoke test: Install built wheel into a clean virtualenv and execute `f2m --version` and `f2m help`.
- **Rationale**:
  - Guarantees reliability across all promised platforms and Python versions before any code can be merged into master.
  - Validates that distribution packages are not only buildable, but also installable and runnable.

---

## 5. Secure Release Pipeline (`.github/workflows/release.yml`)

### Decision: Tag-Triggered GitHub Release with Minimal Permissions
- **Approach**:
  - Triggered exclusively on `push: tags: ["v*"]`.
  - Never runs on pull requests or untrusted forks.
  - Jobs:
    1. **Build Packages**: Builds source distribution (`sdist`) and binary wheel (`wheel`) using `python -m build`. Validates with `twine check`.
    2. **Build Binaries**: Builds PyInstaller standalone binaries for Linux (`f2m-linux-x64`) and Windows (`f2m-windows-x64.exe`) reusing the proven compilation steps from `.github/workflows/build.yml`.
    3. **Publish GitHub Release**: Computes SHA-256 checksums (`SHA256SUMS.txt`), attaches all distribution files and binaries to the GitHub Release using `softprops/action-gh-release@v2`.
    4. **Permissions**: Minimal `contents: write` scoped strictly to the release creation job.
  - **PyPI Status**: PyPI publishing is deferred as GitHub Releases is the established project distribution model. No long-lived API tokens or PyPI credentials are required.
- **Rationale**:
  - Eliminates manual release errors and provides instant access to ready-to-run binaries and pip-installable wheels.
  - Follows supply chain security best practices with cryptographic checksums and scoped permissions.
