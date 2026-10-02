from rich.console import Console
from f2m.core.models import SearchResult
from f2m.ui.views import render_search_table


def test_table_narrow_width_fallback():
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
        )
    ]
    # At 60 columns (< 65), render_search_table switches to Panel compact layout
    card = render_search_table(results, width=60)
    console = Console(record=True, width=60)
    console.print(card)
    output = console.export_text()
    assert "Search Results" in output
    assert "Inception 2010" in output
    assert "★ 8.8/10" in output
    assert "اینسپشن" in output


def test_table_wide_width():
    results = [
        SearchResult(
            kind="series",
            title="Loki",
            title_fa="لوکی",
            year="2021",
            rating="8.2",
            url="https://example.com/loki/",
        )
    ]
    table = render_search_table(results, width=120)
    console = Console(record=True, width=120)
    console.print(table)
    output = console.export_text()
    assert "Loki" in output
    assert "لوکی" in output
    assert "Series" in output
