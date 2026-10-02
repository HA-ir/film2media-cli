# Feature Specification: Phase 7 — Packaging, CI/CD & Release Automation

**Feature Branch**: `feat/phase-7-packaging-ci-release`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "Phase 7 — Packaging, CI/CD & Release Automation: Turn the completed film2media-cli project into a properly installable, testable, reproducible, and releasable Python CLI package with robust CI and release automation while preserving all completed behaviors from Phases 1–6."

---

## 1. Executive Summary & Purpose

Across Phases 1 through 6, `film2media-cli` was modernized from a single monolithic file into a modular, reliable, secure CLI application:
- **Phase 1**: Automated offline test harness and regression safety net (`tests/`).
- **Phase 2**: Core domain models, dataclasses, and XDG configuration engine (`f2m/core/`).
- **Phase 3**: BeautifulSoup4 DOM scraper and resilient HTTP client with bounded retries and mirror failover (`f2m/net/`).
- **Phase 4**: Modernized headless CLI arguments, stream formatters (`--json`, `--plain`, `--no-color`), and deterministic POSIX exit codes (`f2m/cli/`).
- **Phase 5**: Rich-powered terminal UI with structural BiDi and RTL layout safety (`f2m/ui/`).
- **Phase 6**: Secure downloader subsystem eliminating `sudo` and remote binary downloads, with path traversal protection and atomic temporary file handling (`f2m/integrations/`).

**Phase 7 (Final Phase)** completes the modernization roadmap by establishing professional packaging, automated CI testing across supported Python versions, artifact validation, and secure release workflows:
1. **Standard Python Packaging (`pyproject.toml`)**: Formalize `setuptools` build configuration, package discovery, runtime dependencies, optional development dependencies, and console script entry point (`f2m = f2m:main` or `f2m.cli.runner:main`).
2. **Backward-Compatible Dual Invocation**: Support installation via `pip install .` as a system/virtualenv console script (`f2m`) while maintaining 100% backward compatibility for direct source execution (`python f2m.py`).
3. **Comprehensive Multi-OS & Multi-Python CI Pipeline**: Implement GitHub Actions matrix workflow running unit, integration, and subprocess E2E suites across Python 3.8, 3.9, 3.10, 3.11, and 3.12 on Linux, macOS, and Windows.
4. **Package Build & Smoke Verification Gate**: Automated CI verification that builds wheel and source distributions, installs them in a clean isolated virtual environment, and executes CLI smoke tests (`f2m --version`, `f2m help`).
5. **Secure Automated Release Pipeline**: Triggered on signed version tags (`v*`), generating binary bundles and distribution packages attached to GitHub Releases with least-privilege permissions.

---

## 2. Clarifications & Architectural Decisions

### Session 2026-10-02

- Q: What build backend should be used for packaging? → A: Retain `setuptools>=61.0` with explicit package discovery directive `[tool.setuptools.packages.find] where = ["."]`, `include = ["f2m*"]`, and `py-modules = ["f2m"]` to fix the flat-layout build error.
- Q: How should the console entry point be registered? → A: Register `f2m = "f2m:main"` under `[project.scripts]`, keeping `f2m.py` directly executable via `if __name__ == "__main__": main()`.
- Q: Where should the authoritative version be defined? → A: In `pyproject.toml` as `version = "1.1.0"`, synchronized with `VERSION = "1.1.0"` in `f2m.py` and `f2m/cli/runner.py`.
- Q: Should PyPI publishing be automated in Phase 7? → A: No, GitHub Releases remains the established release target; PyPI publishing is deferred unless explicitly requested with OIDC trusted publishing.
- Q: What matrix should CI cover? → A: Test Python 3.8, 3.9, 3.10, 3.11, 3.12 on Linux, plus Python 3.12 on macOS and Windows for cross-platform OS verification.

#### 32 Concrete Architectural Decisions (from Master Codebase Inspection):

1. **Current Package Layout**: Flat layout with top-level package directory `f2m/` containing subpackages (`core`, `net`, `cli`, `ui`, `integrations`) alongside legacy runner script `f2m.py`.
2. **Installability Status**: Currently fails `pip install -e .` with `error: Multiple top-level packages discovered in a flat-layout: ['f2m', 'specs', 'assets']`.
3. **Build Backend Selection**: Retain existing `setuptools>=61.0` and `build-backend = "setuptools.build_meta"` from `pyproject.toml`. Do NOT introduce poetry, hatch, or flit.
4. **Pyproject Metadata Fixes**:
   - Add `[tool.setuptools.packages.find] include = ["f2m*"]` to exclude `specs`, `tests`, and `assets`.
   - Add `py-modules = ["f2m"]` so `f2m.py` is included for the console entry point.
   - Fix license deprecation warning: use standard license expression `license = "MIT"` or keep `{ text = "MIT" }` with `license-files = ["LICENSE"]`.
5. **Authoritative Version Source**: `version = "1.1.0"` in `pyproject.toml`, keeping `VERSION = "1.1.0"` in `f2m.py` and `f2m/cli/runner.py` in parity.
6. **CLI Entry Mechanism**: `[project.scripts] f2m = "f2m:main"`.
7. **Legacy Script Direct Execution**: `f2m.py` remains 100% executable as `python f2m.py` without package installation.
8. **Runtime Dependencies**: Strictly `beautifulsoup4>=4.11.0` and `rich>=13.0.0`. No additional dependencies.
9. **Development/Test Dependencies**: Under `[project.optional-dependencies] dev`: `pytest>=7.0.0`, `pytest-cov>=4.0.0`, `pytest-mock>=3.10.0`, `ruff>=0.1.0`, `build>=1.0.0`, `twine>=5.0.0`.
10. **Supported Python Versions**: Python 3.8 through 3.12 (`requires-python = ">=3.8"`).
11. **Existing GitHub Workflows**: `.github/workflows/build.yml` currently runs on `v*` tags using PyInstaller on Windows and Ubuntu.
12. **Test Command Invariants**: `pytest` and `python -m pytest tests/unit tests/e2e -v`.
13. **Lint/Type Checking**: `ruff` is already configured in `pyproject.toml` (`[tool.ruff]`). CI will run `ruff check .`.
14. **E2E Environment Setup**: Pure standard library and subprocess; zero external services or daemon prerequisites.
15. **Network Independence**: All 105 existing tests run 100% offline via local fixtures and mock guards.
16. **Package Resources**: No non-code binary package resources needed; package contains pure Python modules.
17. **Wheel Contents**: Contains `f2m/` package tree, `f2m.py`, and `.dist-info` metadata. Excludes `tests/`, `specs/`, `assets/`.
18. **Sdist Contents**: Contains source files, `pyproject.toml`, `README.md`, `README.fa.md`, `LICENSE`, excluding `.git/` and `.specify/`.
19. **Console-Script Behavior**: `f2m` invokes `main()` which initializes Windows VT, checks config, parses args, and runs `CliRunner`.
20. **Version Consistency Enforcement**: CI checks that `VERSION` in `f2m.py`, `runner.py`, and `pyproject.toml` match.
21. **Release/Tag Conventions**: Semantic version tags `vX.Y.Z` (e.g. `v1.1.0`).
22. **PyPI Publishing Intent**: GitHub Releases is the established release destination for binaries and wheels. PyPI is NOT enabled unless explicitly requested with OIDC.
23. **GitHub Releases Intent**: Established by `.github/workflows/build.yml`; enhanced in Phase 7 to include wheels, sdist, and checksums.
24. **GitHub Actions Permissions**: Principle of least privilege: `contents: read` default, `contents: write` only for the release job on tag push.
25. **Untrusted PR Protection**: Release workflow triggers ONLY on `push: tags: ["v*"]`, NEVER on `pull_request`.
26. **Artifact Validation**: `twine check --strict dist/*` in CI.
27. **Clean Environment Testing**: CI creates a fresh virtual environment, runs `pip install dist/*.whl`, and verifies `f2m --version` and `f2m help`.
28. **README Installation Updates**: Document `pip install .` and `pipx install .` alongside direct `python f2m.py`.
29. **Persian Parity**: Mirror installation and development updates into `README.fa.md`.
30. **Backward Compatibility**: All Phase 1–6 functionality remains invariant.
31. **Explicit Phase 7 Scope Bounding**: Packaging, CI, and release only. No new CLI commands, domain models, or scraper refactors.

---

## 3. User Scenarios & Testing *(mandatory)*

### User Story 1 - Standard Package Installation & CLI Console Script (Priority: P1) 🎯 MVP
As an end-user or system administrator, I want to install `film2media-cli` using standard Python package tools (`pip install .` or `pipx install .`), so that the `f2m` command is globally available on my system `$PATH` without requiring manual directory navigation or running `python f2m.py`.

**Why this priority**: Core delivery of Phase 7. Makes the tool a first-class citizen of the Python CLI ecosystem.

**Independent Test**: In a clean virtual environment, run `pip install .` and verify that typing `f2m --version` executes successfully, outputs `f2m v1.1.0`, and provides identical command-line functionality to `python f2m.py`.

**Acceptance Scenarios**:
1. **Given** a clean virtual environment without `film2media-cli` installed, **When** executing `pip install .`, **Then** the package builds and installs successfully with all runtime dependencies (`beautifulsoup4`, `rich`).
2. **Given** an installed package, **When** the user types `f2m search "Inception" --json`, **Then** the console entry point invokes the CLI runner, outputting valid JSON to `stdout` with exit code `0`.
3. **Given** a developer checking out the source repository, **When** running `python f2m.py` directly without running `pip install`, **Then** the CLI continues to execute without import errors.

---

### User Story 2 - Multi-Python & Multi-Platform CI Automation (Priority: P2)
As a project maintainer and contributor, I want automated GitHub Actions CI checks to run on every Pull Request and branch push across supported Python versions (3.8 through 3.12) on Linux, macOS, and Windows, so that regressions in scraping, terminal rendering, or downloader security are detected before merging.

**Why this priority**: Guarantees reliability (Principle II) and prevents cross-platform or version-specific regressions.

**Independent Test**: Trigger a pull request and verify that GitHub Actions executes the full 105+ test suite across the test matrix and reports green status.

**Acceptance Scenarios**:
1. **Given** a pull request against `master`, **When** the CI workflow triggers, **Then** it tests the entire automated test suite (`tests/unit`, `tests/e2e`) across Linux, macOS, and Windows.
2. **Given** Python versions 3.8, 3.9, 3.10, 3.11, and 3.12 in the test matrix, **When** tests execute, **Then** all 105+ tests pass with zero failures.
3. **Given** the CI pipeline, **When** test steps complete, **Then** the workflow builds `sdist` and `wheel` artifacts and verifies they can be installed and executed in an isolated environment.

---

### User Story 3 - Secure Release Automation & Artifact Publishing (Priority: P3)
As a project release manager, I want a secure, automated release workflow triggered when a version tag (`v*`) is pushed to GitHub, building verified distribution wheels, source tarballs, and standalone executable binaries, attaching them to a GitHub Release with minimal permissions.

**Why this priority**: Eliminates error-prone manual release packaging and secures the supply chain.

**Independent Test**: Push a git release tag and verify that GitHub Actions automatically packages distribution artifacts, validates metadata with `twine check`, and creates a GitHub Release with checksums.

**Acceptance Scenarios**:
1. **Given** a git tag matching `v*` pushed to the repository, **When** the release workflow runs, **Then** it validates version consistency between the tag, `pyproject.toml`, and `VERSION` in code.
2. **Given** build artifacts (wheel, sdist, PyInstaller binaries), **When** uploaded to the GitHub Release, **Then** they are accompanied by SHA-256 checksums.
3. **Given** a Pull Request from a fork, **When** CI workflows execute, **Then** no release permissions or secrets are exposed.

---

### Edge Cases

- **Unsupported Python Version (< 3.8)**: `pyproject.toml` specifies `requires-python = ">=3.8"`. Attempting to install on Python 3.7 fails early during package metadata resolution with an explicit Python version mismatch error.
- **Top-Level Script Compatibility (`f2m.py`)**: Users who cloned the repo or use legacy shell aliases invoking `python f2m.py` must experience zero breaking changes.
- **Console Script Name Collision**: The console script name is `f2m`. If another binary named `f2m` exists on system `$PATH`, standard shell path lookup rules apply.
- **Dirty Working Directory or Tag Mismatch in Release**: Release workflow verifies that the git tag matches the version declared in `pyproject.toml` and halts if there is a discrepancy.

---

## 3. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST declare package metadata, build requirements, dependencies, and entry points strictly via `pyproject.toml` using `setuptools>=61.0`.
- **FR-002**: System MUST register a console script entry point `f2m` that invokes `f2m:main` (or equivalent top-level runner).
- **FR-003**: System MUST include the entire `f2m` package and all subpackages (`f2m.core`, `f2m.net`, `f2m.cli`, `f2m.ui`, `f2m.integrations`) in wheel and sdist distributions.
- **FR-004**: System MUST maintain 100% backward compatibility for direct source execution via `python f2m.py` without requiring package installation.
- **FR-005**: System MUST declare runtime dependencies strictly: `beautifulsoup4>=4.11.0` and `rich>=13.0.0`.
- **FR-006**: System MUST declare optional development dependencies under `[project.optional-dependencies]` (`pytest>=7.0.0`, `pytest-cov>=4.0.0`, `pytest-mock>=3.10.0`, `ruff>=0.1.0`, `build`, `twine`).
- **FR-007**: System MUST declare Python version requirement as `requires-python = ">=3.8"`.
- **FR-008**: System MUST maintain a single authoritative version string in `pyproject.toml` and ensure `VERSION` in `f2m.py` and `f2m/cli/runner.py` remains strictly synchronized.
- **FR-009**: System MUST provide a GitHub Actions CI workflow (`.github/workflows/ci.yml`) triggered on pushes to `master` and pull requests.
- **FR-010**: CI workflow MUST test across a matrix of Python versions (3.8, 3.9, 3.10, 3.11, 3.12) on `ubuntu-latest`.
- **FR-011**: CI workflow MUST test across operating systems (`ubuntu-latest`, `macos-latest`, `windows-latest`) on Python 3.12.
- **FR-012**: CI workflow MUST execute the complete automated test suite (105+ tests) verifying zero regressions.
- **FR-013**: CI workflow MUST build distribution packages (`python -m build`) and validate metadata using `twine check --strict`.
- **FR-014**: CI workflow MUST execute an isolated smoke test installing the built wheel and verifying `f2m --version` and `f2m help`.
- **FR-015**: System MUST provide a GitHub Actions Release workflow (`.github/workflows/release.yml`) triggered exclusively on `v*` tags with minimal permissions (`contents: write`).
- **FR-016**: Release workflow MUST build and attach source distribution (`.tar.gz`), wheel (`.whl`), and standalone PyInstaller executable binaries (Windows `.exe`, Linux ELF) with SHA-256 checksums to the GitHub Release.
- **FR-017**: System MUST update `README.md` and `README.fa.md` with package installation instructions (`pip install .`, `pipx`), virtual environment usage, supported Python versions, and development test commands.

---

### Key Entities

- **`PackageDistribution`**: Build artifacts comprising source distribution (`sdist`, `.tar.gz`) and binary distribution (`wheel`, `.whl`).
- **`ConsoleScript`**: System command `f2m` mapped to Python callable entry point.
- **`CiMatrix`**: Testing permutation matrix across operating systems and Python versions.
- **`ReleaseArtifact`**: Version-tagged wheel, sdist, PyInstaller standalone binary, and SHA-256 checksum file.

---

## 4. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Clean `pip install .` succeeds in an isolated virtual environment and creates an executable `f2m` command.
- **SC-002**: `f2m --version` outputs the exact version string matching `pyproject.toml` and exits with code `0`.
- **SC-003**: 100% of the 105+ existing automated tests pass across all Python versions (3.8, 3.9, 3.10, 3.11, 3.12) on Linux, macOS, and Windows.
- **SC-004**: Package build verification (`python -m build` followed by `twine check --strict`) reports 0 warnings and 0 errors.
- **SC-005**: Direct invocation via `python f2m.py` functions identically to installed `f2m` console script.
- **SC-006**: Pushing a `v*` release tag generates a GitHub Release containing wheel, sdist, standalone binaries, and checksums with zero manual intervention.

---

## 5. Assumptions & Scope Exclusions

### Assumptions
- Python 3.8+ is available in GitHub Actions runner environments.
- PyPI publishing is optional/deferred unless explicit API tokens or GitHub OIDC Trusted Publishing are configured by the repository owner. GitHub Releases serve as the primary distribution channel for binary and package artifacts.
- PyInstaller binary compilation remains compatible with the modular `f2m` package layout.

### Scope Exclusions
- **No Unrelated Code Refactors**: Scraper, DOM parser, CLI argument tokenizer, Rich UI layouts, and downloader security logic remain untouched.
- **No New CLI Features**: No new product commands or domain entities outside of packaging and entry point integration.
- **No External Paid Services**: CI and release pipelines rely exclusively on standard GitHub Actions free-tier infrastructure.

---

## 6. Backward Compatibility Invariants

1. **Source Execution Invariant**:
   - `python f2m.py` continues to execute seamlessly without requiring installation.
2. **CLI Contract Invariant**:
   - All Phase 4 commands (`search`, `url`, `categories`, `config`, `test`, `help`, `version`) and flags (`--json`, `--plain`, `--no-color`, exit codes) function identically when invoked via `f2m`.
3. **UI & Downloader Invariants**:
   - Phase 5 Rich UI styling and Phase 6 unprivileged downloader execution remain fully intact.
