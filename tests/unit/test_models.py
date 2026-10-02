import pytest
from f2m.core.models import (
    SearchResult,
    Card,
    Episode,
    Quality,
    MediaVersion,
    Version,
    Season,
    MediaPost,
    Post,
)


def test_search_result_normalization_and_serialization():
    data = {
        "kind": "SERIES",
        "title": "<em>Breaking</em> Bad",
        "title_fa": "بریکینگ بد",
        "year": "2008",
        "rating": "9.5",
        "url": "https://www.myf2ms.top/series/breaking-bad/",
        "image": "https://www.myf2ms.top/posters/bb.jpg",
        "meta": "جنایی، درام",
        "is_dub": True,
        "is_hardsub": False,
        "unexpected_extra_key": "ignore_me",
    }
    sr = SearchResult.from_dict(data)
    assert sr.kind == "series"
    assert sr.title == "Breaking Bad"
    assert sr.title_fa == "بریکینگ بد"
    assert sr.is_dub is True

    # Round trip
    d = sr.to_dict()
    assert d["title"] == "Breaking Bad"
    assert "unexpected_extra_key" not in d
    sr2 = SearchResult.from_dict(d)
    assert sr2 == sr


def test_card_model():
    card = Card(
        url="https://example.com/post/",
        title="Sample Movie",
        year="2023",
        kind="movie",
    )
    d = card.to_dict()
    assert d["title"] == "Sample Movie"
    card2 = Card.from_dict(d)
    assert card2 == card


def test_episode_model():
    # Auto label & filename derivation
    ep = Episode(num=1, url="https://dl.f2m.xyz/movies/test%20file.mkv")
    assert ep.filename == "test file.mkv"
    assert ep.label == "قسمت 1"

    # Custom label & filename
    ep2 = Episode(
        num=2,
        url="https://dl.f2m.xyz/ep2.mp4",
        filename="custom_ep2.mp4",
        label="Special Ep",
    )
    assert ep2.filename == "custom_ep2.mp4"
    assert ep2.label == "Special Ep"

    # to_dict / from_dict
    d = ep2.to_dict()
    assert d["num"] == 2
    ep2_recovered = Episode.from_dict(d)
    assert ep2_recovered == ep2


def test_quality_and_version_models():
    ep1 = Episode(num=1, url="https://dl.f2m.xyz/ep1.mkv")
    ep2 = Episode(num=2, url="https://dl.f2m.xyz/ep2.mkv")
    q = Quality(label="1080p BluRay", encoder="unknown", episodes=[ep1, ep2])
    assert q.encoder == ""  # 'unknown' normalized to empty string
    assert len(q.episodes) == 2

    v = MediaVersion(key="DUB", title="نسخه دوبله", qualities=[q])
    assert v.key == "dub"  # normalized lower
    assert Version is MediaVersion  # alias test

    d = v.to_dict()
    v_recovered = Version.from_dict(d)
    assert v_recovered.key == "dub"
    assert len(v_recovered.qualities) == 1
    assert len(v_recovered.qualities[0].episodes) == 2


def test_season_and_post_models():
    assert Post is MediaPost  # alias test

    ep = Episode(num=1, url="https://dl.f2m.xyz/loki.s01e01.mkv")
    q = Quality(label="720p", encoder="PSA", episodes=[ep])
    v = MediaVersion(key="hardsub", title="زیرنویس", qualities=[q])
    season = Season(title="فصل اول", number=1, versions=[v])

    post = MediaPost(
        url="https://www.myf2ms.top/series/loki-2021/",
        title="Loki 2021",
        year="2021",
        imdb_id="tt9140554",
        rating="8.2",
        is_series=True,
        seasons=[season],
        trailer="https://dl.f2m.xyz/trailer.mp4",
    )

    d = post.to_dict()
    assert d["is_series"] is True
    assert d["title"] == "Loki 2021"

    post_recovered = Post.from_dict(d)
    assert post_recovered.title == "Loki 2021"
    assert len(post_recovered.seasons) == 1
    assert post_recovered.seasons[0].versions[0].qualities[0].episodes[0].num == 1
