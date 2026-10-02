import os
import subprocess
import sys
from pathlib import Path
import pytest
from f2m.core.exceptions import F2MParseError
from f2m.core.scraper import parse_post, parse_listing, parse_quick_search

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_cli(*args, env=None) -> subprocess.CompletedProcess:
    """Helper to run the CLI via subprocess."""
    full_env = os.environ.copy()
    full_env["PYTHONIOENCODING"] = "utf-8"
    if env:
        full_env.update(env)
    cmd = [sys.executable, str(REPO_ROOT / "f2m.py")] + list(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=full_env,
        cwd=str(REPO_ROOT),
    )


def test_e2e_search_and_post_parsing_offline(load_fixture):
    """
    E2E-1 & E2E-2: Validate search and post parsing workflows end-to-end
    producing typed domain models from offline fixtures.
    """
    html_search = load_fixture("search_results.html")
    cards, last_page = parse_listing(html_search)
    assert len(cards) == 2
    assert last_page == 3

    html_movie = load_fixture("movie_post.html")
    post_movie = parse_post(html_movie, "https://www.myf2ms.top/movies/inception-2010/")
    assert "Inception 2010" in post_movie.title
    assert post_movie.imdb_id == "tt1375666"
    assert len(post_movie.versions) == 2

    html_series = load_fixture("series_post.html")
    post_series = parse_post(html_series, "https://www.myf2ms.top/series/loki-2021/")
    assert post_series.is_series is True
    assert len(post_series.seasons) == 2


def test_e2e_malformed_html_error_reporting():
    """
    E2E-4: Malformed HTML error reporting raises structured F2MParseError.
    """
    with pytest.raises(F2MParseError):
        parse_post("", "https://example.com/bad/")


def test_e2e_cli_test_command_offline_guard(monkeypatch):
    """
    E2E-3: CLI 'f2m test' command runs cleanly and handles unreachable network
    by displaying actionable diagnostic messages.
    """
    res = run_cli("test")
    # In offline test environment, it should either report reachable (if mock exists)
    # or output a clean error without unhandled traceback
    assert res.returncode == 0
    assert ("base_url:" in res.stdout) or ("base_url:" in res.stderr)
    assert "Traceback (most recent call last)" not in res.stderr
