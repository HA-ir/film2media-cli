# Data Model & Entity Specifications: film2media-cli

**Feature**: `001-baseline-specification`  
**Date**: 2026-10-01  
**Status**: Completed  

---

## 1. Domain Entities Overview

The core domain model decouples site scraping, interactive navigation, and external process runners from raw HTML strings.

```text
SearchResult (from search)
      │
      ▼
  MediaPost ─── has ───► [ Season ] ─── has ───► [ MediaVersion ]
                                                        │
                                                        ▼
                                                  [ Quality ]
                                                        │
                                                        ▼
                                                  [ Episode ]
```

---

## 2. Entity Definitions

### 2.1 SearchResult
Represents an individual entry returned by quick-search (AJAX) or HTML search fallback.

| Field | Type | Description | Validation / Constraints |
|---|---|---|---|
| `kind` | `str` | Media classification: `"movie"` or `"series"` | Must be one of `("movie", "series")` |
| `title` | `str` | Primary / English title | Non-empty string |
| `title_fa` | `str` | Persian localized title | String (may be empty) |
| `year` | `str` | Release year | 4-digit string or empty |
| `rating` | `str` | IMDb rating string (e.g. `"8.5"`) | Decimal string or empty |
| `url` | `str` | Canonical post URL on Film2Media | Valid HTTP/HTTPS URL |
| `image` | `str` | Poster image URL | Valid HTTP/HTTPS URL or empty |
| `meta` | `str` | Summary note / genre badges | String |
| `is_dub` | `bool` | Indicates Persian dubbed audio availability | Boolean flag |
| `is_hardsub` | `bool` | Indicates Persian hardcoded subtitle availability | Boolean flag |

---

### 2.2 MediaPost
Represents the fully resolved metadata and downloadable structure of a movie or series post.

| Field | Type | Description | Validation / Constraints |
|---|---|---|---|
| `url` | `str` | Canonical post URL | Valid HTTP/HTTPS URL |
| `title` | `str` | Normalized title (noise stripped) | Non-empty string |
| `year` | `str` | Release year | 4-digit string or empty |
| `imdb_id` | `str` | IMDb title identifier (e.g. `"tt0111161"`) | Matches `tt\d+` or empty |
| `rating` | `str` | IMDb rating (e.g. `"9.3"`) | Decimal string or empty |
| `is_series` | `bool` | True if television/web series; False if feature movie | Boolean flag |
| `seasons` | `list[Season]` | Structured seasons list (for series) | Empty for movies; >=1 for series |
| `versions` | `list[MediaVersion]`| Direct versions list (for movies) | >=1 for movies; empty for series |
| `trailer` | `str` | Direct trailer video stream URL | Valid media URL or empty |

---

### 2.3 Season
Represents a specific season within a series.

| Field | Type | Description | Validation / Constraints |
|---|---|---|---|
| `number` | `int` | Season sequence number | Positive integer >= 1 |
| `title` | `str` | Display title (e.g., `"فصل اول - Season 01"`) | Non-empty string |
| `versions` | `list[MediaVersion]` | Audio/subtitled versions available for this season | List of `MediaVersion` (>=1) |

---

### 2.4 MediaVersion
Represents an audio/translation version (e.g., Persian Dubbed vs Persian Soft/Hard Subbed).

| Field | Type | Description | Validation / Constraints |
|---|---|---|---|
| `key` | `str` | Canonical version key (`"dub"` or `"hardsub"`) | Must be one of `("dub", "hardsub")` |
| `title` | `str` | Human-readable version title | Non-empty string |
| `qualities` | `list[Quality]` | Available resolution and encoder options | List of `Quality` (>=1) |

---

### 2.5 Quality
Represents a specific resolution and encoding format (e.g., `1080p x265 10bit - PSA`).

| Field | Type | Description | Validation / Constraints |
|---|---|---|---|
| `label` | `str` | Quality identifier (e.g., `"1080p.Web-DL"`, `"720p.x265"`) | Non-empty string |
| `encoder` | `str` | Encoder release group (e.g., `"F2M"`, `"PSA"`, `"Pahe"`) | String (optional) |
| `episodes` | `list[Episode]` | Downloadable media files for this quality | List of `Episode` (>=1) |

---

### 2.6 Episode
Represents a single downloadable/streamable media file.

| Field | Type | Description | Validation / Constraints |
|---|---|---|---|
| `num` | `int` | Episode number (or `1` for single-part movies) | Positive integer >= 1 |
| `url` | `str` | Direct download/stream URL | Valid media URL ending in `.mkv`, `.mp4`, etc. |
| `filename` | `str` | Extracted unquoted media filename | Non-empty string |
| `label` | `str` | Display label (e.g., `"قسمت 01"`) | String |

---

### 2.7 ConfigurationProfile
Represents the persisted application configuration.

| Field | Type | Default | Description |
|---|---|---|---|
| `base_url` | `str` | `"https://www.myf2ms.top"` | Primary site URL |
| `mirrors` | `list[str]` | `["https://www.myf2m.info"]` | Fallback mirror domains |
| `proxy` | `str` | `""` | Optional HTTP/HTTPS/SOCKS5 proxy URI |
| `player` | `str` | `"auto"` | Preferred media player (`"auto"`, `"mpv"`, `"vlc"`, `"potplayer"`) |
| `download_dir`| `str` | `"~/Downloads/f2m"` | Destination directory for downloaded files |
| `search_sort` | `str` | `"modified_at:desc"` | Default sort order for quick search |
| `user_agent` | `str` | Standard modern Chrome UA | HTTP User-Agent header |
| `no_color` | `bool` | `False` | Strip ANSI formatting if True |
