import json
import pytest
from f2m.core.exceptions import F2MParseError
from f2m.core.scraper import (
    clean_title,
    parse_filename,
    parse_categories,
    parse_listing,
    parse_post,
    parse_quick_search,
)


def test_clean_title_patterns():
    assert clean_title("دانلود فیلم Inception 2010 با زیرنویس فارسی چسبیده") == "فیلم Inception 2010"
    assert clean_title("دانلود سریال The Last of Us بدون سانسور با دوبله فارسی") == "سریال The Last of Us"
    assert clean_title("Interstellar 2014") == "Interstellar 2014"
    assert clean_title("") == ""


def test_parse_filename_tokens():
    fn, s, e, v = parse_filename("https://dl.f2m.xyz/movies/Test.2024.1080p.Farsi.Dubbed.mkv")
    assert fn == "Test.2024.1080p.Farsi.Dubbed.mkv"
    assert s is None
    assert e is None
    assert v == "dub"

    fn2, s2, e2, v2 = parse_filename("https://dl.f2m.xyz/series/Show/Show.S02E10.720p.Farsi.Sub.mp4")
    assert fn2 == "Show.S02E10.720p.Farsi.Sub.mp4"
    assert s2 == 2
    assert e2 == 10
    assert v2 == "hardsub"


def test_dom_parse_categories(load_fixture):
    html = load_fixture("homepage.html")
    sections, genres = parse_categories(html)

    # Sections
    section_urls = [u for _, u in sections]
    assert "https://www.myf2ms.top/movies/" in section_urls
    assert "https://www.myf2ms.top/series/" in section_urls

    # Genres
    assert len(genres["movie"]) >= 4
    assert any(g[0] == "اکشن" for g in genres["movie"])
    assert any(g[0] == "جنایی" for g in genres["series"])


def test_dom_parse_listing(load_fixture):
    html = load_fixture("search_results.html")
    cards, last_page = parse_listing(html)

    assert len(cards) == 2
    assert last_page == 3
    assert "Oppenheimer" in cards[0].title
    assert cards[0].kind == "movie"
    assert "The Last of Us" in cards[1].title
    assert cards[1].kind == "series"


def test_dom_parse_quick_search(load_fixture):
    raw_json = load_fixture("quick_search.json")
    results = parse_quick_search(raw_json, "https://www.myf2ms.top")

    assert len(results) == 2
    r1 = results[0]
    assert r1.title == "Inception"
    assert r1.title_fa == "تلقین"
    assert r1.kind == "movie"
    assert r1.url == "https://www.myf2ms.top/movies/inception-2010/"
    assert r1.is_dub is True
    assert r1.is_hardsub is True

    r2 = results[1]
    assert r2.title == "Breaking Bad"
    assert r2.kind == "series"


def test_dom_parse_post_movie(load_fixture):
    html = load_fixture("movie_post.html")
    post = parse_post(html, "https://www.myf2ms.top/movies/inception-2010/")

    assert post.is_series is False
    assert "Inception 2010" in post.title
    assert post.imdb_id == "tt1375666"
    assert post.rating == "8.8"
    assert post.year == "2010"
    assert post.trailer == "https://dl.f2m.xyz/trailers/Inception.2010.Trailer.mp4"
    assert len(post.versions) == 2


def test_dom_parse_post_series(load_fixture):
    html = load_fixture("series_post.html")
    post = parse_post(html, "https://www.myf2ms.top/series/loki-2021/")

    assert post.is_series is True
    assert "Loki 2021" in post.title
    assert post.imdb_id == "tt9140554"
    assert post.rating == "8.2"
    assert len(post.seasons) == 2

    s1 = post.seasons[0]
    assert "فصل اول" in s1.title
    assert len(s1.versions[0].qualities) == 2
    assert s1.versions[0].qualities[0].episodes[0].num == 1


def test_dom_parse_edge_cases(load_fixture):
    html = load_fixture("edge_cases_post.html")
    post = parse_post(html, "https://www.myf2ms.top/movies/interstellar-2014/")

    assert post.is_series is False
    assert "Interstellar 2014" in post.title
    assert post.rating == "8.7"
    assert post.imdb_id == "tt0816692"
    assert len(post.versions) == 1
    assert post.versions[0].qualities[0].label == "1080p BluRay"
    assert post.versions[0].qualities[0].encoder == "PSA"
    assert "Interstellar.2014.TRAILER.mp4" in post.trailer


def test_empty_post_raises_parse_error():
    with pytest.raises(F2MParseError, match="Received empty HTML content"):
        parse_post("", "https://example.com/test/")
