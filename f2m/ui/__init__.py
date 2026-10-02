"""
UI presentation subsystem for film2media-cli.
"""

from f2m.ui.models import MenuItem, TableLayoutMode, UiThemeConfig
from f2m.ui.console import get_stderr_console, get_stdout_console, is_color_disabled
from f2m.ui.theme import DEFAULT_THEME_CONFIG, RICH_THEME
from f2m.ui.bidi import escape_text, get_cell_width, protect_ltr
from f2m.ui.views import (
    render_banner,
    render_menu,
    render_post_header,
    render_quality_table,
    render_search_table,
    status_spinner,
)

__all__ = [
    "MenuItem",
    "TableLayoutMode",
    "UiThemeConfig",
    "get_stdout_console",
    "get_stderr_console",
    "is_color_disabled",
    "DEFAULT_THEME_CONFIG",
    "RICH_THEME",
    "escape_text",
    "get_cell_width",
    "protect_ltr",
    "render_banner",
    "render_menu",
    "render_post_header",
    "render_quality_table",
    "render_search_table",
    "status_spinner",
]
