# Phase 3 Data Model & Scraper Extraction Contracts

**Feature**: Phase 3 — Robust DOM Scraper & Network Reliability  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Domain Entities Utilized

Phase 3 introduces **no duplicate domain models**. It consumes and populates the existing Phase 2 entities from `f2m.core.models`:

- **`SearchResult`**: Populated by `parse_quick_search()` and `parse_listing()` fallback.
- **`Card`**: Populated by `parse_listing()` for category/pagination browsing.
- **`Episode`**: Populated for each media download link in a quality container.
- **`Quality`**: Populated with resolution label, encoder, and episode list.
- **`MediaVersion` (`Version`)**: Populated with version key (`"dub"` vs `"hardsub"`), title, and qualities.
- **`Season`**: Populated with season title, number, and audio versions.
- **`MediaPost` (`Post`)**: Root container for movie or series metadata, versions, and trailer.

---

## 2. Extraction Contracts & Fallback Rules

| Target Concept | Primary DOM Selector | Secondary / Text Fallback | Fallback Rule if Missing |
|---|---|---|---|
| **Post Title** | `meta[property="og:title"]['content']` | `h1.entry-title` or `h1` | Unquoted URL slug cleaned of noise |
| **IMDb ID** | `a[href*="imdb.com/title/tt"]` regex `(tt\d+)` | Page text regex `imdb\.com/title/(tt\d+)` | Empty string `""` |
| **IMDb Rating** | `.imdb-box strong` or `strong:contains('/ 10')` | Regex `([\d.]+)\s*/\s*10` | Empty string `""` |
| **Trailer URL** | `a[href*="trailer"]['href']` | Media link regex containing `trailer` | Empty string `""` |
| **Listing Cards** | `article.entry` | `div.entry`, `article` | Empty card list `[]` |
| **Card Title** | `h2.entry-title a` or `h2.entry-title` | `a.stretched-link` | URL slug |
| **Card URL** | `a.stretched-link['href']` | `h2.entry-title a['href']` | Skip card |
| **Pagination Max** | `.page-numbers` numeric texts | Regex `page/(\d+)` in links | `1` (single page) |
| **Season Containers**| `div.download-season` | - | Empty seasons list (triggers movie version extraction) |
| **Download Lists** | `div.download-list` | - | Empty version list |
| **Quality Blocks** | `li:has(span:contains('کیفیت'))` | `li` containing media URLs | Extract links directly |
| **Episode Links** | `a[href$=".mkv"], a[href$=".mp4"]` | Regex on anchor text `قسمت\s*(\d+)` | Sequential 1-based index |
