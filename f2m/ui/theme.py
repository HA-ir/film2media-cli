from __future__ import annotations

from rich.theme import Theme
from f2m.ui.models import UiThemeConfig

DEFAULT_THEME_CONFIG = UiThemeConfig()

RICH_THEME = Theme({
    "accent": DEFAULT_THEME_CONFIG.accent,
    "primary": DEFAULT_THEME_CONFIG.primary,
    "secondary": DEFAULT_THEME_CONFIG.secondary,
    "dim": DEFAULT_THEME_CONFIG.dim,
    "success": DEFAULT_THEME_CONFIG.success,
    "warning": DEFAULT_THEME_CONFIG.warning,
    "error": DEFAULT_THEME_CONFIG.error,
    "rating": DEFAULT_THEME_CONFIG.rating,
    "series": DEFAULT_THEME_CONFIG.series,
    "movie": DEFAULT_THEME_CONFIG.movie,
    "border": DEFAULT_THEME_CONFIG.border,
    "prompt": DEFAULT_THEME_CONFIG.prompt,
})
