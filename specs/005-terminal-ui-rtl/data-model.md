# Data Model: Phase 5 — Terminal UI & RTL Redesign with Rich

**Feature**: Phase 5 — Terminal UI & RTL Redesign with Rich  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Presentation Entities & UI Component Structures

Phase 5 introduces typed data structures and presentation models in `f2m.ui.models` to encapsulate terminal view configuration, themes, and responsive layout constraints without mutating core business entities in `f2m.core.models`.

```text
       ┌────────────────────────┐
       │      UiThemeConfig     │  (Colors, styles, box borders)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │       UiConsole        │  (stdout_console, stderr_console)
       └───────────┬────────────┘
                   │
     ┌─────────────┴─────────────┐
     ▼                           ▼
┌──────────────┐         ┌──────────────┐
│  MediaTable  │         │  PostHeader  │  (Rich Table / Panel Renderables)
└──────────────┘         └──────────────┘
```

---

## 2. Model Specifications

### 2.1 `UiThemeConfig` (Dataclass)
Defines the semantic terminal styling tokens:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class UiThemeConfig:
    accent: str = "bold cyan"
    primary: str = "bold white"
    secondary: str = "white"
    dim: str = "dim grey"
    success: str = "bold green"
    warning: str = "bold yellow"
    error: str = "bold red"
    rating: str = "bold yellow"
    series: str = "bold magenta"
    movie: str = "bold cyan"
    border: str = "cyan"
    prompt: str = "bold yellow"
```

### 2.2 `TableLayoutMode` (Enum)
Determines whether tables render in full tabular format or compact vertical card layout based on terminal width:

```python
from enum import Enum, auto

class TableLayoutMode(Enum):
    EXPANDED = auto()  # Standard / wide terminals (>= 65 columns): full multi-column table
    COMPACT = auto()   # Narrow terminals (< 65 columns): vertical card listing
```

### 2.3 `MenuItem` (Dataclass)
Represents an item within an interactive selection menu:

```python
@dataclass(frozen=True)
class MenuItem:
    index: int
    label: str
    icon: str = "•"
    key: str = ""
    shortcut: str = ""
```

---

## 3. Relationship with Existing Domain Entities

Phase 5 UI components consume existing Phase 2 domain entities from `f2m.core.models` directly:
- `SearchResult`: Rendered into `MediaTable` rows in search flows.
- `MediaPost` / `Post`: Rendered into `PostHeader` panels and download option trees.
- `Season` / `Episode`: Rendered into episode selection tables with badges.
- `Quality`: Rendered with resolution and encoder tags (`1080p`, `F2M`, `PSA`).
- `ConfigurationProfile`: Rendered into the human-readable configuration table.

Zero modifications to `f2m.core.models` are required.
