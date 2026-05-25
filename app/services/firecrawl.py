from __future__ import annotations

import concurrent.futures
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

# Path keywords that signal a page worth reading for business context.
_RELEVANT_KEYWORDS = (
    "about",
    "pricing",
    "price",
    "plan",
    "product",
    "service",
    "feature",
    "solution",
    "how-it-works",
    "faq",
    "use-case",
    "benefit",
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
    """Reads a business's website via the Firecrawl API.

    ``gather`` discovers the site's pages, picks the most relevant ones (home,
    pricing, about, product…), scrapes them in parallel, and returns one combined
    markdown document. Best-effort throughout: any failure degrades (down to a
    single-page scrape, or "") so a bad URL or a Firecrawl outage never breaks a
    chat turn."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.firecrawl.dev",
        timeout: float = 25.0,
        max_chars: int = 4000,
        max_pages: int = 6,
        total_max_chars: int = 12000,
    ) -> None:
        self._max_chars = max_chars
        self._max_pages = max(1, max_pages)
        self._total_max_chars = total_max_chars
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    def scrape(self, url: str) -> str:
        """Scrape a single page to markdown (empty on failure)."""
        try:
            resp = self._client.post(
                "/v1/scrape",
                json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            )
            resp.raise_for_status()
            markdown = (resp.json().get("data") or {}).get("markdown") or ""
            return markdown[: self._max_chars].strip()
        except Exception as exc:  # noqa: BLE001 — scraping must never break a turn
            logger.warning("Firecrawl scrape failed for %s: %s", url, exc)
            return ""

    def _map(self, url: str) -> list[str]:
        """List the site's page URLs (empty on failure)."""
        try:
            resp = self._client.post("/v1/map", json={"url": url})
            resp.raise_for_status()
            return [u for u in (resp.json().get("links") or []) if isinstance(u, str)]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Firecrawl map failed for %s: %s", url, exc)
            return []

    @staticmethod
    def _relevance(link: str, root: str) -> int:
        score = sum(1 for kw in _RELEVANT_KEYWORDS if kw in link.lower())
        if link.rstrip("/") == root.rstrip("/"):
            score += 10  # the homepage
        # Shallower paths tend to be more important.
        score -= link.count("/")
        return score

    def _select_pages(self, url: str, links: list[str]) -> list[str]:
        ranked = sorted(set(links), key=lambda l: self._relevance(l, url), reverse=True)
        chosen = [url] if url not in ranked else []
        for link in ranked:
            if link not in chosen:
                chosen.append(link)
            if len(chosen) >= self._max_pages:
                break
        return chosen[: self._max_pages]

    def gather(self, url: str) -> str:
        """Discover, scrape, and combine the most relevant pages into one document."""
        pages = self._select_pages(url, self._map(url) or [url])
        scraped: dict[str, str] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(pages))) as ex:
            futures = {ex.submit(self.scrape, p): p for p in pages}
            for fut in concurrent.futures.as_completed(futures):
                page = futures[fut]
                try:
                    scraped[page] = fut.result()
                except Exception:  # noqa: BLE001
                    scraped[page] = ""

        parts: list[str] = []
        total = 0
        for page in pages:  # preserve relevance order
            content = scraped.get(page, "").strip()
            if not content:
                continue
            block = f"## Page: {page}\n{content}"
            if total + len(block) > self._total_max_chars:
                block = block[: max(0, self._total_max_chars - total)]
            if block:
                parts.append(block)
                total += len(block)
            if total >= self._total_max_chars:
                break
        return "\n\n".join(parts).strip()


def build_scraper(settings: Settings) -> FirecrawlClient | None:
    if not settings.firecrawl_api_key:
        return None
    return FirecrawlClient(
        api_key=settings.firecrawl_api_key,
        base_url=settings.firecrawl_base_url,
        max_pages=settings.firecrawl_max_pages,
    )
