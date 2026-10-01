import pytest
from f2m import (
    clean_title,
    parse_filename,
    parse_selection,
    parse_categories,
    parse_listing,
    parse_post,
)


def test_clean_title():
    raw1 = "دانلود فیلم Inception 2010 با زیرنویس فارسی چسبیده"
    assert clean_title(raw1) == "فیلم Inception 2010"

    raw2 = "دانلود سریال The Last of Us بدون سانسور با دوبله فارسی"
    assert clean_title(raw2) == "سریال The Last of Us"

    raw3 = "Dune Part Two 2024"
    assert clean_title(raw3) == "Dune Part Two 2024"


def test_parse_filename():
    url_movie = "https://dl.f2m.xyz/movies/Inception.2010.1080p.Farsi.Dubbed.mkv"
    fn, season, episode, version = parse_filename(url_movie)
    assert fn == "Inception.2010.1080p.Farsi.Dubbed.mkv"
    assert season is None
    assert episode is None
    assert version == "dub"

    url_series = "https://dl.f2m.xyz/series/Loki/S01/Loki.S01E05.720p.HardSub.mkv"
    fn, season, episode, version = parse_filename(url_series)
    assert fn == "Loki.S01E05.720p.HardSub.mkv"
    assert season == 1
    assert episode == 5
    assert version == "hardsub"


def test_parse_selection():
    # Empty
    assert parse_selection("", 10) == []
    # Wildcards
    assert parse_selection("all", 5) == [0, 1, 2, 3, 4]
    assert parse_selection("*", 3) == [0, 1, 2]
    assert parse_selection("a", 2) == [0, 1]

    # Single number (1-based to 0-based)
    assert parse_selection("1", 5) == [0]
    assert parse_selection("3", 5) == [2]

    # Comma separated
    assert parse_selection("1,3,5", 5) == [0, 2, 4]

    # Persian comma separated
    assert parse_selection("1،2،4", 5) == [0, 1, 3]

    # Range
    assert parse_selection("2-4", 5) == [1, 2, 3]

    # Mixed range and commas
    assert parse_selection("1, 3-5", 6) == [0, 2, 3, 4]

    # Out of bounds ignored
    assert parse_selection("0, 99", 5) == []


def test_parse_categories(load_fixture):
    html = load_fixture("homepage.html")
    sections, genres = parse_categories(html)

    # Sections
    section_urls = [url for _, url in sections]
    assert "https://www.myf2ms.top/movies/" in section_urls
    assert "https://www.myf2ms.top/series/" in section_urls
    assert "https://www.myf2ms.top/250tmdb/" in section_urls

    # Genres
    assert len(genres["movie"]) >= 4
    movie_genre_names = [name for name, _ in genres["movie"]]
    assert "اکشن" in movie_genre_names
    assert "کمدی" in movie_genre_names

    assert len(genres["series"]) >= 3
    series_genre_names = [name for name, _ in genres["series"]]
    assert "جنایی" in series_genre_names


def test_parse_listing(load_fixture):
    html = load_fixture("search_results.html")
    cards, last_page = parse_listing(html)

    assert len(cards) == 2
    assert last_page == 3

    oppenheimer = cards[0]
    assert oppenheimer.url == "https://www.myf2ms.top/movies/oppenheimer-2023/"
    assert "Oppenheimer" in oppenheimer.title
    assert oppenheimer.year == "2023"
    assert oppenheimer.kind == "movie"

    tlou = cards[1]
    assert tlou.url == "https://www.myf2ms.top/series/the-last-of-us-2023/"
    assert "The Last of Us" in tlou.title
    assert tlou.kind == "series"


def test_parse_post_movie(load_fixture):
    html = load_fixture("movie_post.html")
    url = "https://www.myf2ms.top/movies/inception-2010/"
    post = parse_post(html, url)

    assert post.is_series is False
    assert "Inception 2010" in post.title
    assert post.year == "2010"
    assert post.imdb_id == "tt1375666"
    assert post.rating == "8.8"
    assert post.trailer == "https://dl.f2m.xyz/trailers/Inception.2010.Trailer.mp4"

    # Versions
    assert len(post.versions) == 2
    dubbed = post.versions[0]
    assert dubbed.key == "dub"
    assert len(dubbed.qualities) == 2
    assert dubbed.qualities[0].label == "1080p BluRay"
    assert dubbed.qualities[0].encoder == "F2M"
    assert len(dubbed.qualities[0].episodes) == 1
    assert dubbed.qualities[0].episodes[0].url == "https://dl.f2m.xyz/movies/Inception.2010.1080p.Farsi.Dubbed.mkv"


def test_parse_post_series(load_fixture):
    html = load_fixture("series_post.html")
    url = "https://www.myf2ms.top/series/loki-2021/"
    post = parse_post(html, url)

    assert post.is_series is True
    assert "Loki 2021" in post.title
    assert post.imdb_id == "tt9140554"
    assert post.rating == "8.2"

    # Seasons
    assert len(post.seasons) == 2
    season_1 = post.seasons[0]
    assert "فصل اول" in season_1.title
    assert len(season_1.versions) == 1

    s1_sub = season_1.versions[0]
    assert len(s1_sub.qualities) == 2
    q1 = s1_sub.qualities[0]
    assert q1.label == "1080p x265"
    assert len(q1.episodes) == 2
    assert q1.episodes[0].num == 1
    assert q1.episodes[1].num == 2
