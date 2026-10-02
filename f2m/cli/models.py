from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class OutputFormat(Enum):
    """Output presentation format."""
    HUMAN = auto()  # Default: colored terminal text, interactive menus
    JSON = auto()   # Machine-readable: valid JSON on stdout
    PLAIN = auto()  # Unix pipeline: unadorned tab- or newline-delimited text


class CliCommand(Enum):
    """Primary CLI subcommands."""
    MENU = auto()        # Bare invocation: interactive welcome banner & menu
    SEARCH = auto()      # Search Film2Media
    URL = auto()         # Inspect a post by URL
    CATEGORIES = auto()  # Browse categories & genres
    CONFIG = auto()      # Configuration inspection & editing
    TEST = auto()        # Connectivity & mirror diagnostic check
    HELP = auto()        # Display usage help
    VERSION = auto()     # Display version information


class ConfigAction(Enum):
    """Sub-action for the config command."""
    SHOW = auto()  # Display all configuration parameters
    GET = auto()   # Retrieve a single configuration key value
    SET = auto()   # Validate and persist a configuration key-value pair


@dataclass(frozen=True)
class CliArgs:
    """Parsed and validated command-line arguments."""
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


@dataclass(frozen=True)
class JsonErrorPayload:
    """Structured error payload emitted to stderr in --json mode."""
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
