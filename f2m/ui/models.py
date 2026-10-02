from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TableLayoutMode(Enum):
    """Determines table presentation mode based on terminal width."""
    EXPANDED = auto()  # Standard / wide terminals (>= 65 cols): multi-column table
    COMPACT = auto()   # Narrow terminals (< 65 cols): vertical card listing


@dataclass(frozen=True)
class UiThemeConfig:
    """Semantic terminal styling tokens mapping to Rich styles."""
    accent: str = "bold cyan"
    primary: str = "bold white"
    secondary: str = "white"
    dim: str = "dim"
    success: str = "bold green"
    warning: str = "bold yellow"
    error: str = "bold red"
    rating: str = "bold yellow"
    series: str = "bold magenta"
    movie: str = "bold cyan"
    border: str = "cyan"
    prompt: str = "bold yellow"


@dataclass(frozen=True)
class MenuItem:
    """Represents an item within an interactive selection menu."""
    index: int
    label: str
    icon: str = "•"
    key: str = ""
    shortcut: str = ""
