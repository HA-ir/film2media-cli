from __future__ import annotations

import json
import sys
from typing import Any

from f2m.cli.models import JsonErrorPayload
from f2m.core.config import ConfigurationProfile
from f2m.core.models import MediaPost, SearchResult


def emit_stdout(text: str) -> None:
    """Write text to standard output and flush."""
    if not text:
        return
    if not text.endswith("\n"):
        text += "\n"
    sys.stdout.write(text)
    sys.stdout.flush()


def emit_stderr(text: str) -> None:
    """Write text to standard error and flush."""
    if not text:
        return
    if not text.endswith("\n"):
        text += "\n"
    sys.stderr.write(text)
    sys.stderr.flush()


class JsonFormatter:
    """Formatter for machine-readable JSON output streams."""

    @staticmethod
    def format_search(results: list[SearchResult]) -> str:
        return json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False)

    @staticmethod
    def format_post(post: MediaPost) -> str:
        return json.dumps(post.to_dict(), indent=2, ensure_ascii=False)

    @staticmethod
    def format_categories(sections: list[tuple[str, str]], genres: dict[str, list[tuple[str, str]]]) -> str:
        payload = {
            "sections": [{"name": s[0], "url": s[1]} for s in sections],
            "genres": {
                "movie": [{"name": g[0], "url": g[1]} for g in genres.get("movie", [])],
                "series": [{"name": g[0], "url": g[1]} for g in genres.get("series", [])],
            },
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @staticmethod
    def format_config(profile: ConfigurationProfile) -> str:
        return json.dumps(profile.to_dict(), indent=2, ensure_ascii=False)

    @staticmethod
    def format_config_get(key: str, val: Any) -> str:
        return json.dumps({"key": key, "value": val}, indent=2, ensure_ascii=False)

    @staticmethod
    def format_config_set(key: str, val: Any, file_path: str) -> str:
        return json.dumps({
            "success": True,
            "key": key,
            "value": val,
            "file_path": file_path,
        }, indent=2, ensure_ascii=False)

    @staticmethod
    def format_test(
        reachable: bool,
        base_url: str,
        final_host: str,
        sections_count: int,
        movie_genres_count: int,
        series_genres_count: int,
        error: str | None = None,
    ) -> str:
        payload = {
            "reachable": reachable,
            "base_url": base_url,
            "final_host": final_host,
            "sections_count": sections_count,
            "movie_genres_count": movie_genres_count,
            "series_genres_count": series_genres_count,
            "error": error,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @staticmethod
    def format_error(error_code: str, message: str, exit_code: int) -> str:
        payload = JsonErrorPayload(error=True, code=error_code, message=message, exit_code=exit_code)
        return json.dumps(payload.to_dict(), indent=2, ensure_ascii=False)


class PlainFormatter:
    """Formatter for plain, unadorned Unix pipeline streams."""

    @staticmethod
    def format_search(results: list[SearchResult]) -> str:
        lines: list[str] = []
        for r in results:
            lines.append(f"{r.kind}\t{r.title}\t{r.year}\t{r.rating}\t{r.url}")
        return "\n".join(lines)

    @staticmethod
    def format_post(post: MediaPost) -> str:
        urls: list[str] = []
        if post.is_series and post.seasons:
            for s in post.seasons:
                for v in s.versions:
                    for q in v.qualities:
                        for ep in q.episodes:
                            if ep.url and ep.url not in urls:
                                urls.append(ep.url)
        else:
            for v in post.versions:
                for q in v.qualities:
                    for ep in q.episodes:
                        if ep.url and ep.url not in urls:
                            urls.append(ep.url)
        return "\n".join(urls)

    @staticmethod
    def format_categories(sections: list[tuple[str, str]], genres: dict[str, list[tuple[str, str]]]) -> str:
        lines: list[str] = []
        for name, url in sections:
            lines.append(f"section\t{name}\t{url}")
        for name, url in genres.get("movie", []):
            lines.append(f"movie_genre\t{name}\t{url}")
        for name, url in genres.get("series", []):
            lines.append(f"series_genre\t{name}\t{url}")
        return "\n".join(lines)

    @staticmethod
    def format_config(profile: ConfigurationProfile) -> str:
        profile_dict = profile.to_dict()
        lines: list[str] = []
        for k in ("base_url", "mirrors", "proxy", "search_sort", "player", "download_dir", "user_agent"):
            val = profile_dict.get(k, "")
            if isinstance(val, list):
                val = ",".join(val)
            lines.append(f"{k}={val}")
        return "\n".join(lines)

    @staticmethod
    def format_config_get(val: Any) -> str:
        if isinstance(val, list):
            return ",".join(val)
        return str(val)

    @staticmethod
    def format_config_set(key: str, val: Any) -> str:
        if isinstance(val, list):
            val = ",".join(val)
        return f"OK: {key}={val}"

    @staticmethod
    def format_test(reachable: bool, base_url: str, target_or_err: str) -> str:
        status = "OK" if reachable else "FAIL"
        return f"{status}\t{base_url}\t{target_or_err}"

    @staticmethod
    def format_error(message: str) -> str:
        return f"Error: {message}"
