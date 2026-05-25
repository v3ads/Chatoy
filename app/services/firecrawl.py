from __future__ import annotations

import logging
import re

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

# Matches a full URL or a bare domain (with optional path) inside a message.
_URL_RE = re.compile(
    r"(https?://[^\s]+|(?:[a-z0-9][a-z0-9-]*\.)+[a-z]{2,}(?:/[^\s]*)?)",
    re.IGNORECASE,
)


def extract_first_url(text: str | None) -> str | None:
    """Return the first website URL in ``text`` (normalised to https://), or None.

    Skips domains that are part of an email address."""
    if not text:
        return None
    for match in _URL_RE.finditer(text):
        start = match.start()
        if start > 0 and text[start - 1] == "@":
            continue  # the domain of an email address, not a website
        url = match.group(0).rstrip(".,);]'\"")
        if not url.lower().startswith(("http://", "https://")):
            url = "https://" + url
        return url
    return None


class FirecrawlClient:
    """Scrapes a single page to markdown via the Firecrawl API.

    Best-effort by design: any failure returns "" so a bad URL or a Firecrawl
    outage never breaks a chat turn — the Architect just proceeds without it."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.firecrawl.dev",
        timeout: float = 25.0,
        max_chars: int = 8000,
    ) -> None:
        self._max_chars = max_chars
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    def scrape(self, url: str) -> str:
        try:
            resp = self._client.post(
                "/v1/scrape",
                json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            )
            resp.raise_for_status()
            data = resp.json()
            markdown = (data.get("data") or {}).get("markdown") or ""
            return markdown[: self._max_chars].strip()
        except Exception as exc:  # noqa: BLE001 — scraping must never break a turn
            logger.warning("Firecrawl scrape failed for %s: %s", url, exc)
            return ""


def build_scraper(settings: Settings) -> FirecrawlClient | None:
    if not settings.firecrawl_api_key:
        return None
    return FirecrawlClient(
        api_key=settings.firecrawl_api_key,
        base_url=settings.firecrawl_base_url,
    )
