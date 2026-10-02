from __future__ import annotations

import json
import os
import sys
from urllib import parse as urlparse
from typing import Any, Callable

from f2m.cli.formatters import JsonFormatter, PlainFormatter, emit_stderr, emit_stdout
from f2m.cli.models import CliArgs, CliCommand, ConfigAction, OutputFormat
from f2m.cli.parser import parse_args
from f2m.core.config import CONFIG_DEFAULTS, ConfigManager, ConfigurationProfile
from f2m.core.exceptions import (
    F2MCliError,
    F2MConfigError,
    F2MError,
    F2MNetworkError,
    F2MParseError,
)
from f2m.core.models import MediaPost, SearchResult
from f2m.core.scraper import parse_categories, parse_listing, parse_post, parse_quick_search
from f2m.net.client import HttpClient

VERSION = "1.1.0"


def _c(code: str, text: Any, no_color: bool = False) -> str:
    """Format text with ANSI escape code if color is enabled and stdout is a TTY."""
    if no_color or not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return str(text)
    return f"\033[{code}m{text}\033[0m"


USAGE_TEXT = f"""\
\033[1mf2m\033[0m \033[90mv{VERSION}\033[0m — film2media terminal client

\033[1musage:\033[0m
  f2m [options] [command] [args...]

\033[1mcommands:\033[0m
  f2m                              interactive menu
  f2m search <query>               search movies & series
  f2m url <post-url>               open or inspect a post by URL
  f2m categories                   browse categories & genres
  f2m config                       show active configuration
  f2m config get <key>             get configuration value
  f2m config set <key> <val>       set configuration key
  f2m test                         connectivity & mirror check
  f2m help [command]               show usage help
  f2m version                      show application version

\033[1moptions:\033[0m
  --json                           machine-readable JSON output on stdout
  --plain                          unadorned tab/newline-delimited output on stdout
  --no-color                       disable ANSI colored output
  --config <path>                  custom configuration file path
  -h, --help                       show this help message
  -V, --version                    show application version

\033[1mexit codes:\033[0m
  0: Success                       1: Operational runtime error
  2: Invalid arguments             3: Configuration error
  4: Network failure               5: Parse error
  6: Resource not found            130: Interrupted (SIGINT)
"""


class CliRunner:
    """Orchestrates argument parsing, command dispatch, and output formatting."""

    def __init__(
        self,
        config_mgr: ConfigManager | None = None,
        http_client: HttpClient | None = None,
        interactive_handlers: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        self.config_mgr = config_mgr
        self.http_client = http_client
        self.interactive_handlers = interactive_handlers or {}

    def get_config_manager(self, config_path: str | None = None) -> ConfigManager:
        if self.config_mgr and not config_path:
            return self.config_mgr
        return ConfigManager(file_path=config_path)

    def get_http_client(self, config_mgr: ConfigManager) -> HttpClient:
        if self.http_client:
            return self.http_client
        profile = config_mgr.profile()
        return HttpClient(
            base_url=profile.base_url,
            mirrors=profile.mirrors,
            proxy=profile.proxy,
            user_agent=profile.user_agent,
            timeout=25,
        )

    def execute_search(self, client: HttpClient, query: str, sort: str = "date") -> list[SearchResult]:
        body = urlparse.urlencode({"q": query, "sort": sort}).encode()
        try:
            text = client.fetch(
                "/quick-search",
                ajax=True,
                data=body,
                referer=client.base_url + "/",
                allow_mirrors=False,
            )
            items = json.loads(text)
            if isinstance(items, list) and items:
                results = parse_quick_search(items, client.base_url)
                if results:
                    return results
        except (F2MNetworkError, F2MParseError, json.JSONDecodeError, ValueError):
            pass

        # Fallback to HTML search
        html = client.fetch("/?s=" + urlparse.quote(query))
        cards, _ = parse_listing(html)
        return [
            SearchResult(
                kind=c.kind,
                title=c.title,
                title_fa="",
                year=c.year,
                rating="",
                url=c.url,
                image=c.poster,
                meta=c.note,
            )
            for c in cards
        ]

    def execute_post(self, client: HttpClient, url: str) -> MediaPost:
        html = client.fetch(url)
        return parse_post(html, url)

    def execute_categories(self, client: HttpClient) -> tuple[list[tuple[str, str]], dict[str, list[tuple[str, str]]]]:
        html = client.fetch("/")
        return parse_categories(html)

    def execute_test(self, client: HttpClient) -> tuple[bool, str, str, int, int, int, str | None]:
        base_url = client.base_url
        try:
            html = client.fetch("/")
            final_host = urlparse.urlsplit(client.current_base_url or base_url).netloc
            sections, genres = parse_categories(html)
            movie_count = len(genres.get("movie", []))
            series_count = len(genres.get("series", []))
            return True, base_url, final_host, len(sections), movie_count, series_count, None
        except Exception as exc:
            return False, base_url, urlparse.urlsplit(base_url).netloc, 0, 0, 0, str(exc)

    def handle_command(self, args: CliArgs) -> int:
        mgr = self.get_config_manager(args.config_path)
        run_interactive = self.interactive_handlers.get("run_interactive", lambda fn, *a, **kw: fn(*a, **kw))

        # Disable spinner in non-interactive mode
        spinner_cls = self.interactive_handlers.get("spinner_cls")
        if spinner_cls and args.format != OutputFormat.HUMAN:
            spinner_cls.ENABLED = False

        # 1. HELP
        if args.command == CliCommand.HELP:
            usage = USAGE_TEXT
            if args.no_color or not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
                # Strip ANSI codes if no_color
                import re
                usage = re.sub(r"\033\[[0-9;]*m", "", usage)
            emit_stdout(usage)
            return 0

        # 2. VERSION
        if args.command == CliCommand.VERSION:
            emit_stdout(f"f2m {VERSION}")
            return 0

        # 3. CONFIG
        if args.command == CliCommand.CONFIG:
            profile = mgr.profile()
            if args.config_action == ConfigAction.SHOW:
                if args.format == OutputFormat.JSON:
                    emit_stdout(JsonFormatter.format_config(profile))
                elif args.format == OutputFormat.PLAIN:
                    emit_stdout(PlainFormatter.format_config(profile))
                else:
                    for k in ("base_url", "mirrors", "proxy", "search_sort", "player", "download_dir", "user_agent"):
                        val = ",".join(profile.mirrors) if k == "mirrors" else getattr(profile, k)
                        print(f"{_c('36', k.ljust(13), args.no_color)} = {_c('97', val, args.no_color)}")
                return 0

            if args.config_action == ConfigAction.GET:
                key = args.config_key or ""
                if key not in CONFIG_DEFAULTS:
                    raise F2MConfigError(f"unknown configuration key '{key}'")
                val = getattr(profile, key)
                if args.format == OutputFormat.JSON:
                    emit_stdout(JsonFormatter.format_config_get(key, val))
                elif args.format == OutputFormat.PLAIN:
                    emit_stdout(PlainFormatter.format_config_get(val))
                else:
                    print(f"{_c('36', key.ljust(13), args.no_color)} = {_c('97', val, args.no_color)}")
                return 0

            if args.config_action == ConfigAction.SET:
                key = args.config_key or ""
                val = args.config_val or ""
                mgr.set(key, val)
                if args.format == OutputFormat.JSON:
                    emit_stdout(JsonFormatter.format_config_set(key, val, str(mgr.file_path)))
                elif args.format == OutputFormat.PLAIN:
                    emit_stdout(PlainFormatter.format_config_set(key, val))
                else:
                    print(f"{_c('32', '✔', args.no_color)} {key} saved")
                return 0

        # 4. SEARCH
        if args.command == CliCommand.SEARCH:
            if args.format == OutputFormat.HUMAN:
                # Interactive flow
                search_flow = self.interactive_handlers.get("search_flow")
                if search_flow:
                    run_interactive(search_flow, args.query)
                    return 0
                emit_stderr("Interactive search handler not registered")
                return 1

            client = self.get_http_client(mgr)
            query = args.query or ""
            sort_mode = mgr.profile().search_sort
            results = self.execute_search(client, query, sort=sort_mode)
            if not results:
                emit_stderr(f"ℹ no results found for '{query}'")
                if args.format == OutputFormat.JSON:
                    emit_stdout("[]")
                return 6

            if args.format == OutputFormat.JSON:
                emit_stdout(JsonFormatter.format_search(results))
            else:
                emit_stdout(PlainFormatter.format_search(results))
            return 0

        # 5. URL
        if args.command == CliCommand.URL:
            if args.format == OutputFormat.HUMAN:
                post_flow = self.interactive_handlers.get("post_flow")
                if post_flow:
                    run_interactive(post_flow, args.url or "")
                    return 0
                emit_stderr("Interactive post handler not registered")
                return 1

            client = self.get_http_client(mgr)
            post = self.execute_post(client, args.url or "")
            if args.format == OutputFormat.JSON:
                emit_stdout(JsonFormatter.format_post(post))
            else:
                emit_stdout(PlainFormatter.format_post(post))
            return 0

        # 6. CATEGORIES
        if args.command == CliCommand.CATEGORIES:
            if args.format == OutputFormat.HUMAN:
                categories_flow = self.interactive_handlers.get("categories_flow")
                if categories_flow:
                    run_interactive(categories_flow)
                    return 0
                emit_stderr("Interactive categories handler not registered")
                return 1

            client = self.get_http_client(mgr)
            sections, genres = self.execute_categories(client)
            if args.format == OutputFormat.JSON:
                emit_stdout(JsonFormatter.format_categories(sections, genres))
            else:
                emit_stdout(PlainFormatter.format_categories(sections, genres))
            return 0

        # 7. TEST
        if args.command == CliCommand.TEST:
            if args.format == OutputFormat.HUMAN:
                test_connection = self.interactive_handlers.get("test_connection")
                if test_connection:
                    test_connection()
                    return 0

            client = self.get_http_client(mgr)
            reachable, base_url, final_host, sections, movies, series, err_msg = self.execute_test(client)
            if args.format == OutputFormat.JSON:
                emit_stdout(JsonFormatter.format_test(reachable, base_url, final_host, sections, movies, series, err_msg))
                return 0 if reachable else 4
            if args.format == OutputFormat.PLAIN:
                target_or_err = final_host if reachable else (err_msg or "unreachable")
                emit_stdout(PlainFormatter.format_test(reachable, base_url, target_or_err))
                return 0 if reachable else 4

            if reachable:
                print(f"{_c('32', '✔', args.no_color)} base_url: {base_url}")
                print(f"{_c('32', '✔', args.no_color)} reachable — final host: {_c('1', final_host, args.no_color)}")
                print(f"{_c('34', 'ℹ', args.no_color)} categories parsed: {sections} sections, {movies} movie genres, {series} series genres")
                return 0
            emit_stderr(f"{_c('31', '✖', args.no_color)} base_url: {base_url} unreachable ({err_msg})")
            return 0

        # 8. MENU (bare invocation)
        if args.command == CliCommand.MENU:
            main_menu = self.interactive_handlers.get("main_menu")
            banner = self.interactive_handlers.get("banner")
            if banner:
                banner()
            if main_menu:
                run_interactive(main_menu)
                print("\033[90mbye 👋\033[0m")
                return 0
            emit_stdout(USAGE_TEXT)
            return 0

        return 0

    def run(self, argv: list[str]) -> int:
        format_mode = OutputFormat.HUMAN
        try:
            args = parse_args(argv)
            format_mode = args.format
            return self.handle_command(args)
        except F2MCliError as exc:
            if format_mode == OutputFormat.JSON:
                emit_stderr(JsonFormatter.format_error("INVALID_ARGUMENT", str(exc), exc.exit_code))
            else:
                emit_stderr(PlainFormatter.format_error(str(exc)))
            return exc.exit_code
        except F2MConfigError as exc:
            if format_mode == OutputFormat.JSON:
                emit_stderr(JsonFormatter.format_error("CONFIG_ERROR", str(exc), 3))
            else:
                emit_stderr(PlainFormatter.format_error(str(exc)))
            return 3
        except F2MNetworkError as exc:
            if format_mode == OutputFormat.JSON:
                emit_stderr(JsonFormatter.format_error("NETWORK_ERROR", str(exc), 4))
            else:
                emit_stderr(PlainFormatter.format_error(str(exc)))
            return 4
        except F2MParseError as exc:
            if format_mode == OutputFormat.JSON:
                emit_stderr(JsonFormatter.format_error("PARSE_ERROR", str(exc), 5))
            else:
                emit_stderr(PlainFormatter.format_error(str(exc)))
            return 5
        except KeyboardInterrupt:
            if format_mode == OutputFormat.JSON:
                emit_stderr(JsonFormatter.format_error("SIGINT", "interrupted", 130))
            else:
                emit_stderr("\ninterrupted")
            return 130
        except F2MError as exc:
            if format_mode == OutputFormat.JSON:
                emit_stderr(JsonFormatter.format_error("RUNTIME_ERROR", str(exc), 1))
            else:
                emit_stderr(PlainFormatter.format_error(str(exc)))
            return 1
        except Exception as exc:
            if format_mode == OutputFormat.JSON:
                emit_stderr(JsonFormatter.format_error("RUNTIME_ERROR", str(exc), 1))
            else:
                emit_stderr(PlainFormatter.format_error(str(exc)))
            return 1


def run_cli(argv: list[str] | None = None, runner: CliRunner | None = None) -> int:
    """Public CLI entry point."""
    if argv is None:
        argv = [a for a in sys.argv[1:] if a.strip()]
    active_runner = runner or CliRunner()
    return active_runner.run(argv)
