#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
f2m — Film2Media terminal client.

Search movies & series, browse categories, download with aria2c and stream
to mpv / VLC / PotPlayer.

  f2m.py                interactive menu
  f2m.py search QUERY   search from the command line
  f2m.py url URL        open a post page directly
  f2m.py categories     browse categories & genres
  f2m.py config         show config (config set KEY VALUE to edit)
  f2m.py test           connectivity test

All site-specific regexes live in the PATTERNS class — if the site changes
its markup, only that section needs updating.

Requires Python 3.8+ (stdlib only). aria2c / mpv / vlc are used if installed.
"""

from __future__ import annotations

import configparser
import http.client
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import zipfile
from dataclasses import dataclass, field
from html import unescape
from http.cookiejar import CookieJar
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from f2m.core.exceptions import (
    F2MError,
    F2MConfigError,
    F2MNetworkError,
    F2MParseError,
    F2MCliError,
)
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
from f2m.core.config import (
    CONFIG_DEFAULTS,
    CONF_COMMENT,
    ConfigurationProfile,
    ConfigManager,
    resolve_config_path,
    validate_key_value,
)
from f2m.core.scraper import (
    clean_title,
    parse_filename,
    parse_categories,
    parse_listing,
    parse_post,
    parse_quick_search,
)
from f2m.net.client import HttpClient
from f2m.cli.runner import CliRunner, run_cli

VERSION = "1.1.0"
APP = "f2m"
TIMEOUT = 25



class C:
    ENABLED = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

    @staticmethod
    def _c(code: str, text: object) -> str:
        if not C.ENABLED:
            return str(text)
        return f"\033[{code}m{text}\033[0m"

    @classmethod
    def bold(cls, t): return cls._c("1", t)
    @classmethod
    def dim(cls, t): return cls._c("2", t)
    @classmethod
    def red(cls, t): return cls._c("31", t)
    @classmethod
    def green(cls, t): return cls._c("32", t)
    @classmethod
    def yellow(cls, t): return cls._c("33", t)
    @classmethod
    def blue(cls, t): return cls._c("34", t)
    @classmethod
    def magenta(cls, t): return cls._c("35", t)
    @classmethod
    def cyan(cls, t): return cls._c("36", t)
    @classmethod
    def white(cls, t): return cls._c("97", t)
    @classmethod
    def grey(cls, t): return cls._c("90", t)
    @classmethod
    def bg_accent(cls, t): return cls._c("97;45", t)


def _enable_windows_vt() -> None:
    if os.name == "nt":
        os.system("")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def banner() -> None:
    top = "╔" + "═" * 46 + "╗"
    bot = "╚" + "═" * 46 + "╝"
    print(C.magenta(top))
    print(C.magenta("║") + C.bold(C.white("   ⚡ F2M ")) + C.grey("· film2media terminal client ") + C.grey(f"v{VERSION}".rjust(9)) + C.magenta("║"))
    print(C.magenta(bot))


class Spinner:
    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    ENABLED = True

    def __init__(self, text: str = "fetching"):
        self.text = text
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _spin(self):
        i = 0
        while not self._stop.is_set():
            sys.stderr.write(f"\r{C.cyan(self.FRAMES[i % len(self.FRAMES)])} {self.text}…  ")
            sys.stderr.flush()
            i += 1
            time.sleep(0.08)

    def __enter__(self):
        if C.ENABLED and Spinner.ENABLED and sys.stderr.isatty():
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        sys.stderr.write("\r" + " " * (len(self.text) + 6) + "\r")
        sys.stderr.flush()
        return False


class Screen:
    depth = 0

    @classmethod
    def enter(cls) -> None:
        if C.ENABLED and cls.depth == 0:
            sys.stdout.write("\033[?1049h\033[H\033[2J")
            sys.stdout.flush()
        cls.depth += 1

    @classmethod
    def leave(cls) -> None:
        cls.depth = max(0, cls.depth - 1)
        if C.ENABLED and cls.depth == 0:
            sys.stdout.write("\033[?1049l")
            sys.stdout.flush()

    @classmethod
    def frame(cls) -> None:
        if C.ENABLED and cls.depth > 0:
            sys.stdout.write("\033[H\033[J")
            sys.stdout.flush()


def run_interactive(fn, *args, **kwargs):
    Screen.enter()
    try:
        fn(*args, **kwargs)
    finally:
        Screen.leave()


def info(msg): print(f"{C.blue('ℹ')} {msg}")
def ok(msg): print(f"{C.green('✔')} {msg}")
def warn(msg): print(f"{C.yellow('⚠')} {msg}")
def err(msg): sys.stderr.write(f"{C.red('✖')} {msg}\n"); sys.stderr.flush()


def heading(text: str) -> None:
    print()
    print(C.bold(C.white(f"  {text}")))
    print(C.grey("  " + "─" * min(len(text) + 2, 60)))


def menu(title: str, options: list[tuple[str, str]], back: str = "← Back",
         frame: bool = True, header=None) -> int:
    if frame:
        Screen.frame()
    if header:
        header()
    heading(title)
    icons = {"search": "🔍", "categories": "🗂 ", "url": "🌐", "settings": "⚙ ",
             "download": "⬇ ", "stream": "▶ ", "trailer": "🎬", "copy": "📋",
             "series": "📺", "movie": "🎞 "}
    for i, (label, icon_key) in enumerate(options, 1):
        icon = icons.get(icon_key, "•")
        print(f"   {C.cyan(str(i).rjust(2))}. {icon} {label}")
    print(f"   {C.cyan(' 0')}. {C.grey(back)}")
    while True:
        try:
            raw = input(f"   {C.yellow('❯')} ").strip().lower()
        except EOFError:
            return -1
        if raw in ("q", "b", "0", ""):
            return -1
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        warn(f"enter 1-{len(options)} or 0")


def prompt(msg: str, default: str = "") -> str:
    try:
        raw = input(f"   {C.yellow('❯')} {msg}").strip()
    except EOFError:
        return ""
    return raw or default


def parse_selection(raw: str, count: int) -> list[int]:
    raw = raw.strip().lower()
    if not raw:
        return []
    if raw in ("a", "all", "*"):
        return list(range(count))
    picked: set[int] = set()
    for token in raw.replace("،", ",").split(","):
        token = token.strip()
        if not token:
            continue
        m = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", token)
        if m:
            lo, hi = sorted((int(m.group(1)), int(m.group(2))))
            picked.update(i - 1 for i in range(lo, min(hi, count) + 1) if i >= 1)
        elif token.isdigit() and 1 <= int(token) <= count:
            picked.add(int(token) - 1)
    return sorted(picked)


# ---------------------------------------------------------------------------
# 2. CONFIG
# ---------------------------------------------------------------------------
_config_mgr = ConfigManager()
CONF_PATH = str(_config_mgr.file_path)
_cfg: dict[str, Any] = _config_mgr._cfg


def load_config() -> None:
    _config_mgr.load()
    global CONF_PATH, _cfg
    CONF_PATH = str(_config_mgr.file_path)
    _cfg = _config_mgr._cfg


def save_config() -> None:
    _config_mgr.save()


def ensure_config() -> None:
    load_config()


def base_url() -> str:
    return str(_config_mgr.get("base_url", CONFIG_DEFAULTS["base_url"])).rstrip("/")


def set_base_url(url: str, announce: bool = True) -> None:
    url = url.rstrip("/")
    if base_url() != url:
        _config_mgr.set("base_url", url)
        if announce:
            info(f"base_url updated to {C.bold(url)} (saved to {CONF_PATH})")


def proxies() -> dict[str, str | None]:
    p = str(_config_mgr.get("proxy", "")).strip()
    return {"http": p or None, "https": p or None} if p else {}


# ---------------------------------------------------------------------------
# 3. HTTP
# ---------------------------------------------------------------------------


def _get_http_client() -> HttpClient:
    profile = _config_mgr.profile()
    return HttpClient(
        base_url=profile.base_url,
        mirrors=profile.mirrors,
        proxy=profile.proxy,
        user_agent=profile.user_agent,
        timeout=TIMEOUT,
    )


_client = _get_http_client()


def fetch(path_or_url: str, *, referer: str | None = None, ajax: bool = False,
          data: bytes | None = None, allow_mirrors: bool = True) -> str:
    global _client
    profile = _config_mgr.profile()
    # Ensure client mirrors and proxy match current config
    _client.timeout = TIMEOUT
    return _client.fetch(
        path_or_url,
        referer=referer,
        ajax=ajax,
        data=data,
        allow_mirrors=allow_mirrors,
    )


def page_url(base_path: str, page: int) -> str:
    if page <= 1:
        return base_path
    if "?" in base_path:
        path, _, query = base_path.partition("?")
        return f"{path.rstrip('/')}/page/{page}/?{query}"
    return f"{base_path.rstrip('/')}/page/{page}/"


# ---------------------------------------------------------------------------
# 6. SITE CALLS
# ---------------------------------------------------------------------------


def quick_search(query: str) -> list[SearchResult]:
    body = urlparse.urlencode({"q": query, "sort": _cfg["search_sort"]}).encode()
    try:
        with Spinner(f"searching “{query}”"):
            text = fetch("/quick-search", ajax=True, data=body,
                         referer=base_url() + "/", allow_mirrors=False)
        items = json.loads(text)
        if isinstance(items, list) and items:
            results = parse_quick_search(items, base_url())
            if results:
                return results
    except (F2MNetworkError, F2MParseError, json.JSONDecodeError, ValueError) as exc:
        warn(f"quick-search endpoint failed ({exc}); falling back to HTML search")
    with Spinner(f"searching “{query}”"):
        html = fetch("/?s=" + urlparse.quote(query))
    cards, _ = parse_listing(html)
    return [SearchResult(kind=c.kind, title=c.title, title_fa="", year=c.year,
                         rating="", url=c.url, image=c.poster, meta=c.note)
            for c in cards]


def fetch_home() -> str:
    return fetch("/")


def fetch_post(url: str) -> Post:
    with Spinner("loading post"):
        html = fetch(url)
    return parse_post(html, url)


# ---------------------------------------------------------------------------
# 7. EXTERNAL TOOLS
# ---------------------------------------------------------------------------


ARIA2_VERSION = "1.37.0"
ARIA2_WIN_URL = ("https://github.com/aria2/aria2/releases/download/"
                 f"release-{ARIA2_VERSION}/"
                 f"aria2-{ARIA2_VERSION}-win-64bit-build1.zip")

LINUX_PKG_MANAGERS = {
    "apt-get": ["install", "-y"],
    "dnf": ["install", "-y"],
    "yum": ["install", "-y"],
    "pacman": ["-S", "--noconfirm"],
    "apk": ["add"],
    "zypper": ["install", "-y"],
}


def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def local_aria2c() -> str | None:
    exe = os.path.join(app_dir(), "aria2c.exe" if os.name == "nt" else "aria2c")
    return exe if os.path.isfile(exe) else None


def find_aria2c() -> str | None:
    return local_aria2c() or shutil.which("aria2c")


def install_aria2c_windows() -> str | None:
    dest = app_dir()
    zip_path = os.path.join(dest, "aria2.zip")
    tmp = os.path.join(dest, "aria2-tmp")
    target = os.path.join(dest, "aria2c.exe")
    try:
        with Spinner(f"downloading aria2c {ARIA2_VERSION}"):
            req = urlrequest.Request(ARIA2_WIN_URL,
                                     headers={"User-Agent": _cfg.get("user_agent", DEFAULT_UA)})
            with _OPENER.open(req, timeout=TIMEOUT * 4) as resp, \
                    open(zip_path, "wb") as fh:
                shutil.copyfileobj(resp, fh)
        with zipfile.ZipFile(zip_path) as zf:
            member = next(n for n in zf.namelist() if n.endswith("aria2c.exe"))
            zf.extract(member, tmp)
            shutil.move(os.path.join(tmp, member), target)
        ok(f"aria2c installed: {target}")
        return target
    except Exception as exc:
        err(f"aria2c download failed: {exc}")
        info(f"install it manually from https://github.com/aria2/aria2/releases")
        return None
    finally:
        for path in (zip_path, tmp):
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.exists(path):
                os.remove(path)


def install_aria2c_linux() -> str | None:
    sudo = os.geteuid() != 0 and shutil.which("sudo")
    for mgr, args in LINUX_PKG_MANAGERS.items():
        if not shutil.which(mgr):
            continue
        cmd = ([sudo] if sudo else []) + [mgr] + args + ["aria2"]
        info(f"installing aria2 via {mgr} …")
        if subprocess.call(cmd) == 0 and shutil.which("aria2c"):
            ok("aria2c installed")
            return shutil.which("aria2c")
        warn(f"{mgr} failed")
    err("could not install aria2c automatically")
    info("install it manually (e.g. sudo apt install aria2)")
    return None


def install_aria2c() -> str | None:
    if os.name == "nt":
        return install_aria2c_windows()
    return install_aria2c_linux()


def find_player() -> tuple[str | None, str]:
    choice = _cfg.get("player", "auto").lower()
    candidates: list[str] = ["mpv", "vlc", "potplayer"] if choice == "auto" else [choice]
    for name in candidates:
        if name == "mpv":
            exe = shutil.which("mpv") or shutil.which("mpv.exe")
            if exe:
                return exe, "mpv"
        elif name == "vlc":
            exe = shutil.which("vlc") or shutil.which("vlc.exe")
            for path in (r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                         r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"):
                if not exe and os.path.exists(path):
                    exe = path
            if exe:
                return exe, "vlc"
        elif name == "potplayer":
            for path in (r"C:\Program Files\PotPlayer\PotPlayerMini64.exe",
                         r"C:\Program Files (x86)\PotPlayer\PotPlayerMini64.exe",
                         r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
                         r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini64.exe"):
                if os.path.exists(path):
                    return path, "potplayer"
    return None, choice


def player_command(url: str | list[str], title: str) -> tuple[str, list[str]] | None:
    exe, name = find_player()
    if not exe:
        return None
    urls = url if isinstance(url, list) else [url]
    proxy = _cfg.get("proxy", "").strip()
    if name == "mpv":
        cmd = [exe, "--force-media-title=" + title, "--keep-open=no"] + urls
        if proxy:
            cmd.insert(1, "--http-proxy=" + proxy)
    elif name == "vlc":
        cmd = [exe] + urls
        if proxy:
            cmd[1:1] = ["--http-proxy=" + proxy]
    else:  # potplayer
        cmd = [exe] + urls
    return name, cmd


# ---------------------------------------------------------------------------
# 8. ACTIONS
# ---------------------------------------------------------------------------


def download_dir() -> str:
    path = os.path.expanduser(_cfg["download_dir"])
    os.makedirs(path, exist_ok=True)
    return path


def do_download(urls: list[str], subdir: str | None = None) -> None:
    if not urls:
        warn("nothing selected")
        return
    dest = download_dir()
    if subdir:
        dest = os.path.join(dest, sanitize(subdir))
        os.makedirs(dest, exist_ok=True)
    aria = find_aria2c()
    if aria is None:
        info("aria2c not found — trying to install it automatically")
        aria = install_aria2c()
        if aria is None:
            warn("falling back to curl / plain links")
    info(f"{len(urls)} file(s) → {C.bold(dest)}")
    if aria:
        cmd = [aria, "-x", "16", "-s", "16", "-j", "4",
               "--file-allocation=none", "--console-log-level=warn",
               "--summary-interval=0", "--download-result=hide",
               "-d", dest] + urls
        if _cfg.get("proxy", "").strip():
            cmd += ["--all-proxy=" + _cfg["proxy"].strip()]
        code = subprocess.call(cmd)
        if code == 0:
            ok("download finished")
        else:
            warn(f"aria2c exited with code {code}")
    elif shutil.which("curl"):
        warn("aria2c not found — falling back to curl (single connections)")
        for u in urls:
            out = os.path.join(dest, sanitize(urlparse.unquote(u.rsplit("/", 1)[-1])))
            print(f"  {C.cyan('→')} {u.rsplit('/', 1)[-1]}")
            subprocess.call(["curl", "-L", "--fail", "-o", out, u])
        ok("download finished")
    else:
        warn("neither aria2c nor curl found — links below:")
        for u in urls:
            print("     " + u)


def do_stream(urls: list[str], title: str) -> None:
    if not urls:
        warn("nothing selected")
        return
    resolved = player_command(urls, title)
    if not resolved:
        warn(f"no player found (config: player={_cfg['player']}). Install mpv/vlc/PotPlayer")
        info("link(s) to paste into your player:")
        for u in urls:
            print("     " + u)
        return
    name, cmd = resolved
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ok(f"streaming with {C.bold(name)} → {'…' if len(urls) == 1 else f'{len(urls)} parts'}")
    except OSError as exc:
        err(f"could not launch {name}: {exc}")


def copy_links(urls: list[str], name_hint: str) -> None:
    if not urls:
        warn("nothing selected")
        return
    path = os.path.join(download_dir(), sanitize(name_hint) + ".txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(urls) + "\n")
    ok(f"saved {len(urls)} link(s) → {C.bold(path)}")
    if os.name == "nt" and shutil.which("clip"):
        try:
            subprocess.run("clip", input="\n".join(urls).encode("utf-16-le"),
                           check=False)
            info("also copied to clipboard")
        except OSError:
            pass


def sanitize(name: str) -> str:
    name = unicodedata.normalize("NFKC", name)
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip() or "f2m"


# ---------------------------------------------------------------------------
# 9. INTERACTIVE FLOWS
# ---------------------------------------------------------------------------


def show_post_header(post: Post) -> None:
    heading(post.title)
    bits = []
    if post.rating:
        bits.append(C.yellow("★ " + post.rating + "/10"))
    if post.imdb_id:
        bits.append(C.grey(post.imdb_id))
    if post.year:
        bits.append(C.grey(post.year))
    bits.append(C.magenta("series" if post.is_series else "movie"))
    print("   " + "  ".join(bits))


def choose_quality(qualities: list[Quality], header=None) -> Quality | None:
    Screen.frame()
    if header:
        header()
    heading("Quality")
    for i, q in enumerate(qualities, 1):
        enc = f"  {C.grey('enc: ' + q.encoder)}" if q.encoder and q.encoder.lower() != "unknown" else ""
        count = f"  {C.grey(str(len(q.episodes)) + ' eps')}" if len(q.episodes) > 1 else ""
        print(f"   {C.cyan(str(i).rjust(2))}. {C.white(q.label)}{enc}{count}")
    print(f"   {C.cyan(' 0')}. {C.grey('← Back')}")
    while True:
        raw = prompt("")
        if raw in ("q", "b", "0", ""):
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(qualities):
            return qualities[int(raw) - 1]
        warn(f"enter 1-{len(qualities)} or 0")


def choose_episodes(quality: Quality, header=None) -> list[Episode]:
    eps = quality.episodes
    if len(eps) == 1 and eps[0].num == 1:      # movie-style single file
        return eps
    Screen.frame()
    if header:
        header()
    heading(f"Episodes — {quality.label}")
    line = "   "
    for i, ep in enumerate(eps, 1):
        chunk = f"{C.cyan(str(i).rjust(2))} {C.white('E%02d' % ep.num)}   "
        if len(line) + len(re.sub(r"\033\[\d+m", "", chunk)) > 70:
            print(line)
            line = "   "
        line += chunk
    if line.strip():
        print(line)
    print(C.grey("   select: 3  |  1,3,5-8  |  all  |  (empty/b = back)"))
    while True:
        raw = prompt("")
        if raw in ("", "b", "q", "0"):
            return []
        picked = parse_selection(raw, len(eps))
        if picked:
            return [eps[i] for i in picked]
        warn("invalid selection")


def after_selection(post: Post, urls: list[str], name_hint: str, label: str,
                    header=None) -> None:
    Screen.frame()
    if header:
        header()
    heading(f"{label} — {len(urls)} file(s)")
    for u in urls[:6]:
        print(f"     {C.grey(urlparse.unquote(u.rsplit('/', 1)[-1]))}")
    if len(urls) > 6:
        print(C.grey(f"     … and {len(urls) - 6} more"))
    actions = [("Download (aria2c)", "download"),
               ("Stream to player", "stream"),
               ("Copy links", "copy")]
    choice = menu("Action", actions, frame=False)
    if choice == 0:
        do_download(urls, name_hint)
    elif choice == 1:
        do_stream(urls, label + " — " + name_hint)
    elif choice == 2:
        copy_links(urls, name_hint)


def movie_flow(post: Post) -> None:
    header = lambda: show_post_header(post)
    while True:
        versions = post.versions
        if not versions or not any(v.qualities for v in versions):
            Screen.frame()
            show_post_header(post)
            warn("no download links found on this page")
            return
        options = [(v.title or v.key, "movie") for v in versions]
        if post.trailer:
            options.append(("Play trailer", "trailer"))
        choice = menu("Version", options, header=header)
        if choice == -1:
            return
        if post.trailer and choice == len(options) - 1:
            do_stream([post.trailer], post.title + " trailer")
            continue
        version = versions[choice]
        quality = choose_quality(version.qualities, header=header)
        if quality is None:
            continue
        eps = choose_episodes(quality, header=header)
        if not eps:
            continue
        urls = [e.url for e in eps]
        hint = sanitize(post.title) + " " + quality.label
        after_selection(post, urls, hint, quality.label, header=header)


def series_flow(post: Post) -> None:
    header = lambda: show_post_header(post)
    while True:
        if not post.seasons:
            Screen.frame()
            show_post_header(post)
            warn("no season blocks found on this page")
            return
        options = [(s.title, "series") for s in post.seasons]
        if post.trailer:
            options.append(("Play trailer", "trailer"))
        s_choice = menu("Season", options, header=header)
        if s_choice == -1:
            return
        if post.trailer and s_choice == len(options) - 1:
            do_stream([post.trailer], post.title + " trailer")
            continue
        season = post.seasons[s_choice]
        v_choice = menu(season.title, [(v.title or v.key, "series") for v in season.versions],
                        header=header)
        if v_choice == -1:
            continue
        version = season.versions[v_choice]
        quality = choose_quality(version.qualities, header=header)
        if quality is None:
            continue
        eps = choose_episodes(quality, header=header)
        if not eps:
            continue
        urls = [e.url for e in eps]
        hint = sanitize(post.title) + " " + season.title + " " + quality.label
        after_selection(post, urls, hint, season.title + " · " + quality.label,
                        header=header)


def post_flow(url: str) -> None:
    post = fetch_post(url)
    if post.is_series:
        series_flow(post)
    else:
        movie_flow(post)


def listing_menu(title: str, path: str) -> None:
    page = 1
    while True:
        with Spinner("loading"):
            html = fetch(page_url(path, page))
        cards, last = parse_listing(html)
        if not cards:
            warn("nothing here")
            return
        Screen.frame()
        heading(f"{title}   {C.grey(f'— page {page}/{last}')}")
        for i, card in enumerate(cards, 1):
            kind = C.magenta("📺") if card.kind == "series" else C.cyan("🎞 ")
            year = C.grey(card.year) if card.year else ""
            note = f"  {C.grey(card.note[:30])}" if card.note else ""
            print(f"   {C.cyan(str(i).rjust(2))}. {kind} {C.white(card.title)} {year}{note}")
        footer = f"   {C.cyan('n')}. next page   "
        if page > 1:
            footer += f"{C.cyan('p')}. prev page   "
        footer += f"{C.cyan('0')}. back"
        print(footer)
        raw = prompt("").lower()
        if raw in ("0", "q", "b", ""):
            return
        if raw == "n" and page < last:
            page += 1
            continue
        if raw == "p" and page > 1:
            page -= 1
            continue
        picked = parse_selection(raw, len(cards))
        if picked:
            post_flow(cards[picked[0]].url)


def categories_flow() -> None:
    with Spinner("loading categories"):
        sections, genres = parse_categories(fetch_home())
    while True:
        entries: list[tuple[str, str]] = [("Movies", "movies"), ("Series", "series")]
        for name, url in sections:
            if "/movies/" in url or "/series/" in url:
                continue                       # already offered above
            entries.append((name, url))        # e.g. Top 250 movies/series
        choice = menu("Categories", [(e[0], "categories") for e in entries])
        if choice == -1:
            return
        if choice <= 1:
            kind = "movie" if choice == 0 else "series"
            genre_menu(kind, genres[kind])
        else:
            name, url = entries[choice]
            listing_menu(name, urlparse.urlsplit(url).path)


def genre_menu(kind: str, glist: list[tuple[str, str]]) -> None:
    if not glist:
        warn("no genres parsed — site layout may have changed (see PATTERNS.GENRE_LINK)")
        return
    while True:
        Screen.frame()
        heading(f"{kind.title()} genres ({len(glist)})")
        # two-column grid (padding computed on plain text, then colorized)
        half = (len(glist) + 1) // 2
        left, right = glist[:half], glist[half:]
        for i in range(half):
            line = "   " + C.cyan(f"{i + 1}.") + " " + C.white(left[i][0])
            line += " " * max(2, 34 - len(f"{i + 1}. {left[i][0]}"))
            if i < len(right):
                line += C.cyan(f"{half + i + 1}.") + " " + C.white(right[i][0])
            print(line)
        print(f"   {C.cyan(' 0')}. {C.grey('← Back')}")
        raw = prompt("").lower()
        if raw in ("0", "q", "b", ""):
            return
        picked = parse_selection(raw, len(glist))
        if picked:
            name, url = glist[picked[0]]
            listing_menu(f"{kind.title()} · {name}",
                         urlparse.urlsplit(url).path + "?type=" + kind)


def search_flow(query: str | None = None) -> None:
    query = query or prompt("search: ")
    if not query:
        return
    results = quick_search(query)
    if not results:
        warn("nothing found")
        return
    while True:
        Screen.frame()
        heading(f"Results for “{query}” ({len(results)})")
        for i, r in enumerate(results, 1):
            icon = C.magenta("📺") if r.kind == "series" else C.cyan("🎞 ")
            title = C.white(r.title)
            if r.title_fa:
                title += f"  {C.grey(r.title_fa)}"
            year = C.grey(r.year) if r.year else ""
            rating = C.yellow("★" + r.rating) if r.rating else ""
            meta = C.grey(f"  {r.meta}") if r.meta else ""
            badges = " ".join(b for b in (
                C.green("[dub]") if r.is_dub else "",
                C.blue("[hardsub]") if r.is_hardsub else "") if b)
            print(f"   {C.cyan(str(i).rjust(2))}. {icon} {title} {year} {rating} {badges}{meta}")
        print(f"   {C.cyan(' 0')}. {C.grey('← Back')}")
        raw = prompt("").lower()
        if raw in ("0", "q", "b", ""):
            return
        picked = parse_selection(raw, len(results))
        if picked:
            post_flow(results[picked[0]].url)


def settings_flow() -> None:
    while True:
        choice = menu("Settings", [("Show config", "settings"),
                                   ("Edit base_url (site domain)", "settings"),
                                   ("Edit proxy", "settings"),
                                   ("Edit player", "settings"),
                                   ("Edit download_dir", "settings"),
                                   ("Edit search_sort", "settings"),
                                   ("Connection test", "settings")])
        if choice == -1:
            return
        if choice == 0:
            heading("Config — " + CONF_PATH)
            for key in ("base_url", "mirrors", "proxy", "search_sort", "player",
                        "download_dir", "user_agent"):
                val = _cfg["_raw_mirrors"] if key == "mirrors" else _cfg[key]
                print(f"   {C.cyan(key.ljust(13))} = {C.white(val)}")
        elif choice == 6:
            test_connection()
        else:
            keys = {1: None, 2: "proxy", 3: "player", 4: "download_dir", 5: "search_sort"}
            if choice == 1:
                val = prompt(f"new base_url [{_cfg['base_url']}]: ")
                if val:
                    set_base_url(val)
            else:
                key = keys[choice]
                val = prompt(f"new {key} [{_cfg[key]}]: ")
                if val:
                    try:
                        _config_mgr.set(key, val)
                        ok(f"{key} saved")
                    except F2MConfigError as exc:
                        err(str(exc))


def test_connection() -> None:
    ok(f"base_url: {base_url()}")
    try:
        with Spinner("testing"):
            html = fetch("/")
        ok(f"reachable — final host: {C.bold(urlparse.urlsplit(base_url()).netloc)}")
        sections, genres = parse_categories(html)
        info(f"categories parsed: {len(sections)} sections, "
             f"{len(genres['movie'])} movie genres, {len(genres['series'])} series genres")
    except F2MNetworkError as exc:
        err(str(exc))


def main_menu() -> None:
    while True:
        choice = menu("", [("Search movies & series", "search"),
                           ("Browse categories & genres", "categories"),
                           ("Open a post by URL", "url"),
                           ("Settings & connection test", "settings")])
        if choice == -1:
            return
        if choice == 0:
            search_flow()
        elif choice == 1:
            categories_flow()
        elif choice == 2:
            raw = prompt("post url: ")
            if raw:
                post_flow(raw.strip())
        elif choice == 3:
            settings_flow()


# ---------------------------------------------------------------------------
# 10. CLI
# ---------------------------------------------------------------------------

USAGE = f"""\
{C.bold('f2m')} {C.grey('v' + VERSION)} — film2media terminal client

{C.bold('usage:')}
  python f2m.py                     interactive menu
  python f2m.py search <query>      search, then pick interactively
  python f2m.py url <post-url>      open a post page directly
  python f2m.py categories          browse categories & genres
  python f2m.py config              show config
  python f2m.py config set K V      set a config key (e.g. base_url)
  python f2m.py test                connectivity / domain check
  python f2m.py help                this text

{C.bold('config:')} {CONF_PATH}   — edit base_url when the domain changes,
  or let the script auto-update it on redirects. Mirrors & proxy are supported.
"""


def get_runner() -> CliRunner:
    handlers = {
        "search_flow": search_flow,
        "post_flow": post_flow,
        "categories_flow": categories_flow,
        "test_connection": test_connection,
        "main_menu": main_menu,
        "banner": banner,
        "run_interactive": run_interactive,
        "spinner_cls": Spinner,
    }
    return CliRunner(
        config_mgr=_config_mgr,
        http_client=_client,
        interactive_handlers=handlers,
    )


def cli(argv: list[str]) -> None:
    code = get_runner().run(argv)
    if code != 0:
        sys.exit(code)


def main() -> None:
    _enable_windows_vt()
    ensure_config()
    argv = [a for a in sys.argv[1:] if a.strip()]
    code = get_runner().run(argv)
    if code != 0:
        sys.exit(code)


if __name__ == "__main__":
    main()
