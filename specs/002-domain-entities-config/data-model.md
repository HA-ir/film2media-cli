# Phase 2 Data Model & Domain Entity Specification

**Feature**: Phase 2 — Domain Entities & XDG Configuration Engine  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Domain Entities Architecture (`f2m.core.models`)

### 1.1 `SearchResult`
Represents an individual entry returned by quick-search (AJAX) or HTML search fallback.

```python
@dataclass
class SearchResult:
    kind: str             # "movie" | "series"
    title: str            # Clean English title
    url: str              # Absolute URL
    title_fa: str = ""    # Persian localized title
    year: str = ""        # 4-digit year string
    rating: str = ""      # IMDb rating string (e.g. "8.8")
    image: str = ""       # Poster URL
    meta: str = ""        # Summary note / genre badges
    is_dub: bool = False  # Dubbed audio available
    is_hardsub: bool = False # Hardcoded subtitle available
```

**Normalization & Validation**:
- `kind`: Lowercased, must be `"movie"` or `"series"`.
- `title`: Unescapes HTML entities, strips `<em>` tags, strips whitespace.
- `url`: Strips whitespace, validated non-empty.

---

### 1.2 `Card`
Represents a listing summary entry card during HTML category and pagination browsing.

```python
@dataclass
class Card:
    url: str
    title: str
    note: str = ""
    poster: str = ""
    year: str = ""
    kind: str = ""
```

---

### 1.3 `Episode`
Represents an individual downloadable or streamable media file.

```python
@dataclass
class Episode:
    num: int              # Episode number (>= 1, or 1 for single movies)
    url: str              # Direct download URL (.mkv, .mp4, etc.)
    filename: str         # Unquoted filename extracted from URL
    label: str = ""       # Display label (e.g., "قسمت 01")
```

**Normalization & Validation**:
- `num`: Must be integer >= 1.
- `url`: Validated non-empty string.
- `filename`: If not provided, computed via `urllib.parse.unquote(url.rsplit('/', 1)[-1])`.
- `label`: If empty, defaults to `f"قسمت {num}"`.

---

### 1.4 `Quality`
Represents a specific resolution and encoding format release block.

```python
@dataclass
class Quality:
    label: str            # Resolution label (e.g., "1080p BluRay", "720p x265")
    encoder: str = ""     # Encoder group (e.g., "F2M", "PSA", "Pahe")
    episodes: list[Episode] = field(default_factory=list)
```

**Normalization**:
- `encoder`: Strip whitespace. If `"unknown"`, normalized to empty string.

---

### 1.5 `MediaVersion` (Aliased as `Version`)
Represents an audio/subtitle translation version block.

```python
@dataclass
class MediaVersion:
    key: str              # "dub" | "hardsub"
    title: str            # Human-readable title (e.g., "نسخه دوبله فارسی")
    qualities: list[Quality] = field(default_factory=list)

# Backward-compatible alias
Version = MediaVersion
```

---

### 1.6 `Season`
Represents a television series season.

```python
@dataclass
class Season:
    title: str            # Display title (e.g., "فصل اول")
    number: int = 1       # Season number
    versions: list[MediaVersion] = field(default_factory=list)
```

---

### 1.7 `MediaPost` (Aliased as `Post`)
Represents the complete resolved metadata and downloadable structure of a movie or series post.

```python
@dataclass
class MediaPost:
    url: str
    title: str
    year: str = ""
    imdb_id: str = ""
    rating: str = ""
    is_series: bool = False
    seasons: list[Season] = field(default_factory=list)
    versions: list[MediaVersion] = field(default_factory=list)
    trailer: str = ""

# Backward-compatible alias
Post = MediaPost
```

---

### 1.8 `ConfigurationProfile`
Represents the validated runtime configuration profile.

```python
@dataclass
class ConfigurationProfile:
    base_url: str = "https://www.myf2ms.top"
    mirrors: list[str] = field(default_factory=lambda: ["https://www.myf2m.info", "https://www.myf2ms.top"])
    proxy: str = ""
    search_sort: str = "modified_at:desc"
    player: str = "auto"
    download_dir: str = "~/Downloads/f2m"
    user_agent: str = DEFAULT_UA

    @property
    def raw_mirrors(self) -> str:
        return ", ".join(self.mirrors)

    def proxies_dict(self) -> dict[str, str | None]:
        p = self.proxy.strip()
        return {"http": p or None, "https": p or None} if p else {}
```

---

## 2. Serialization & Deserialization Protocol

Every dataclass in `f2m.core.models` implements:
- `to_dict() -> dict[str, Any]`: Recursively converts the entity and its children into primitive JSON-compatible types.
- `from_dict(data: dict[str, Any]) -> ModelType`: Classmethod that instantiates the entity, recursively hydrating child entities, and safely ignoring unknown keys.
