# Data Model: Phase 4 — CLI Argument & Output Modernization

**Feature**: Phase 4 — CLI Argument & Output Modernization  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Domain Entities & Type Definitions

Phase 4 introduces typed models in `f2m.cli.models` (or `f2m.cli.parser`) to represent command-line arguments, execution options, and formatted results cleanly without modifying the core business models in `f2m.core.models`.

```text
       ┌─────────────────┐
       │   OutputFormat  │  (HUMAN, JSON, PLAIN)
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │     CliArgs     │
       ├─────────────────┤
       │ command         │ ───► CliCommand (SEARCH, URL, CATEGORIES, CONFIG, TEST, HELP, VERSION, MENU)
       │ format          │ ───► OutputFormat
       │ query           │
       │ url             │
       │ config_action   │ ───► ConfigAction (SHOW, GET, SET)
       │ config_key      │
       │ config_val      │
       │ config_path     │
       │ no_color        │
       └─────────────────┘
```

---

## 2. Model Specifications

### 2.1 `OutputFormat` (Enum)
Defines the output serialization mode requested by the caller:

```python
from enum import Enum, auto

class OutputFormat(Enum):
    HUMAN = auto()  # Default: colored terminal text, interactive menus, status icons
    JSON = auto()   # Machine-readable: deterministic unadorned JSON on stdout
    PLAIN = auto()  # Unix pipeline: unadorned tab- or newline-delimited text on stdout
```

### 2.2 `CliCommand` (Enum)
Defines the primary operation to execute:

```python
class CliCommand(Enum):
    MENU = auto()        # Default bare invocation: launches interactive welcome banner and menu
    SEARCH = auto()      # Search Film2Media for movies/series
    URL = auto()         # Inspect a post by direct URL
    CATEGORIES = auto()  # Explore sections and genres
    CONFIG = auto()      # Configuration inspection and editing
    TEST = auto()        # Connectivity and mirror diagnostic check
    HELP = auto()        # Display usage assistance
    VERSION = auto()     # Display version information
```

### 2.3 `ConfigAction` (Enum)
Specifies the configuration operation:

```python
class ConfigAction(Enum):
    SHOW = auto()  # Display all configuration keys and values
    GET = auto()   # Retrieve a single configuration key value
    SET = auto()   # Validate and persist a configuration key-value pair
```

### 2.4 `CliArgs` (Dataclass)
Represents the validated, normalized command-line arguments:

```python
@dataclass(frozen=True)
class CliArgs:
    command: CliCommand
    format: OutputFormat = OutputFormat.HUMAN
    query: str | None = None
    url: str | None = None
    config_action: ConfigAction = ConfigAction.SHOW
    config_key: str | None = None
    config_val: str | None = None
    config_path: str | None = None
    no_color: bool = False
    raw_args: list[str] = field(default_factory=list)
```

**Validation & Invariants**:
- `format == OutputFormat.JSON and format == OutputFormat.PLAIN` is impossible due to enum representation; parser rejects simultaneous `--json` and `--plain` before constructing `CliArgs`.
- If `command == CliCommand.SEARCH` and `format != OutputFormat.HUMAN`, `query` must be a non-empty string.
- If `command == CliCommand.URL`, `url` must be a non-empty string.
- If `command == CliCommand.CONFIG` and `config_action == ConfigAction.GET`, `config_key` must be a non-empty string.
- If `command == CliCommand.CONFIG` and `config_action == ConfigAction.SET`, both `config_key` and `config_val` must be non-empty strings.

### 2.5 `JsonErrorPayload` (Dataclass)
Represents structured error output emitted to `stderr` in `--json` mode:

```python
@dataclass(frozen=True)
class JsonErrorPayload:
    error: bool = True
    code: str = "RUNTIME_ERROR"
    message: str = ""
    exit_code: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.error,
            "code": self.code,
            "message": self.message,
            "exit_code": self.exit_code,
        }
```

### 2.6 `ExecutionResult` (Dataclass)
Encapsulates the result of a non-interactive command execution:

```python
@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int
    data: Any = None
    error_message: str | None = None
    error_code: str | None = None
```

---

## 3. Relationship with Existing Domain Entities

Phase 4 formats existing domain models from `f2m.core.models` directly:
- `SearchResult.to_dict()` -> List elements in `f2m search --json`.
- `MediaPost.to_dict()` -> Object payload in `f2m url <url> --json`.
- `ConfigurationProfile.to_dict()` -> Object payload in `f2m config --json`.
- `Card` -> Used in plain/human listing representations.

Zero modifications to `f2m/core/models.py` are required.
