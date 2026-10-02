from rich.console import Console

from f2m.core.models import Episode, MediaPost, MediaVersion, Quality, SearchResult
from f2m.ui.bidi import escape_text, get_cell_width, protect_ltr
from f2m.ui.console import get_stdout_console
from f2m.ui.views import render_banner, render_post_header, render_search_table


def test_escape_text_brackets():
    raw = "Inception [bold] [1080p] [/bold]"
    escaped = escape_text(raw)
    assert r"\[bold]" in escaped
    assert r"\[/bold]" in escaped


def test_cell_width_calculation():
    # Persian text with ZWNJ
    persian_text = "فیلم‌های سال ۲۰۲۴"
    width = get_cell_width(persian_text)
    assert width > 0
    assert get_cell_width("") == 0
    assert get_cell_width(None) == 0


def test_protect_ltr():
    url = "https://example.com/dl/movie_2024.mkv"
    assert protect_ltr(url) == url

    # Directional marks stripped
    corrupt_url = f"‎{url}‏"
    assert protect_ltr(corrupt_url) == url


def test_console_initialization():
    con = get_stdout_console()
    assert isinstance(con, Console)


def test_render_banner():
    banner_panel = render_banner("https://www.myf2ms.top")
    console = Console(record=True, width=80)
    console.print(banner_panel)
    output = console.export_text()
    assert "⚡ F2M" in output
    assert "film2media terminal client" in output
    assert "https://www.myf2ms.top" in output


def test_render_search_table():
    results = [
        SearchResult(
            kind="movie",
            title="Inception 2010",
            title_fa="اینسپشن",
            year="2010",
            rating="8.8",
            url="https://example.com/inception/",
            image="https://example.com/poster.jpg",
            meta="دوبله فارسی",
        ),
        SearchResult(
            kind="series",
            title="Loki",
            title_fa="لوکی",
            year="2021",
            rating="8.2",
            url="https://example.com/loki/",
        ),
    ]
    table = render_search_table(results, width=80)
    console = Console(record=True, width=80)
    console.print(table)
    output = console.export_text()
    assert "Inception" in output
    assert "2010" in output
    assert "اینسپشن" in output
    assert "Loki" in output
    assert "8.8/10" in output
    assert "Movie" in output
    assert "Ser" in output


def test_render_post_header():
    ep = Episode(num=1, label="Part 1", url="https://example.com/m.mkv")
    q = Quality(label="1080p", encoder="F2M", episodes=[ep])
    v = MediaVersion(key="dub", title="Dubbed", qualities=[q])
    post = MediaPost(
        title="Inception 2010",
        url="https://example.com/inception/",
        is_series=False,
        rating="8.8",
        imdb_id="tt1375666",
        year="2010",
        trailer="https://example.com/trailer.mp4",
        versions=[v],
    )
    panel = render_post_header(post)
    console = Console(record=True, width=80)
    console.print(panel)
    output = console.export_text()
    assert "Inception 2010" in output
    assert "tt1375666" in output
    assert "★ 8.8/10" in output
    assert "movie" in output
    assert "trailer available" in output
