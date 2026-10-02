"""
DOM-based HTML and JSON scraping engine for film2media-cli.
Powered by beautifulsoup4 (html.parser).
"""

from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.parse import unquote, urlsplit, urljoin
from bs4 import BeautifulSoup, Tag

from f2m.core.exceptions import F2MParseError
from f2m.core.models import (
    Card,
    Episode,
    Quality,
    MediaVersion,
    Version,
    Season,
    MediaPost,
    Post,
    SearchResult,
)

# Token patterns for text extraction within DOM elements
SE_TOKEN = re.compile(r'(?i)[._\- ]S(?P<s>\d{1,2})[._\- ]?E(?P<e>\d{1,3})(?![\d])')
DUB_TOKEN = re.compile(r'(?i)farsi[._\- ]?dubbed|farsi[._\- ]?dub\b')
SUB_TOKEN = re.compile(r'(?i)hard[._\- ]?sub|farsi[._\- ]?sub')
TRAILER_TOKEN = re.compile(r'(?i)trailer')
IMDB_ID_PATTERN = re.compile(r'imdb\.com/title/(tt\d+)')
IMDB_RATING_PATTERN = re.compile(r'<strong[^>]*>([\d.]+)</strong>\s*/\s*10')
YEAR_SLUG_PATTERN = re.compile(r"-(19|20)(\d{2})/?$")
MEDIA_EXT_PATTERN = re.compile(r'\.(?:mkv|mp4|avi|mka)$', re.IGNORECASE)

_TITLE_NOISE = [
    r"^\s*دانلود\s*",
    r"با\s*زیرنویس\s*فارسی\s*چسبیده",
    r"با\s*زیرنویس\s*چسبیده",
    r"زیرنویس\s*فارسی",
    r"بدون\s*سانسور",
    r"با\s*دوبله\s*فارسی",
    r"دوبله\s*فارسی",
]


def clean_title(raw: str) -> str:
    """Normalize and strip Persian noise words from titles."""
    if not raw:
        return ""
    t = raw
    for pattern in _TITLE_NOISE:
        t = re.sub(pattern, " ", t)
    cleaned = re.sub(r"\s+", " ", t).strip(" -،,")
    return cleaned or raw.strip()


def parse_filename(url: str) -> tuple[str, int | None, int | None, str]:
    """Extract unquoted filename, season number, episode number, and audio version from media URL."""
    filename = unquote(url.rsplit("/", 1)[-1])
    se = SE_TOKEN.search(filename)
    season = int(se.group("s")) if se else None
    episode = int(se.group("e")) if se else None
    version = ""
    if DUB_TOKEN.search(filename):
        version = "dub"
    elif SUB_TOKEN.search(filename):
        version = "hardsub"
    return filename, season, episode, version


def _version_key(css_class: str, title: str) -> str:
    if "dub" in css_class.lower() or "دوبله" in title:
        return "dub"
    return "hardsub"


def ygroup(m: re.Match | None) -> str:
    return m.group(0).strip("-/") if m else ""


def _strip_tags(html_text: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", html_text)).strip()


def parse_categories(html: str) -> tuple[list[tuple[str, str]], dict[str, list[tuple[str, str]]]]:
    """Parse homepage navigation links into main sections and movie/series genres."""
    if not html or not html.strip():
        return [], {"movie": [], "series": []}

    soup = BeautifulSoup(html, "html.parser")
    sections: list[tuple[str, str]] = []
    seen_sections: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        # Check if nav link
        if re.search(r'/(?:movies|series|250tmdb|250tsdb|persons)/?$', href):
            if href not in seen_sections:
                seen_sections.add(href)
                sections.append((text, href))

    genres: dict[str, list[tuple[str, str]]] = {"movie": [], "series": []}
    seen_genres: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        m = re.search(r'/genres/(?P<slug>[^/?"]+)/\?type=(?P<type>movie|series)', href)
        if m:
            g_type = m.group("type")
            g_name = a.get_text(strip=True)
            if href not in seen_genres:
                seen_genres.add(href)
                genres[g_type].append((g_name, href))

    return sections, genres


def parse_listing(html: str) -> tuple[list[Card], int]:
    """Parse HTML category or search results into Card objects and max page number."""
    if not html or not html.strip():
        return [], 1

    soup = BeautifulSoup(html, "html.parser")
    cards: list[Card] = []
    seen: set[str] = set()

    for article in soup.find_all("article", class_=lambda c: c and "entry" in c):
        stretched = article.find("a", class_="stretched-link", href=True)
        if not stretched:
            # Fallback to entry-title link
            title_tag = article.find(class_="entry-title")
            stretched = title_tag.find("a", href=True) if title_tag else None

        if not stretched or not stretched.get("href"):
            continue

        url = stretched["href"].strip()
        if url in seen:
            continue
        seen.add(url)

        title_elem = article.find(class_="entry-title")
        if title_elem:
            title = _strip_tags(title_elem.get_text(strip=True))
        else:
            title = url.rstrip("/").rsplit("/", 1)[-1]

        img_elem = article.find("img")
        poster = img_elem.get("src", "").strip() if img_elem else ""

        note_elem = article.find("p", class_=lambda c: c and "text-center" in c)
        note = _strip_tags(note_elem.get_text(strip=True)) if note_elem else ""

        ym = YEAR_SLUG_PATTERN.search(url.rstrip("/"))
        kind = "series" if "/series/" in url else "movie"

        cards.append(Card(
            url=url,
            title=title,
            note=note,
            poster=poster,
            year=ygroup(ym),
            kind=kind,
        ))

    last = 1
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m1 = re.search(r'/page/(\d+)/', href)
        if m1:
            last = max(last, int(m1.group(1)))
        m2 = re.search(r'[?&]page=(\d+)', href)
        if m2:
            last = max(last, int(m2.group(1)))

    return cards, last


def parse_quick_search(data: list[dict[str, Any]] | str, base_url: str) -> list[SearchResult]:
    """Parse quick-search JSON payload into a list of SearchResult entities."""
    if isinstance(data, str):
        import json
        try:
            data = json.loads(data)
        except Exception as exc:
            raise F2MParseError(f"Malformed quick-search JSON: {exc}") from exc

    if not isinstance(data, list):
        return []

    results: list[SearchResult] = []
    base_slash = base_url.rstrip("/") + "/"

    for it in data:
        if not isinstance(it, dict) or not it.get("url"):
            continue
        raw_title = str(it.get("title", ""))
        title = re.sub(r"</?em>", "", raw_title)
        full_url = urljoin(base_slash, str(it["url"]).lstrip("/"))

        results.append(SearchResult(
            kind="series" if it.get("type") == "series" else "movie",
            title=unescape(title).strip(),
            title_fa=unescape(str(it.get("title_fa", "") or "")).strip(),
            year=str(it.get("year", "") or "").strip(),
            rating=str(it.get("rating", "") or "").strip(),
            url=full_url,
            image=str(it.get("image", "") or "").strip(),
            meta=unescape(str(it.get("meta_data", "") or "")).strip(),
            is_dub=bool(it.get("is_dubbled")),
            is_hardsub=bool(it.get("is_hardsub")),
        ))

    return results


def _extract_episodes_from_li(li: Tag) -> list[Episode]:
    """Extract Episode entities from a list item container."""
    episodes: dict[int, Episode] = {}
    for a in li.find_all("a", href=True):
        href = a["href"].strip()
        if not MEDIA_EXT_PATTERN.search(href):
            continue
        if TRAILER_TOKEN.search(href):
            continue

        text = a.get_text(strip=True)
        lm = re.search(r'قسمت\s*(\d+)', text)
        _, s, e, _ = parse_filename(href)
        num = e or (int(lm.group(1)) if lm else len(episodes) + 1)
        if num not in episodes:
            episodes[num] = Episode(
                num=num,
                url=href,
                filename=unquote(href.rsplit("/", 1)[-1]),
                label=f"قسمت {num}",
            )
    return [episodes[k] for k in sorted(episodes)]


def _extract_quality_from_li(li: Tag) -> Quality | None:
    """Extract Quality container from an li element."""
    # Look for quality label in text or spans
    text = li.get_text()
    qm = re.search(r'کیفیت\s*:\s*([^<\n\r]+)', text)
    label = qm.group(1).strip() if qm else ""
    if not label:
        # Fallback to direct regex
        qm2 = re.search(r'(?:1080p|720p|480p|2160p|4k)[^\s]*', text, re.I)
        label = qm2.group(0).strip() if qm2 else "unknown"

    em = re.search(r'انکودر\s*:\s*([^<\n\r]+)', text)
    encoder = em.group(1).strip() if em else ""
    if encoder.endswith("<"):
        encoder = encoder[:-1].strip()

    episodes = _extract_episodes_from_li(li)
    if not episodes:
        # Direct anchor fallback
        for a in li.find_all("a", href=True):
            href = a["href"].strip()
            if MEDIA_EXT_PATTERN.search(href) and not TRAILER_TOKEN.search(href):
                episodes.append(Episode(
                    num=1,
                    url=href,
                    filename=unquote(href.rsplit("/", 1)[-1]),
                ))
                break

    if episodes:
        return Quality(label=label, encoder=encoder, episodes=episodes)
    return None


def parse_post(html: str, url: str) -> MediaPost:
    """Parse movie or series post HTML into a structured MediaPost."""
    if not html or not html.strip():
        raise F2MParseError("Received empty HTML content for post")

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as exc:
        raise F2MParseError(f"HTML parsing failed: {exc}") from exc

    # 1. Title
    title = ""
    og_meta = soup.find("meta", property="og:title")
    if og_meta and og_meta.get("content"):
        title = clean_title(og_meta["content"])
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = clean_title(h1.get_text(strip=True))
    if not title:
        title = clean_title(url.rstrip("/").rsplit("/", 1)[-1])

    # 2. IMDb ID & Rating & Year
    imdb_id = ""
    for a in soup.find_all("a", href=True):
        m = IMDB_ID_PATTERN.search(a["href"])
        if m:
            imdb_id = m.group(1)
            break
    if not imdb_id:
        text_match = IMDB_ID_PATTERN.search(html)
        if text_match:
            imdb_id = text_match.group(1)

    rating = ""
    # Try finding strong tags followed by / 10
    for s_tag in soup.find_all("strong"):
        s_text = s_tag.get_text(strip=True)
        sibling = s_tag.next_sibling
        if sibling and "/ 10" in str(sibling):
            if re.match(r"^[\d.]+$", s_text):
                rating = s_text
                break
    if not rating:
        rm = IMDB_RATING_PATTERN.search(html)
        if rm:
            rating = rm.group(1).strip()

    ym = YEAR_SLUG_PATTERN.search(url.rstrip("/"))
    year = ygroup(ym)

    post = MediaPost(
        url=url,
        title=title,
        year=year,
        imdb_id=imdb_id,
        rating=rating,
    )

    # 3. Trailer URL
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if MEDIA_EXT_PATTERN.search(href) and TRAILER_TOKEN.search(href):
            post.trailer = href
            break

    # 4. Series Seasons Extraction
    season_divs = soup.find_all("div", class_=lambda c: c and "download-season" in c)
    for s_div in season_divs:
        # Title
        toggle_a = s_div.find("a", attrs={"aria-controls": True})
        if toggle_a:
            s_title = toggle_a.get_text(strip=True)
        else:
            s_title = "Season"

        season = Season(title=s_title)

        # Versions in season
        for v_div in s_div.find_all("div", class_=lambda c: c and "download-list" in c):
            v_title_tag = v_div.find("p", class_="title")
            v_title = v_title_tag.get_text(strip=True) if v_title_tag else ""
            v_class = " ".join(v_div.get("class", []))
            version = MediaVersion(
                key=_version_key(v_class, v_title),
                title=v_title,
            )

            for li in v_div.find_all("li"):
                q = _extract_quality_from_li(li)
                if q:
                    version.qualities.append(q)

            if version.qualities:
                season.versions.append(version)

        if season.versions:
            post.seasons.append(season)

    # 5. Movie Versions Extraction (if no seasons found)
    if not post.seasons:
        for v_div in soup.find_all("div", class_=lambda c: c and "download-list" in c):
            v_title_tag = v_div.find("p", class_="title")
            v_title = v_title_tag.get_text(strip=True) if v_title_tag else ""
            v_class = " ".join(v_div.get("class", []))
            version = MediaVersion(
                key=_version_key(v_class, v_title),
                title=v_title,
            )

            for li in v_div.find_all("li"):
                q = _extract_quality_from_li(li)
                if q:
                    version.qualities.append(q)

            if version.qualities:
                post.versions.append(version)

    post.is_series = bool(post.seasons) or ("/series/" in url)
    return post
