import json
from f2m.cli.formatters import JsonFormatter, PlainFormatter
from f2m.core.config import ConfigurationProfile
from f2m.core.models import Episode, MediaPost, MediaVersion, Quality, SearchResult


def test_json_formatter_search():
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
    formatted = JsonFormatter.format_search(results)
    parsed = json.loads(formatted)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["title"] == "Inception 2010"
    assert parsed[0]["rating"] == "8.8"
    assert "\033[" not in formatted


def test_json_formatter_post():
    ep = Episode(num=1, label="Part 1", url="https://dl.example.com/movie.1080p.mkv")
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
        seasons=[],
    )
    formatted = JsonFormatter.format_post(post)
    parsed = json.loads(formatted)
    assert parsed["title"] == "Inception 2010"
    assert parsed["versions"][0]["qualities"][0]["episodes"][0]["url"] == "https://dl.example.com/movie.1080p.mkv"
    assert "\033[" not in formatted


def test_json_formatter_categories():
    sections = [("Movies", "https://example.com/movies/"), ("Series", "https://example.com/series/")]
    genres = {
        "movie": [("Action", "https://example.com/action/")],
        "series": [("Drama", "https://example.com/drama/")],
    }
    formatted = JsonFormatter.format_categories(sections, genres)
    parsed = json.loads(formatted)
    assert len(parsed["sections"]) == 2
    assert len(parsed["genres"]["movie"]) == 1
    assert len(parsed["genres"]["series"]) == 1


def test_json_formatter_config_and_error():
    profile = ConfigurationProfile(
        base_url="https://example.com",
        mirrors=["https://mirror1.com"],
        proxy="",
        player="auto",
        download_dir="~/Downloads",
        search_sort="date",
        user_agent="TestUA",
    )
    formatted_cfg = JsonFormatter.format_config(profile)
    parsed_cfg = json.loads(formatted_cfg)
    assert parsed_cfg["base_url"] == "https://example.com"
    assert parsed_cfg["mirrors"] == ["https://mirror1.com"]

    formatted_err = JsonFormatter.format_error("CONFIG_ERROR", "Invalid key", 3)
    parsed_err = json.loads(formatted_err)
    assert parsed_err["error"] is True
    assert parsed_err["code"] == "CONFIG_ERROR"
    assert parsed_err["exit_code"] == 3


def test_plain_formatter_search():
    results = [
        SearchResult(
            kind="movie",
            title="Inception 2010",
            title_fa="",
            year="2010",
            rating="8.8",
            url="https://example.com/inception/",
        ),
        SearchResult(
            kind="series",
            title="Loki",
            title_fa="",
            year="2021",
            rating="8.2",
            url="https://example.com/loki/",
        ),
    ]
    formatted = PlainFormatter.format_search(results)
    lines = formatted.split("\n")
    assert len(lines) == 2
    assert lines[0] == "movie\tInception 2010\t2010\t8.8\thttps://example.com/inception/"
    assert lines[1] == "series\tLoki\t2021\t8.2\thttps://example.com/loki/"
    assert "\033[" not in formatted


def test_plain_formatter_post_links():
    ep1 = Episode(num=1, label="E01", url="https://dl.example.com/ep01.mkv")
    ep2 = Episode(num=2, label="E02", url="https://dl.example.com/ep02.mkv")
    q = Quality(label="720p", encoder="F2M", episodes=[ep1, ep2])
    v = MediaVersion(key="sub", title="Subbed", qualities=[q])
    post = MediaPost(
        title="Loki",
        url="https://example.com/loki/",
        is_series=False,
        versions=[v],
    )
    formatted = PlainFormatter.format_post(post)
    lines = formatted.split("\n")
    assert lines == [
        "https://dl.example.com/ep01.mkv",
        "https://dl.example.com/ep02.mkv",
    ]


def test_plain_formatter_config_and_test():
    profile = ConfigurationProfile(
        base_url="https://example.com",
        mirrors=["https://m1.com", "https://m2.com"],
        proxy="",
        player="mpv",
        download_dir="/tmp",
        search_sort="date",
        user_agent="UA",
    )
    formatted = PlainFormatter.format_config(profile)
    assert "base_url=https://example.com" in formatted
    assert "mirrors=https://m1.com,https://m2.com" in formatted
    assert "player=mpv" in formatted

    assert PlainFormatter.format_config_get("https://example.com") == "https://example.com"
    assert PlainFormatter.format_config_set("proxy", "http://127.0.0.1:8080") == "OK: proxy=http://127.0.0.1:8080"
    assert PlainFormatter.format_test(True, "https://example.com", "example.com") == "OK\thttps://example.com\texample.com"
    assert PlainFormatter.format_test(False, "https://example.com", "timeout") == "FAIL\thttps://example.com\ttimeout"
