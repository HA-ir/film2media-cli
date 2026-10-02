# Implementation Plan: Phase 7 — Packaging, CI/CD & Release Automation

**Branch**: `007-packaging-ci-release` | **Date**: 2026-10-02 | **Spec**: [specs/007-packaging-ci-release/spec.md](spec.md)

**Input**: Feature specification from `/specs/007-packaging-ci-release/spec.md`

---

## Summary

Phase 7 completes the modernization roadmap of `film2media-cli` by turning the project into a professional, reproducible, installable, and releasable Python CLI package. It formalizes `pyproject.toml` using `setuptools>=61.0` with explicit package discovery (`f2m*` and `f2m.py`), registers the `f2m` console script entry point, establishes a robust GitHub Actions CI matrix covering Python 3.8–3.12 across Linux, macOS, and Windows, adds package build and smoke verification gates, and enhances tag-triggered release workflows to produce wheels, source tarballs, standalone PyInstaller executables, and SHA-256 checksums.

---

## Technical Context

**Language/Version**: Python 3.8+ (Linux, macOS, Windows)  
**Primary Dependencies**: Standard library, `beautifulsoup4>=4.11.0` (existing), `rich>=13.0.0` (existing)  
**Build System**: `setuptools>=61.0`, `setuptools.build_meta`  
**Packaging Tools**: `build>=1.0.0`, `twine>=5.0.0`, `wheel`  
**CI/CD Infrastructure**: GitHub Actions (`ubuntu-latest`, `macos-latest`, `windows-latest`)  
**Testing**: `pytest>=7.0.0`, `pytest-cov>=4.0.0`, `pytest-mock>=3.10.0`  
**Quality / Linting**: `ruff>=0.1.0`  
**Console Entry Point**: `f2m = "f2m:main"`  
**Scale/Scope**: Final phase of modernization roadmap  

---

## Constitution Check

*GATE: Evaluated against all 10 core principles of `.specify/memory/constitution.md` (v1.0.0).*

1. **Principle I (Professional CLI UX)**: PASS. Standard console script `f2m` installed on `$PATH` preserves all CLI flags, stream isolation, exit codes, and Rich UI presentation.
2. **Principle II (Reliability Over Superficial Visual Changes)**: PASS. CI matrix tests cross-platform and multi-Python reliability on every PR before merge.
3. **Principle III (Backward Compatibility)**: PASS. Direct execution via `python f2m.py` remains 100% functional.
4. **Principle IV (Testability & Multi-Layered Testing)**: PASS. All 105+ existing tests run in CI matrix plus packaging smoke tests.
5. **Principle V (Documentation as Implementation)**: PASS. Bilingual documentation updates to `README.md` and `README.fa.md` covering `pip install .` and `pipx`.
6. **Principle VI (Incremental Delivery & Branch Discipline)**: PASS. Isolated on feature branch `feat/phase-7-packaging-ci-release`.
7. **Principle VII (PR Ownership & Merge Control)**: PASS. Release workflows require tag creation by human owner; automated agents never push to master or merge PRs.
8. **Principle VIII (End-to-End Acceptance Gate)**: PASS. Multi-OS CI matrix and build/install smoke test serve as hard acceptance gates.
9. **Principle IX (Scope Discipline & Proportional Refactoring)**: PASS. Builds on existing `pyproject.toml` and GitHub Actions without framework churn (no Hatch/Poetry).
10. **Principle X (Honest & Verifiable Claims)**: PASS. All claims verifiable through automated CI logs and local build checks.

---

## Project Structure

### Documentation (this feature)

```text
specs/007-packaging-ci-release/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Phase 0 decisions & rationales
├── data-model.md        # Phase 1 entities & validation rules
├── quickstart.md        # Phase 1 runnable validation guide
├── contracts/           # Phase 1 interface contracts
│   └── packaging-contract.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16 passing)
└── tasks.md             # Phase 2 task breakdown (/speckit-tasks)
```

### Source Code & Configuration Changes

```text
pyproject.toml               # Configure setuptools discovery, py-modules,
                             # [project.scripts] f2m = "f2m:main",
                             # and build/twine dev dependencies

.github/
└── workflows/
    ├── ci.yml               # NEW: Multi-OS (Ubuntu, macOS, Windows) &
    │                        # multi-Python (3.8-3.12) CI with build/smoke gate
    └── release.yml          # UPGRADE: Replaces build.yml with secure
                             # tag-triggered release attaching wheels, sdist,
                             # PyInstaller binaries, and SHA-256 checksums

f2m.py                       # Retained as main execution wrapper
f2m/                         # Fully discoverable package tree

README.md                    # Updated installation and development documentation
README.fa.md                 # Updated Persian installation documentation
```

---

## Detailed Implementation Tasks

### 1. `pyproject.toml` Modernization
- Add explicit package discovery directive:
  ```toml
  [tool.setuptools.packages.find]
  where = ["."]
  include = ["f2m*"]
  exclude = ["specs*", "tests*", "assets*"]

  [tool.setuptools]
  py-modules = ["f2m"]
  ```
- Register `[project.scripts]`:
  ```toml
  [project.scripts]
  f2m = "f2m:main"
  ```
- Add `build>=1.0.0` and `twine>=5.0.0` to `[project.optional-dependencies] dev`.
- Fix license metadata warning if needed using standard SPDX string.

### 2. GitHub Actions CI Matrix (`.github/workflows/ci.yml`)
- Trigger on `push: branches: [master]` and `pull_request: branches: [master]`.
- Job 1 (`test`):
  - Matrix:
    - OS: `ubuntu-latest`, Python: `["3.8", "3.9", "3.10", "3.11", "3.12"]`
    - OS: `macos-latest`, Python: `["3.12"]`
    - OS: `windows-latest`, Python: `["3.12"]`
  - Steps:
    - `actions/checkout@v4`
    - `actions/setup-python@v5`
    - `pip install -e ".[dev]"`
    - `ruff check .`
    - `pytest tests/unit tests/e2e -v`
- Job 2 (`build-and-smoke-test`):
  - Runs on `ubuntu-latest`, Python 3.12, after `test` passes.
  - Steps:
    - `pip install build twine`
    - `python -m build`
    - `twine check --strict dist/*`
    - `pip install dist/*.whl`
    - Smoke test: `f2m --version`, `f2m help`, `f2m config --json`

### 3. GitHub Actions Release Automation (`.github/workflows/release.yml`)
- Replaces legacy `.github/workflows/build.yml`.
- Trigger on `push: tags: ["v*"]`.
- Job 1: Build standalone binaries (Linux ELF and Windows `.exe`) via PyInstaller.
- Job 2: Build wheel and sdist (`python -m build`).
- Job 3: Compute SHA-256 checksums (`sha256sum * > SHA256SUMS.txt`).
- Job 4: Create GitHub Release using `softprops/action-gh-release@v2`, attaching all 4 artifacts plus checksums with `generate_release_notes: true`.
- Permissions: Strictly `contents: write` on the release job.

### 4. Bilingual Documentation
- `README.md`:
  - Add installation via `pip install .` and `pipx`.
  - Document supported Python versions (3.8–3.12).
  - Document development setup and testing with pytest.
- `README.fa.md`:
  - Mirror all installation and testing changes in Persian.

---

## Complexity Tracking

| Issue / Decision | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Explicit `setuptools.packages.find` | Resolves flat-layout package discovery error | Moving to `src/` layout would break direct checkout execution (`python f2m.py`) |
| Scoped GitHub Actions permissions | Prevents token misuse or supply chain compromise | Using default permissive tokens violates Principle of Least Privilege |
| CI smoke test gate | Proves built package actually installs and runs | Running pytest against source tree does not prove the wheel package is valid |
