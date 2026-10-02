"""
Domain entities and models for film2media-cli.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from html import unescape
from typing import Any
from urllib.parse import unquote


@dataclass
class SearchResult:
    """Represents an individual entry returned by quick-search or HTML search fallback."""
    kind: str
    title: str
    url: str
    title_fa: str = ""
    year: str = ""
    rating: str = ""
    image: str = ""
    meta: str = ""
    is_dub: bool = False
    is_hardsub: bool = False

    def __post_init__(self) -> None:
        self.kind = self.kind.strip().lower() if self.kind else "movie"
        if self.kind not in ("movie", "series"):
            self.kind = "movie"
        # Normalize title: unescape HTML, strip <em> highlights, strip whitespace
        if self.title:
            cleaned = re.sub(r"</?em>", "", self.title)
            self.title = unescape(cleaned).strip()
        if self.title_fa:
            self.title_fa = unescape(self.title_fa).strip()
        if self.meta:
            self.meta = unescape(self.meta).strip()
        self.url = self.url.strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchResult:
        known_keys = {
            "kind", "title", "url", "title_fa", "year",
            "rating", "image", "meta", "is_dub", "is_hardsub"
        }
        filtered = {k: v for k, v in data.items() if k in known_keys}
        return cls(**filtered)


@dataclass
class Card:
    """Represents an article entry card during HTML category and pagination browsing."""
    url: str
    title: str
    note: str = ""
    poster: str = ""
    year: str = ""
    kind: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Card:
        known_keys = {"url", "title", "note", "poster", "year", "kind"}
        filtered = {k: v for k, v in data.items() if k in known_keys}
        return cls(**filtered)


@dataclass
class Episode:
    """Represents an individual downloadable or streamable media file."""
    num: int
    url: str
    filename: str = ""
    label: str = ""

    def __post_init__(self) -> None:
        if self.num < 1:
            self.num = 1
        self.url = self.url.strip()
        if not self.filename:
            self.filename = unquote(self.url.rsplit("/", 1)[-1])
        if not self.label:
            self.label = f"قسمت {self.num}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Episode:
        known_keys = {"num", "url", "filename", "label"}
        filtered = {k: v for k, v in data.items() if k in known_keys}
        return cls(**filtered)


@dataclass
class Quality:
    """Represents a specific resolution and encoding format release block."""
    label: str
    encoder: str = ""
    episodes: list[Episode] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.label = self.label.strip() if self.label else "unknown"
        self.encoder = self.encoder.strip()
        if self.encoder.lower() == "unknown":
            self.encoder = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "encoder": self.encoder,
            "episodes": [ep.to_dict() for ep in self.episodes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Quality:
        episodes_data = data.get("episodes", [])
        episodes = [
            ep if isinstance(ep, Episode) else Episode.from_dict(ep)
            for ep in episodes_data
        ]
        return cls(
            label=data.get("label", "unknown"),
            encoder=data.get("encoder", ""),
            episodes=episodes,
        )


@dataclass
class MediaVersion:
    """Represents an audio/subtitle translation version block (Dub vs Hardsub)."""
    key: str
    title: str
    qualities: list[Quality] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.key = self.key.strip().lower()
        if self.key not in ("dub", "hardsub"):
            self.key = "hardsub"
        self.title = self.title.strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "qualities": [q.to_dict() for q in self.qualities],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MediaVersion:
        qualities_data = data.get("qualities", [])
        qualities = [
            q if isinstance(q, Quality) else Quality.from_dict(q)
            for q in qualities_data
        ]
        return cls(
            key=data.get("key", "hardsub"),
            title=data.get("title", ""),
            qualities=qualities,
        )


# Backward-compatible alias
Version = MediaVersion


@dataclass
class Season:
    """Represents a television series season."""
    title: str
    number: int = 1
    versions: list[MediaVersion] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if self.number < 1:
            self.number = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "number": self.number,
            "versions": [v.to_dict() for v in self.versions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Season:
        versions_data = data.get("versions", [])
        versions = [
            v if isinstance(v, MediaVersion) else MediaVersion.from_dict(v)
            for v in versions_data
        ]
        return cls(
            title=data.get("title", "Season"),
            number=data.get("number", 1),
            versions=versions,
        )


@dataclass
class MediaPost:
    """Represents the complete resolved metadata and downloadable structure of a post."""
    url: str
    title: str
    year: str = ""
    imdb_id: str = ""
    rating: str = ""
    is_series: bool = False
    seasons: list[Season] = field(default_factory=list)
    versions: list[MediaVersion] = field(default_factory=list)
    trailer: str = ""

    def __post_init__(self) -> None:
        self.url = self.url.strip()
        self.title = self.title.strip()
        self.year = self.year.strip()
        self.imdb_id = self.imdb_id.strip()
        self.rating = self.rating.strip()
        self.trailer = self.trailer.strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "year": self.year,
            "imdb_id": self.imdb_id,
            "rating": self.rating,
            "is_series": self.is_series,
            "seasons": [s.to_dict() for s in self.seasons],
            "versions": [v.to_dict() for v in self.versions],
            "trailer": self.trailer,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MediaPost:
        seasons_data = data.get("seasons", [])
        seasons = [
            s if isinstance(s, Season) else Season.from_dict(s)
            for s in seasons_data
        ]
        versions_data = data.get("versions", [])
        versions = [
            v if isinstance(v, MediaVersion) else MediaVersion.from_dict(v)
            for v in versions_data
        ]
        return cls(
            url=data.get("url", ""),
            title=data.get("title", ""),
            year=data.get("year", ""),
            imdb_id=data.get("imdb_id", ""),
            rating=data.get("rating", ""),
            is_series=data.get("is_series", False),
            seasons=seasons,
            versions=versions,
            trailer=data.get("trailer", ""),
        )


# Backward-compatible alias
Post = MediaPost
