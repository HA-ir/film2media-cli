from __future__ import annotations

import os
import sys
from rich.console import Console
from f2m.ui.theme import RICH_THEME

_stdout_console: Console | None = None
_stderr_console: Console | None = None


def is_color_disabled() -> bool:
    """Check if NO_COLOR environment variable is present or color is disabled."""
    return bool(os.environ.get("NO_COLOR"))


def get_stdout_console(no_color: bool = False) -> Console:
    """
    Get configured Rich Console for standard output.
    Respects NO_COLOR, --no-color, non-TTY streams, and terminal width.
    """
    global _stdout_console
    disable_color = no_color or is_color_disabled() or not sys.stdout.isatty()
    if _stdout_console is None or _stdout_console.no_color != disable_color:
        _stdout_console = Console(
            file=sys.stdout,
            theme=RICH_THEME,
            no_color=disable_color,
            highlight=False,
            legacy_windows=False if os.name == "nt" else None,
        )
    return _stdout_console


def get_stderr_console(no_color: bool = False) -> Console:
    """
    Get configured Rich Console for standard error (spinners, diagnostics, logs).
    Respects NO_COLOR, --no-color, and non-TTY streams.
    """
    global _stderr_console
    disable_color = no_color or is_color_disabled() or not sys.stderr.isatty()
    if _stderr_console is None or _stderr_console.no_color != disable_color:
        _stderr_console = Console(
            file=sys.stderr,
            theme=RICH_THEME,
            no_color=disable_color,
            highlight=False,
            legacy_windows=False if os.name == "nt" else None,
        )
    return _stderr_console
