"""
Resilient HTTP client for film2media-cli.
Supports bounded retries, exponential backoff, ordered mirror failover,
proxy routing, and session-transient domain redirect handling.
"""

from __future__ import annotations

import http.client
import os
import sys
import time
from http.cookiejar import CookieJar
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from f2m.core.exceptions import F2MNetworkError

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
)

RETRYABLE_STATUSES = {429, 502, 503, 504}


class HttpClient:
    """
    HTTP client providing mirror failover, bounded retries with backoff,
    and session-transient domain redirect tracking.
    """

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
        self._configured_base_url = base_url.rstrip("/")
        self._session_base_url = self._configured_base_url
        self._mirrors = [m.rstrip("/") for m in (mirrors or []) if m.strip()]
        self._proxy = proxy.strip()
        self._user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.backoff_factor = backoff_factor

        self._cookie_jar = CookieJar()
        self._opener = self._build_opener()

    def _build_opener(self) -> urlrequest.OpenerDirector:
        proxies_map = (
            {"http": self._proxy, "https": self._proxy}
            if self._proxy
            else {}
        )
        return urlrequest.build_opener(
            urlrequest.HTTPCookieProcessor(self._cookie_jar),
            urlrequest.ProxyHandler(proxies_map),
        )

    @property
    def current_base_url(self) -> str:
        """Active base URL for the running session (transiently updated on redirects)."""
        return self._session_base_url

    @property
    def base_url(self) -> str:
        """Configured base URL (or current active base URL)."""
        return self._session_base_url

    def set_session_base_url(self, new_url: str) -> None:
        """Update session-transient base URL without touching on-disk config."""
        self._session_base_url = new_url.rstrip("/")

    def _headers(self, referer: str | None, ajax: bool) -> dict[str, str]:
        h = {
            "User-Agent": self._user_agent,
            "Accept": "*/*" if ajax else "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en,fa;q=0.9",
        }
        if referer:
            h["Referer"] = referer
            split = urlparse.urlsplit(referer)
            if split.netloc:
                h["Origin"] = f"{split.scheme}://{split.netloc}"
        if ajax:
            h["X-Requested-With"] = "XMLHttpRequest"
            h["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        return h

    def _check_transient_redirect(self, final_url: str) -> None:
        try:
            new_host = urlparse.urlsplit(final_url).netloc.lower()
            curr_host = urlparse.urlsplit(self._session_base_url).netloc.lower()
            if new_host and new_host != curr_host and "f2m" in new_host:
                scheme = urlparse.urlsplit(final_url).scheme or "https"
                self.set_session_base_url(f"{scheme}://{new_host}")
        except Exception:
            pass

    def _candidate_urls(self, path_or_url: str, allow_mirrors: bool) -> list[str]:
        candidates: list[str] = []
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            candidates.append(path_or_url)
            if allow_mirrors:
                parsed = urlparse.urlsplit(path_or_url)
                curr_host = urlparse.urlsplit(self._session_base_url).netloc.lower()
                if parsed.netloc.lower() == curr_host:
                    path_q = parsed.path + ("?" + parsed.query if parsed.query else "")
                    for mirror in self._mirrors:
                        alt = mirror + path_q
                        if alt not in candidates:
                            candidates.append(alt)
        else:
            rel = "/" + path_or_url.lstrip("/")
            candidates.append(self._session_base_url + rel)
            if allow_mirrors:
                for mirror in self._mirrors:
                    alt = mirror + rel
                    if alt not in candidates:
                        candidates.append(alt)
        return candidates

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
        Execute request with bounded retries, exponential backoff, and mirror failover.
        Raises F2MNetworkError on ultimate failure.
        """
        candidates = self._candidate_urls(path_or_url, allow_mirrors and (data is None))
        last_exc: Exception | None = None
        attempted_urls: list[str] = []

        for host_url in candidates:
            attempted_urls.append(host_url)
            for attempt in range(self.max_retries + 1):
                req = urlrequest.Request(
                    host_url,
                    data=data,
                    headers=self._headers(referer or host_url, ajax),
                )
                try:
                    with self._opener.open(req, timeout=self.timeout) as resp:
                        body = resp.read().decode("utf-8", errors="replace")
                        self._check_transient_redirect(resp.geturl())
                        return body
                except urlerror.HTTPError as exc:
                    last_exc = exc
                    if exc.code in RETRYABLE_STATUSES:
                        if attempt < self.max_retries:
                            sleep_time = self.backoff_factor * (2 ** attempt)
                            time.sleep(sleep_time)
                            continue
                        else:
                            break  # advance to next mirror
                    elif exc.code in (403, 404):
                        break  # non-retryable on this mirror; try next
                    else:
                        break
                except (
                    urlerror.URLError,
                    http.client.HTTPException,
                    OSError,
                    TimeoutError,
                ) as exc:
                    last_exc = exc
                    if attempt < self.max_retries:
                        sleep_time = self.backoff_factor * (2 ** attempt)
                        time.sleep(sleep_time)
                        continue
                    else:
                        break

        detail = f"{last_exc}" if last_exc else "unknown error"
        tried_str = ", ".join(attempted_urls)
        raise F2MNetworkError(
            f"Could not reach {self._session_base_url}\n"
            f"      Reason: {detail}\n"
            f"      Attempted endpoints: {tried_str}\n"
            f"      The domain may be filtered — check proxy settings or configure active mirrors."
        )
