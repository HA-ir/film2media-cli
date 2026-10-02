# Feature Specification: Phase 2 — Domain Entities & XDG Configuration Engine

**Feature Branch**: `feat/phase-2-domain-entities-config`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "We are now starting Phase 2 after Phase 1 has been successfully merged into master. Focus ONLY on Domain Entities & XDG Configuration Engine."

---

## 1. Executive Summary & Purpose

Phase 1 established the testing safety net (`pytest`), recorded offline fixtures, and verified legacy regression baselines without altering application code.

Phase 2 introduces the foundational **domain models** and a resilient, **XDG-compliant configuration engine** for `film2media-cli`. Currently, `f2m.py` relies on an untyped module-level global dictionary (`_cfg`) and hardcodes `CONF_PATH` relative to the running script/binary directory. This causes immediate fatal `PermissionError` crashes when installed into system locations (such as `/usr/local/bin` or `C:\Program Files`), lacks configuration hierarchy (environment variables are ignored), and offers no input validation. Simultaneously, media data structures (`Post`, `Season`, `Quality`, `Episode`, `SearchResult`) are loosely defined dataclasses coupled to scraping routines.

Phase 2 extracts clean, typed domain entities and provides an XDG-compliant configuration system with automatic legacy migration. **User-facing CLI behavior, terminal UI rendering, and scraping algorithms remain unchanged in this phase.**

---

## Clarifications

### Session 2026-10-02

#### 1. Domain Model Contracts & Legacy Mapping
- **`SearchResult`**: Represents a parsed search hit from quick-search JSON or HTML cards.
  - *Required*: `kind` (`"movie"` | `"series"`), `title: str`, `url: str`.
  - *Optional (with defaults)*: `title_fa: str = ""`, `year: str = ""`, `rating: str = ""`, `image: str = ""`, `meta: str = ""`, `is_dub: bool = False`, `is_hardsub: bool = False`.
  - *Normalization*: HTML entities unescaped (`html.unescape`), `<em>` highlights stripped, `url` resolved to absolute URL.
- **`Card`**: Legacy listing summary card (used for pagination & category flows).
  - *Fields*: `url: str`, `title: str`, `note: str = ""`, `poster: str = ""`, `year: str = ""`, `kind: str = ""`. Retained for 100% backward compatibility with `parse_listing`.
- **`Episode`**: Represents an individual downloadable or streamable media file.
  - *Required*: `num: int` (validated >= 1), `url: str` (validated non-empty media URL), `filename: str` (unquoted filename extracted from URL).
  - *Optional*: `label: str = ""` (defaults to `f"قسمت {num}"` if empty).
- **`Quality`**: Represents a resolution/encoding release block.
  - *Required*: `label: str` (e.g. `"1080p BluRay"`, `"720p x265"`).
  - *Optional*: `encoder: str = ""`, `episodes: list[Episode] = field(default_factory=list)`.
- **`MediaVersion`**: Represents audio translation/subtitle version.
  - *Required*: `key: str` (`"dub"` | `"hardsub"`), `title: str` (e.g. `"نسخه دوبله فارسی"`).
  - *Optional*: `qualities: list[Quality] = field(default_factory=list)`.
- **`Season`**: Represents a television series season.
  - *Required*: `title: str` (e.g. `"فصل اول"`).
  - *Optional*: `number: int = 1`, `versions: list[MediaVersion] = field(default_factory=list)`.
- **`MediaPost` (aliased as `Post` for legacy compatibility)**:
  - *Required*: `url: str`, `title: str` (normalized via `clean_title`).
  - *Optional*: `year: str = ""`, `imdb_id: str = ""`, `rating: str = ""`, `is_series: bool = False`, `seasons: list[Season] = field(default_factory=list)`, `versions: list[MediaVersion] = field(default_factory=list)`, `trailer: str = ""`.
- *Serialization*: All domain models provide `to_dict()` and `from_dict()` for round-trip data conversion and testing. Missing or unknown dictionary keys are ignored safely without raising exceptions.

#### 2. Configuration Precedence & Environment Parsing
- **Keys Participating in Precedence**: Exactly the 7 existing configuration keys: `base_url`, `mirrors`, `proxy`, `search_sort`, `player`, `download_dir`, and `user_agent`.
- **Precedence Order**:
  1. `CLI Overrides` (via programmatic parameters; CLI flag support reserved for Phase 4)
  2. `Environment Variables` (`F2M_*`)
  3. `Local Working Directory File` (`./f2m.conf` or `./config.ini` in `os.getcwd()`)
  4. `User Global XDG Config` (`~/.config/f2m/config.ini` on POSIX, `%APPDATA%\f2m\config.ini` on Windows)
  5. `Built-in Defaults` (`CONFIG_DEFAULTS`)
- **Environment Mapping**:
  - `F2M_BASE_URL` → `base_url` (strips trailing slashes)
  - `F2M_MIRRORS` → `mirrors` (comma-separated string split into `list[str]`)
  - `F2M_PROXY` → `proxy` (explicit empty string `""` disables proxy)
  - `F2M_PLAYER` → `player` (case-insensitive: `"auto"`, `"mpv"`, `"vlc"`, `"potplayer"`)
  - `F2M_DOWNLOAD_DIR` → `download_dir` (expands `~`)
  - `F2M_SEARCH_SORT` → `search_sort`
  - `F2M_USER_AGENT` → `user_agent`
  - `F2M_CONFIG` → explicit path to configuration file (overrides file lookup location)
- **Empty Value Semantics**: An explicitly set empty environment variable (e.g. `F2M_PROXY=""`) overrides a lower-priority non-empty value (disables the proxy).
- **Missing File Semantics**: A missing configuration file is a completely normal, non-error condition. Built-in defaults are used silently.

#### 3. Legacy `f2m.conf` Migration Invariants
- **Recognized Legacy Locations**:
  - `os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "f2m.conf")` (frozen binary)
  - `os.path.join(os.path.dirname(os.path.abspath(__file__)), "f2m.conf")` (source install)
- **Migration Trigger**: Occurs ONLY when:
  1. The user-global XDG configuration file (`~/.config/f2m/config.ini`) does NOT exist, AND
  2. A legacy `f2m.conf` DOES exist at the recognized legacy location.
- **Safety & Non-Destructive Invariant**:
  - The legacy `f2m.conf` file is **NEVER deleted or moved**; it is copied into the user XDG location.
  - If an XDG configuration file already exists, migration is completely skipped (idempotent).
  - If the legacy file is malformed or unreadable, a warning is logged to `stderr` and defaults are used; the corrupted file is not copied and no exception is thrown.

#### 4. XDG Platform Behavior & Directory Resolution
- **POSIX (Linux, BSD, macOS)**:
  - If `XDG_CONFIG_HOME` is set and non-empty: `$XDG_CONFIG_HOME/f2m/config.ini`.
  - Otherwise: `~/.config/f2m/config.ini` (standard POSIX convention).
- **Windows**:
  - If `APPDATA` is set: `%APPDATA%\f2m\config.ini`.
  - Otherwise: `~\\AppData\\Roaming\\f2m\\config.ini`.
- **Directory Creation & Permissions**:
  - Directory `f2m/` is created via `os.makedirs(..., exist_ok=True)` on first save.
  - If the user configuration path is entirely unwritable (e.g. read-only `$HOME`), the engine warns to `stderr` and operates in-memory without crashing.

#### 5. Atomic Write Guarantees
- Configuration writes write to a temporary file (`config.ini.tmp.<pid>`) in the target directory and replace the target file via `os.replace()` to ensure atomicity.
- If a write is interrupted or fails (e.g., disk full), the temporary file is cleaned up and the previous configuration file remains completely uncorrupted.

#### 6. Permission Safety (DEF-003 Resolution)
- **Root Cause in Legacy Code**: `f2m.py` defined `CONF_PATH = os.path.dirname(__file__) + "/f2m.conf"` and called `ensure_config()` which immediately executed `save_config()` on first run. When installed into root-owned directories (`/usr/local/bin`), this caused immediate fatal `PermissionError: [Errno 13] Permission denied`.
- **Resolution**: `f2m` **NEVER** writes to the application script or binary installation directory. Configuration persistence targets exclusively the user XDG configuration path (or an explicitly provided local/custom path).

#### 7. Exception Usage Boundaries
- `F2MError`: Root domain exception in `f2m.core.exceptions`.
- `F2MConfigError`: Raised on invalid configuration values (e.g. invalid player name), unwritable custom configuration paths, or corrupt configuration data. Caught cleanly at the CLI boundary to display user-friendly errors (`err(...)`) with exit code `1`.
- `F2MNetworkError` and `F2MParseError` are defined in `f2m.core.exceptions` for architectural completeness and future phases, but Phase 2 does NOT perform premature refactoring of network or scraping exceptions.

---

## 2. User Scenarios & Testing *(mandatory)*

### User Story 1 - System-Wide and Multi-User Configuration (Priority: P1)
As a user who installs `film2media-cli` system-wide (e.g., via `pipx install .` or package manager into `/usr/local/bin`), I want the application to load and persist configuration in my user profile directory, so that the CLI runs and saves settings without encountering permission errors.

**Why this priority**: Solves critical defect `DEF-003` (crashes when executable directory is read-only) and establishes standard multi-user compliance across Linux, macOS, and Windows.

**Independent Test**: Run the CLI in an environment where the application script directory is read-only. Verify that `f2m config set download_dir ~/Movies` writes successfully to the user's XDG/AppData configuration directory without permission failures.

**Acceptance Scenarios**:
1. **Given** a clean system without existing configuration, **When** running `f2m` or `f2m config`, **Then** the application automatically resolves the configuration path to `$XDG_CONFIG_HOME/f2m/config.ini` (or `~/.config/f2m/config.ini` on Linux/macOS, `%APPDATA%\f2m\config.ini` on Windows) and populates default settings.
2. **Given** a read-only application binary directory (e.g., `/usr/local/bin`), **When** updating a configuration key via `f2m config set proxy http://127.0.0.1:8080`, **Then** the configuration file in the user directory is updated successfully and returns exit code `0`.
3. **Given** an invalid configuration path or permission denial in the user directory, **When** saving configuration, **Then** an informative error message is displayed with exit code `1` rather than an unhandled traceback.

---

### User Story 2 - Seamless Legacy Configuration Migration (Priority: P2)
As an existing user who previously customized settings (e.g., custom mirrors, download directory, or proxy) in a legacy `f2m.conf` file, I want my configuration to automatically migrate to the new XDG directory on first run, so that I do not lose my customized settings or have to re-enter them.

**Why this priority**: Preserves Constitution Principle III (Backward Compatibility) and ensures zero disruption for existing users upgrading from v1.1.0.

**Independent Test**: Place an existing `f2m.conf` with custom `base_url` and `download_dir` adjacent to the executable, run `f2m config`, and verify that the values are imported into the new XDG configuration file.

**Acceptance Scenarios**:
1. **Given** no configuration exists in the user XDG directory, but a legacy `f2m.conf` exists adjacent to the script/binary, **When** the application starts, **Then** settings from `f2m.conf` are copied into `~/.config/f2m/config.ini`, an informational message announces the migration, and the new file is used.
2. **Given** both a legacy `f2m.conf` next to the binary and a modern user XDG `config.ini` exist, **When** the application starts, **Then** the modern user XDG configuration takes precedence.
3. **Given** a portable user running `f2m` with a local `./f2m.conf` in their current working directory, **When** the application runs, **Then** the working directory `./f2m.conf` acts as an active portable override.

---

### User Story 3 - Environment Variable and Configuration Precedence (Priority: P3)
As a developer or automation script author, I want to override configuration options (such as proxy or base URL) using environment variables, so that I can configure the CLI ephemerally in containerized or script-driven environments.

**Why this priority**: Enables non-interactive containerized workflows and testing without mutating persistent files on disk.

**Independent Test**: Set `F2M_PROXY="http://proxy:8080"` in the environment, run `f2m config`, and verify that the active proxy reflects the environment variable without overwriting the on-disk file.

**Acceptance Scenarios**:
1. **Given** `F2M_BASE_URL` is set in the environment, **When** the application resolves the base URL, **Then** the environment variable value overrides the on-disk configuration value.
2. **Given** `F2M_CONFIG` is set to a custom file path, **When** the application initializes configuration, **Then** it loads from and saves to the specified custom path.
3. **Given** conflicting values between defaults, on-disk file, environment variable, and explicit CLI flag, **Then** the resolution hierarchy strictly follows: `CLI Flag > Environment Variable > Working Directory Config > User XDG Config > Defaults`.

---

### User Story 4 - Typed and Validated Domain Entities (Priority: P4)
As an application maintainer and developer, I want strongly typed, decoupled domain entities for media posts, seasons, versions, qualities, and episodes with built-in validation, so that downstream scraping, UI rendering, and download execution can rely on consistent data contracts without runtime type errors.

**Why this priority**: Eliminates brittle dictionary-like manipulations and establishes clean architectural separation between network/HTML parsing and CLI presentation.

**Independent Test**: Instantiate `MediaPost`, `Season`, `MediaVersion`, `Quality`, and `Episode` with valid and invalid inputs, verifying normalization and invariant enforcement.

**Acceptance Scenarios**:
1. **Given** valid metadata and episode links, **When** constructing a `MediaPost`, **Then** the entity validates and normalizes all fields (cleaning title noise, stripping trailing URL slashes, validating rating format).
2. **Given** an invalid player name or malformed URL, **When** updating configuration, **Then** the configuration validator rejects the value with an explicit domain error (`F2MConfigError`) rather than causing runtime crashes.

---

### Edge Cases
- **Missing XDG Directories**: If `~/.config/f2m/` does not exist, the configuration engine MUST create the directory path with standard user permissions (`0o700` or `0o755`).
- **Read-Only Filesystem / Live USB**: If both the executable directory and the user home directory are completely read-only, the configuration engine MUST gracefully fall back to in-memory defaults with a diagnostic warning on `stderr` instead of crashing.
- **Corrupted Configuration File**: If the INI file contains syntax errors or unparseable lines, the engine MUST back up or warn the user, load default values, and avoid crashing.
- **Concurrent Execution**: If multiple instances of `f2m` are launched simultaneously, configuration writes MUST be atomic (write to temp file then atomic rename) to avoid file corruption.

---

## 3. Requirements *(mandatory)*

### Functional Requirements

#### Domain Entities (`f2m.core.models`)
- **FR-001**: System MUST provide a typed `SearchResult` entity containing `kind` (`movie` or `series`), `title` (str), `title_fa` (str), `year` (str), `rating` (str), `url` (str), `image` (str), `meta` (str), `is_dub` (bool), and `is_hardsub` (bool).
- **FR-002**: System MUST provide a typed `Episode` entity containing `num` (int >= 1), `url` (valid media URL string), `filename` (unquoted filename), and display `label` (str).
- **FR-003**: System MUST provide a typed `Quality` entity containing `label` (str), `encoder` (str), and `episodes` (list of `Episode`).
- **FR-004**: System MUST provide a typed `MediaVersion` entity containing `key` (`dub` or `hardsub`), `title` (str), and `qualities` (list of `Quality`).
- **FR-005**: System MUST provide a typed `Season` entity containing `number` (int >= 1), `title` (str), and `versions` (list of `MediaVersion`).
- **FR-006**: System MUST provide a typed `MediaPost` entity containing `url` (str), `title` (str), `year` (str), `imdb_id` (str), `rating` (str), `is_series` (bool), `seasons` (list of `Season`), `versions` (list of `MediaVersion`), and `trailer` (str).
- **FR-007**: Domain entities MUST support bidirectional serialization to/from primitive Python dictionaries (`to_dict()` and `from_dict()`) for caching, test assertions, and future JSON export.

#### Configuration Engine (`f2m.core.config`)
- **FR-008**: System MUST resolve user-global configuration paths according to platform conventions:
  - Linux / BSD / POSIX: `$XDG_CONFIG_HOME/f2m/config.ini` (defaulting to `~/.config/f2m/config.ini`).
  - macOS: `~/.config/f2m/config.ini` (or `$XDG_CONFIG_HOME/f2m/config.ini`).
  - Windows: `%APPDATA%\f2m\config.ini`.
- **FR-009**: System MUST support local portable configuration: if a file named `f2m.conf` or `config.ini` exists in the current working directory, it MUST take precedence over the user-global XDG file.
- **FR-010**: System MUST support explicit configuration file path overrides via the `F2M_CONFIG` environment variable.
- **FR-011**: System MUST support configuration overrides via environment variables:
  - `F2M_BASE_URL` → overrides `base_url`
  - `F2M_PROXY` → overrides `proxy`
  - `F2M_PLAYER` → overrides `player`
  - `F2M_DOWNLOAD_DIR` → overrides `download_dir`
  - `F2M_MIRRORS` → overrides `mirrors`
- **FR-012**: System MUST enforce the following configuration priority hierarchy (highest to lowest):
  1. Explicit CLI Flags (reserved for Phase 4)
  2. Environment Variables (`F2M_*`)
  3. Working Directory Local File (`./f2m.conf` or `./config.ini`)
  4. User Global Configuration File (`~/.config/f2m/config.ini` or `%APPDATA%\f2m\config.ini`)
  5. Built-in Default Settings
- **FR-013**: System MUST automatically migrate legacy configuration on first run: if no user-global configuration exists, but a legacy `f2m.conf` is found adjacent to the executable or script, its values MUST be copied into the user-global directory with an informational log on `stderr`.
- **FR-014**: System MUST validate all configuration settings upon loading and updating:
  - `base_url`: Valid HTTP/HTTPS URL scheme.
  - `mirrors`: Comma-separated or list of valid HTTP/HTTPS URLs.
  - `player`: One of `("auto", "mpv", "vlc", "potplayer")` (case-insensitive).
  - `proxy`: Empty string or valid proxy URL scheme (`http://`, `https://`, `socks5://`).
  - `download_dir`: Valid path string, expanding `~` to the user's home directory.
  - `search_sort`: Non-empty string.
  - `user_agent`: Non-empty string.
- **FR-015**: System MUST perform atomic configuration writes (writing to a temporary file in the target directory and renaming atomically) to prevent file corruption during interruptions.

#### Exceptions Hierarchy (`f2m.core.exceptions`)
- **FR-016**: System MUST define a standardized exception hierarchy rooted at `F2MError`:
  - `F2MError` (base domain exception)
  - `F2MConfigError` (configuration parsing, validation, or persistence errors)
  - `F2MNetworkError` (network, mirror, or connection errors)
  - `F2MParseError` (markup parsing or entity validation errors)

#### Integration & Backward Compatibility
- **FR-017**: Existing commands `f2m config` and `f2m config set <key> <value>` MUST continue functioning with identical output formatting and key names.
- **FR-018**: Application script `f2m.py` MUST import and use `f2m.core.models`, `f2m.core.config`, and `f2m.core.exceptions` while keeping existing interactive menus, scraping regexes, and downloader routines operational without regression.

---

### Key Entities

- **ConfigurationProfile**:
  - `base_url`: str (default: `"https://www.myf2ms.top"`)
  - `mirrors`: list[str] (default: `["https://www.myf2m.info", "https://www.myf2ms.top"]`)
  - `proxy`: str (default: `""`)
  - `player`: str (default: `"auto"`)
  - `download_dir`: str (default: `"~/Downloads/f2m"`)
  - `search_sort`: str (default: `"modified_at:desc"`)
  - `user_agent`: str (default: standard Chrome UA)
- **MediaPost**:
  - Encapsulates title, year, IMDb ID, rating, media type, and nested seasons/versions.
- **Season**:
  - Encapsulates season number, title, and versions.
- **MediaVersion**:
  - Encapsulates version key (`dub`/`hardsub`), title, and qualities.
- **Quality**:
  - Encapsulates resolution label, encoder, and episode list.
- **Episode**:
  - Encapsulates episode number, direct download URL, filename, and label.

---

## 4. Success Criteria *(mandatory)*

- **SC-001 (Zero Permission Crashes)**: Running `f2m config` and `f2m config set` succeeds with exit code `0` when the application script directory is read-only.
- **SC-002 (Legacy Migration Parity)**: 100% of custom settings from a legacy `f2m.conf` are preserved and imported into the new XDG configuration location on first run.
- **SC-003 (Configuration Validation)**: Invalid configuration values (e.g. invalid player name, malformed URL) are caught with clear diagnostic messages on `stderr` and exit code `1` rather than causing runtime crashes.
- **SC-004 (Domain Entity Integrity)**: 100% test coverage across entity creation, dictionary serialization, and title/filename normalization.
- **SC-005 (Regression Safety)**: All 8 existing Phase 1 tests continue passing with 0 failures after `f2m.py` adopts `f2m.core`.
- **SC-006 (Documentation Parity)**: Complete synchronization between `README.md` and `README.fa.md` regarding configuration file locations and migration behavior.

---

## 5. Assumptions & Boundaries

### Assumptions
- Python standard library modules `pathlib`, `configparser`, `os`, `sys`, and `dataclasses` are used for the core configuration and entity engine.
- Standard POSIX permissions allow writing to the user's `$HOME` directory.

### Explicit Scope Boundaries (Out of Scope for Phase 2)
- No terminal UI overhaul or `rich` rendering (deferred to Phase 5).
- No scraping algorithm rewrite (deferred to Phase 3).
- No new CLI flags such as `--json` or `--plain` (deferred to Phase 4).
- No downloader changes or `sudo` removal (deferred to Phase 6).
- No modifications to network transport or mirror failover routines.
