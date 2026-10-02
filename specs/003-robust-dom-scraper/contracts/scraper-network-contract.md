# Phase 3 Scraper & Network API Contract

**Feature**: Phase 3 — Robust DOM Scraper & Network Reliability  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. DOM Scraper API (`f2m.core.scraper`)

```python
def clean_title(raw: str) -> str:
    """Normalize and strip Persian noise words from post titles."""

def parse_filename(url: str) -> tuple[str, int | None, int | None, str]:
    """Extract unquoted filename, season number, episode number, and audio version from media URL."""

def parse_listing(html: str) -> tuple[list[Card], int]:
    """Parse HTML category or search results into Card objects and max page number."""

def parse_post(html: str, url: str) -> MediaPost:
    """Parse movie or series post HTML into a structured MediaPost."""

def parse_categories(html: str) -> tuple[list[tuple[str, str]], dict[str, list[tuple[str, str]]]]:
    """Parse homepage navigation into main sections and movie/series genres."""

def parse_quick_search(data: list[dict[str, Any]], base_url: str) -> list[SearchResult]:
    """Parse quick-search JSON payload into a list of SearchResult entities."""
```

---

## 2. HTTP Client API (`f2m.net.client`)

```python
class HttpClient:
    def __init__(
        self,
        base_url: str,
        mirrors: list[str] | None = None,
        proxy: str = "",
        user_agent: str = DEFAULT_UA,
        timeout: int = 25,
        max_retries: int = 2,
        backoff_factor: float = 0.5,
    ):
        ...

    @property
    def current_base_url(self) -> str:
        """Active session base URL (updated transiently on redirects)."""

    def fetch(
        self,
        path_or_url: str,
        *,
        referer: str | None = None,
        ajax: bool = False,
        data: bytes | None = None,
        allow_mirrors: bool = True,
    ) -> str:
        """
        Execute an HTTP request with bounded retries, exponential backoff,
        and mirror failover. Raises F2MNetworkError on ultimate failure.
        """
```
