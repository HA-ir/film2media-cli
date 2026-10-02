# Tasks: Phase 7 — Packaging, CI/CD & Release Automation

**Input**: Design documents from `specs/007-packaging-ci-release/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/packaging-contract.md`, `quickstart.md`)  
**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/packaging-contract.md`  

---

## Phase 1: Setup (Packaging Configuration)

**Purpose**: Formalize package discovery, dependency declarations, and version metadata in `pyproject.toml`.

- [X] T001 Update package discovery in `pyproject.toml` using `[tool.setuptools.packages.find]` with `where = ["."]`, `include = ["f2m*"]`, and `exclude = ["specs*", "tests*", "assets*"]`
- [X] T002 [P] Include top-level execution wrapper in `pyproject.toml` via `[tool.setuptools] py-modules = ["f2m"]`
- [X] T003 [P] Add `build>=1.0.0` and `twine>=5.0.0` to `[project.optional-dependencies] dev` in `pyproject.toml`
- [X] T004 [P] Normalize license declaration in `pyproject.toml` using standard license expression `license = "MIT"` to eliminate deprecation warnings

---

## Phase 2: Foundational (Console Entry Point & Version Synchronization)

**Purpose**: Establish single authoritative versioning and the global console script entry point.

- [X] T005 [P] Register console script entry point `[project.scripts] f2m = "f2m:main"` in `pyproject.toml`
- [X] T006 Ensure version string parity (`1.1.0`) across `pyproject.toml`, `f2m.py`, and `f2m/cli/runner.py`
- [X] T007 [P] Create packaging and version synchronization unit test `test_packaging_and_version_parity` in `tests/unit/test_packaging.py`

**Checkpoint**: Packaging configuration and entry points are established. User story implementations can proceed.

---

## Phase 3: User Story 1 - Standard Package Installation & CLI Console Script (Priority: P1) 🎯 MVP

**Goal**: Enable clean `pip install .` and `pipx install .` creating an executable `f2m` command on `$PATH` while maintaining 100% backward compatibility for direct source checkout execution (`python f2m.py`).

**Independent Test**: In a clean virtual environment, run `pip install .` and verify that `f2m --version`, `f2m help`, `f2m search --json`, and `f2m search --plain` execute with identical behavior to `python f2m.py`.

### Tests for User Story 1 ⚠️

- [X] T008 [P] [US1] Unit test verifying that `f2m:main` correctly executes `run_cli(sys.argv[1:])` with proper Windows VT and config initialization in `tests/unit/test_packaging.py`
- [X] T009 [P] [US1] E2E test verifying package building (`python -m build`) and `twine check --strict` on generated distributions in `tests/e2e/test_packaging_e2e.py`
- [X] T010 [P] [US1] E2E test verifying wheel installation in an isolated clean virtual environment and testing `f2m --version` in `tests/e2e/test_packaging_e2e.py`
- [X] T011 [P] [US1] E2E test verifying direct source checkout execution (`python f2m.py --version`) remains 100% functional without package installation in `tests/e2e/test_packaging_e2e.py`

### Implementation for User Story 1

- [X] T012 [US1] Verify that `f2m:main` functions as a clean zero-argument callable suitable for `console_scripts` in `f2m.py`
- [X] T013 [US1] Test local build generation using `python -m build` ensuring clean `dist/*.whl` and `dist/*.tar.gz` creation
- [X] T014 [US1] Validate generated distribution metadata using `twine check --strict dist/*` ensuring 0 warnings and 0 errors

**Checkpoint**: User Story 1 complete. `film2media-cli` is installable via pip and provides the global `f2m` console command.

---

## Phase 4: User Story 2 - Multi-Python & Multi-Platform CI Automation (Priority: P2)

**Goal**: Implement comprehensive GitHub Actions CI matrix running automated test suites, linting, compilation, and package smoke tests across Python 3.8–3.12 on Linux, macOS, and Windows.

**Independent Test**: Trigger GitHub Actions workflow on PR or push and verify all matrix jobs pass successfully.

### Tests for User Story 2 ⚠️

- [X] T015 [P] [US2] Workflow validation test verifying `.github/workflows/ci.yml` syntax, triggers, matrix definitions, and least-privilege permissions in `tests/unit/test_ci_workflows.py`
- [X] T016 [P] [US2] Offline test suite validation ensuring all 105+ tests execute offline with mock guards in `tests/e2e/test_offline_suite.py`

### Implementation for User Story 2

- [X] T017 [US2] Create GitHub Actions CI workflow in `.github/workflows/ci.yml` triggered on push to `master` and pull requests
- [X] T018 [US2] Configure multi-Python test matrix in `.github/workflows/ci.yml` covering Python 3.8, 3.9, 3.10, 3.11, and 3.12 on `ubuntu-latest`
- [X] T019 [US2] Configure cross-platform matrix in `.github/workflows/ci.yml` covering `macos-latest` and `windows-latest` on Python 3.12
- [X] T020 [US2] Add linting (`ruff check .`) and compilation (`compileall`) steps to `.github/workflows/ci.yml`
- [X] T021 [US2] Add `pytest tests/unit tests/e2e -v` execution step to `.github/workflows/ci.yml`
- [X] T022 [US2] Add `build-and-smoke-test` job in `.github/workflows/ci.yml` verifying `python -m build`, `twine check --strict`, isolated wheel installation, and CLI execution (`f2m --version`, `f2m help`, `f2m config --json`)

**Checkpoint**: User Story 2 complete. Automated CI guards all future changes across all supported environments.

---

## Phase 5: User Story 3 - Secure Release Automation & Artifact Publishing (Priority: P3)

**Goal**: Upgrade tag-triggered GitHub Actions release automation to build wheels, source tarballs, standalone PyInstaller executables, compute SHA-256 checksums, and publish GitHub Releases with minimal scoped permissions.

**Independent Test**: Inspect release workflow configuration to verify trigger strictly on `v*` tags, generation of checksums, and attachment of all distribution assets to GitHub Releases.

### Tests for User Story 3 ⚠️

- [X] T023 [P] [US3] Unit test verifying `.github/workflows/release.yml` triggers exclusively on `v*` tags and has minimal `contents: write` permissions in `tests/unit/test_ci_workflows.py`
- [X] T024 [P] [US3] Verify PyInstaller build command compatibility with modular `f2m` package layout in `tests/unit/test_packaging.py`

### Implementation for User Story 3

- [X] T025 [US3] Replace legacy `.github/workflows/build.yml` with enhanced release workflow in `.github/workflows/release.yml`
- [X] T026 [US3] Configure tag trigger (`push: tags: ["v*"]`) and least-privilege permissions (`contents: write` scoped strictly to release job) in `.github/workflows/release.yml`
- [X] T027 [US3] Add PyInstaller standalone binary build jobs for Linux (`f2m-linux-x64`) and Windows (`f2m-windows-x64.exe`) in `.github/workflows/release.yml`
- [X] T028 [US3] Add distribution package build job (`python -m build`) generating `.whl` and `.tar.gz` in `.github/workflows/release.yml`
- [X] T029 [US3] Add SHA-256 checksum generation step (`sha256sum * > SHA256SUMS.txt`) in `.github/workflows/release.yml`
- [X] T030 [US3] Configure `softprops/action-gh-release@v2` step to attach wheels, sdist, standalone binaries, and checksums with automatic release notes in `.github/workflows/release.yml`

**Checkpoint**: User Story 3 complete. Tagged releases automatically generate and publish complete release bundles.

---

## Phase 6: Documentation & Final Verification

**Purpose**: Update bilingual installation documentation and perform final end-to-end regression audit.

- [X] T031 [P] Update English documentation in `README.md` with package installation instructions (`pip install .`, `pipx`), supported Python versions (3.8–3.12), and development test instructions
- [X] T032 [P] Update Persian documentation in `README.fa.md` with package installation instructions and development workflow in full parity with `README.md`
- [X] T033 Run the complete test suite locally (`pytest tests/unit tests/e2e -v`) verifying all 105+ existing tests pass with 0 regressions
- [X] T034 Run local wheel build and smoke test per `specs/007-packaging-ci-release/quickstart.md`
- [X] T035 Final read-only security and scope review verifying zero unrequested refactorings or feature additions

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1: Setup (pyproject.toml)
   └── Phase 2: Foundational (Version & Entry Point)
          ├── Phase 3: User Story 1 (P1 - pip install & f2m command) [MVP]
          ├── Phase 4: User Story 2 (P2 - Multi-OS & Multi-Python CI)
          └── Phase 5: User Story 3 (P3 - Release Automation & Checksums)
                 └── Phase 6: Documentation & Final Verification
```

### Parallel Opportunities

- **Phase 1**: T002, T003, T004 can be implemented in parallel.
- **Phase 2**: T005 and T007 can proceed in parallel.
- **Phase 3 (US1 Tests)**: T008, T009, T010, T011 can be written concurrently.
- **Phase 4 (US2 Tests)**: T015 and T016 can be written concurrently.
- **Phase 5 (US3 Tests)**: T023 and T024 can be written concurrently.
- **Phase 6 (Docs)**: T031 (`README.md`) and T032 (`README.fa.md`) can be drafted in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (pyproject configuration) and Phase 2 (Foundational entry point).
2. Complete Phase 3 (User Story 1 - pip installation and console script).
3. **Validate MVP**: Run `python -m build`, inspect with `twine check`, install wheel in clean venv, and verify `f2m --version`.

### Incremental Delivery
1. Foundation & US1: Package is installable and runnable via pip.
2. Add US2: Multi-Python & multi-OS CI matrix guarantees automated quality gates on PRs.
3. Add US3: Tag-triggered release automation produces verified wheels and standalone executables.
4. Documentation & Final Audit: Finalize bilingual documentation and verify 100% test pass rate.
