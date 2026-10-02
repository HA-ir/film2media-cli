# Phase 1: Data Model & Packaging Entities

**Feature**: Phase 7 — Packaging, CI/CD & Release Automation  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Packaging & Distribution Entities

### 1.1 `PackageMetadata` (Declarative Specification)
Represented in `pyproject.toml` per PEP 621:

```toml
[project]
name = "film2media-cli"
version = "1.1.0"
description = "Film2Media terminal client for searching, streaming, and downloading movies and series"
readme = "README.md"
requires-python = ">=3.8"
license = { text = "MIT" }
authors = [{ name = "HA-ir" }]
dependencies = [
    "beautifulsoup4>=4.11.0",
    "rich>=13.0.0",
]
```

### 1.2 `PackageDiscovery` (Setuptools Configuration)
Defines exact packages and modules included in build distributions:

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["f2m*"]
exclude = ["specs*", "tests*", "assets*"]

[tool.setuptools]
py-modules = ["f2m"]
```

- **`include`**: `["f2m*"]` recursively includes `f2m`, `f2m.core`, `f2m.net`, `f2m.cli`, `f2m.ui`, and `f2m.integrations`.
- **`exclude`**: Excludes documentation (`specs`), test suites (`tests`), and media (`assets`) from wheels.
- **`py-modules`**: Includes top-level `f2m.py` so entry points and direct execution work interchangeably.

### 1.3 `ConsoleScript`
Maps terminal executable command to Python callable:

```toml
[project.scripts]
f2m = "f2m:main"
```

---

## 2. CI & Release Pipeline Models

### 2.1 `CiMatrix` (GitHub Actions Specification)
Defines operating system and Python runtime test permutations:

| Operating System | Python Versions | Purpose |
|---|---|---|
| `ubuntu-latest` | 3.8, 3.9, 3.10, 3.11, 3.12 | Comprehensive language version matrix |
| `macos-latest` | 3.12 | POSIX / macOS platform verification |
| `windows-latest` | 3.12 | Windows VT emulation & NTFS path verification |

### 2.2 `ReleaseBundle`
The collection of immutable distribution assets produced for each tagged release (`vX.Y.Z`):

```text
dist/
├── film2media_cli-1.1.0-py3-none-any.whl       # Standard Python wheel
├── film2media_cli-1.1.0.tar.gz                 # Source distribution (sdist)
├── f2m-linux-x64                               # Standalone Linux ELF binary
├── f2m-windows-x64.exe                         # Standalone Windows executable
└── SHA256SUMS.txt                              # SHA-256 verification hashes
```

---

## 3. Validation Rules & State Transitions

### 3.1 Packaging Validation Flow
1. **Source State**: Clean repository checkout on tag `vX.Y.Z`.
2. **Build Generation**: `python -m build` produces `.tar.gz` and `.whl` in `dist/`.
3. **Metadata Inspection**: `twine check --strict dist/*` verifies description rendering and metadata syntax.
4. **Isolated Installation**: `pip install dist/*.whl` into a clean virtual environment.
5. **Execution Verification**: `f2m --version` returns `f2m vX.Y.Z` with exit code `0`.

### 3.2 Tag-Triggered Release Lifecycle
```text
[git push origin v1.1.0]
           │
           ▼
[GitHub Actions: release.yml triggered]
           │
           ├──> Job 1: Build Packages (Wheel + Sdist) -> twine check
           ├──> Job 2: Build Linux Standalone Binary (PyInstaller)
           ├──> Job 3: Build Windows Standalone Binary (PyInstaller)
           │
           ▼
[Job 4: Generate Checksums & Create GitHub Release]
           │
           ▼
[Release Published with Assets & Release Notes]
```
