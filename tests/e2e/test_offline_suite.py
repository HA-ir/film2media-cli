import socket
import pytest
from f2m import parse_listing, parse_post, clean_title


def test_entire_suite_runs_offline(block_network, load_fixture):
    """
    E2E acceptance scenario: verifies that parsing operations,
    fixtures, and calculations execute under strict offline isolation
    with network sockets blocked.
    """
    # Verify socket is blocked
    with pytest.raises(RuntimeError, match="Network access attempted"):
        socket.create_connection(("1.1.1.1", 80))

    # Test full offline parsing pipeline on recorded HTML
    html_search = load_fixture("search_results.html")
    cards, last_page = parse_listing(html_search)
    assert len(cards) > 0
    assert last_page >= 1

    html_movie = load_fixture("movie_post.html")
    post = parse_post(html_movie, "https://www.myf2ms.top/movies/inception-2010/")
    assert "Inception 2010" in post.title
    assert len(post.versions) > 0
