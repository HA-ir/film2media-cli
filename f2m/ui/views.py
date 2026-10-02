from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Generator

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from f2m.core.models import MediaPost, Quality, SearchResult
from f2m.ui.bidi import escape_text, protect_ltr
from f2m.ui.console import get_stderr_console, get_stdout_console
from f2m.ui.models import MenuItem

VERSION = "1.1.0"


def render_banner(base_url: str = "") -> Panel:
    """Render application welcome banner inside a styled Rich Panel."""
    content = Text()
    content.append("⚡ F2M", style="bold cyan")
    content.append(" · film2media terminal client ", style="dim")
    content.append(f"v{VERSION}\n", style="bold white")
    if base_url:
        content.append("base url: ", style="dim")
        content.append(protect_ltr(base_url), style="cyan")

    return Panel(
        content,
        box=box.ROUNDED,
        border_style="cyan",
        expand=False,
        padding=(0, 2),
    )


def render_search_table(results: list[SearchResult], width: int | None = None) -> Table | Panel:
    """
    Render search results using an aligned Rich Table.
    Falls back to a compact card listing if width is restricted (< 65 cols).
    """
    console = get_stdout_console()
    active_width = width or console.width or 80

    if active_width < 65:
        # Narrow terminal compact fallback
        body = Text()
        for i, r in enumerate(results, 1):
            kind_icon = "📺" if r.kind == "series" else "🎞"
            body.append(f"{str(i).rjust(2)}. ", style="bold cyan")
            body.append(f"{kind_icon} ", style="bold magenta" if r.kind == "series" else "bold cyan")
            body.append(f"{escape_text(r.title)} ", style="bold white")
            if r.year:
                body.append(f"({escape_text(r.year)}) ", style="dim")
            if r.rating:
                body.append(f"★ {escape_text(r.rating)}/10", style="bold yellow")
            if r.title_fa:
                body.append(f"\n    {escape_text(r.title_fa)}", style="italic white")
            body.append("\n")
        return Panel(body, title="Search Results", box=box.ROUNDED, border_style="cyan")

    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold white",
        expand=True,
    )
    table.add_column("#", justify="right", style="cyan", width=3, no_wrap=True)
    table.add_column("Type", justify="center", width=9, no_wrap=True)
    table.add_column("Original Title", style="bold white", ratio=3, overflow="fold")
    table.add_column("Persian Title", style="white", ratio=3, overflow="fold")
    table.add_column("Year", justify="center", style="dim", width=6, no_wrap=True)
    table.add_column("Rating", justify="center", style="bold yellow", width=9, no_wrap=True)
    table.add_column("Badges", style="dim", width=12, overflow="ellipsis")

    for i, r in enumerate(results, 1):
        kind_str = "📺 Series" if r.kind == "series" else "🎞 Movie"
        badges_list = []
        if getattr(r, "is_dub", False):
            badges_list.append("Dub")
        if getattr(r, "is_hardsub", False):
            badges_list.append("Sub")
        badges = " ".join(badges_list) if badges_list else (escape_text(r.meta) if r.meta else "")
        rating_str = f"★ {r.rating}/10" if r.rating else ""

        table.add_row(
            str(i),
            kind_str,
            escape_text(r.title),
            escape_text(r.title_fa),
            escape_text(r.year),
            rating_str,
            badges,
        )
    return table


def render_post_header(post: MediaPost) -> Panel:
    """Render media post metadata details inside a styled Rich Panel."""
    content = Text()
    content.append(f"{escape_text(post.title)}\n", style="bold white")
    if post.rating:
        content.append(f"★ {escape_text(post.rating)}/10  ", style="bold yellow")
    if post.year:
        content.append(f"{escape_text(post.year)}  ", style="dim")
    if post.imdb_id:
        content.append(f"{escape_text(post.imdb_id)}  ", style="dim")
    kind_label = "📺 series" if post.is_series else "🎞 movie"
    content.append(f"{kind_label}\n", style="bold magenta" if post.is_series else "bold cyan")

    if post.trailer:
        content.append("🎬 trailer available\n", style="italic dim")

    return Panel(
        content,
        title="Media Information",
        box=box.ROUNDED,
        border_style="cyan",
        expand=False,
    )


def render_menu(title: str, items: list[MenuItem]) -> Table:
    """Render interactive selection menu options using an aligned Rich Table."""
    table = Table(
        title=f"[bold white]{escape_text(title)}[/bold white]" if title else None,
        box=box.ROUNDED,
        border_style="cyan",
        show_header=False,
        expand=False,
        padding=(0, 1),
    )
    table.add_column("Index", justify="right", style="bold cyan", width=3)
    table.add_column("Icon", justify="center", width=3)
    table.add_column("Label", style="bold white")

    for item in items:
        table.add_row(str(item.index), item.icon, escape_text(item.label))
    return table


def render_quality_table(qualities: list[Quality]) -> Table:
    """Render quality choices with resolution labels, encoder badges, and episode counts."""
    table = Table(
        title="[bold white]Available Qualities[/bold white]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold white",
        expand=False,
    )
    table.add_column("#", justify="right", style="cyan", width=3)
    table.add_column("Quality", style="bold white")
    table.add_column("Encoder", style="dim")
    table.add_column("Files", justify="right", style="dim")

    for i, q in enumerate(qualities, 1):
        encoder = escape_text(q.encoder) if q.encoder and q.encoder.lower() != "unknown" else "—"
        count_str = f"{len(q.episodes)} file(s)"
        table.add_row(str(i), escape_text(q.label), encoder, count_str)
    return table


@contextmanager
def status_spinner(text: str = "fetching", enabled: bool = True) -> Generator[None, None, None]:
    """
    Transient status spinner context manager.
    Runs inert if enabled=False, stderr is not a TTY, or under --json/--plain.
    """
    console = get_stderr_console()
    if not enabled or not sys.stderr.isatty():
        yield
        return

    with console.status(f"[cyan]{escape_text(text)}…[/cyan]"):
        yield
