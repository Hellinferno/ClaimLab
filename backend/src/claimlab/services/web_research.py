"""TinyFish web search and page fetch for the live tutor's background research."""
import logging
from typing import Any, Dict, List
from urllib.parse import urlparse

import httpx

from claimlab.config import settings

logger = logging.getLogger(__name__)

MAX_RESULTS = 6
MAX_PAGE_CHARS = 6000
SEARCH_TIMEOUT_SECONDS = 15.0
# TinyFish allows 110 s per URL; a tutor turn cannot wait that long.
FETCH_TIMEOUT_SECONDS = 30.0


class WebResearchError(RuntimeError):
    """A web lookup failed; the message is safe to return to the model."""


def web_research_enabled() -> bool:
    return bool(settings.TINYFISH_API_KEY)


def _headers() -> Dict[str, str]:
    return {"X-API-Key": settings.TINYFISH_API_KEY}


def _error_for(response: httpx.Response) -> WebResearchError:
    if response.status_code in (401, 403):
        return WebResearchError("Web research is not authorized; check TINYFISH_API_KEY.")
    if response.status_code == 402:
        return WebResearchError("The web research allowance is used up for today.")
    if response.status_code == 429:
        return WebResearchError("Web research is rate limited; continue without it.")
    return WebResearchError(f"Web research failed (HTTP {response.status_code}).")


def search_web(query: str, domain_type: str = "web") -> List[Dict[str, Any]]:
    """Top results for a query as {title, url, site, snippet}; snippets are untrusted text."""
    query = query.strip()[:400]
    if not query:
        raise WebResearchError("Search query is empty.")
    if domain_type not in ("web", "research_paper", "news"):
        domain_type = "web"
    try:
        response = httpx.get(
            settings.TINYFISH_SEARCH_URL,
            params={"query": query, "domain_type": domain_type, "language": "en"},
            headers=_headers(),
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        logger.warning("TinyFish search request failed (%s)", type(exc).__name__)
        raise WebResearchError("Web search is unavailable right now.") from exc
    if response.status_code != 200:
        raise _error_for(response)
    results = response.json().get("results") or []
    return [
        {
            "title": str(item.get("title") or "")[:200],
            "url": str(item.get("url") or ""),
            "site": str(item.get("site_name") or "")[:80],
            "snippet": str(item.get("snippet") or "")[:400],
        }
        for item in results[:MAX_RESULTS]
        if str(item.get("url") or "").startswith(("http://", "https://"))
    ]


def fetch_page(url: str) -> Dict[str, Any]:
    """Readable markdown for one public page, truncated to a bounded excerpt."""
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise WebResearchError("Only public http(s) URLs can be read.")
    try:
        response = httpx.post(
            settings.TINYFISH_FETCH_URL,
            json={"urls": [url], "format": "markdown", "per_url_timeout_ms": int(FETCH_TIMEOUT_SECONDS * 1000) - 2000},
            headers=_headers(),
            timeout=FETCH_TIMEOUT_SECONDS + 5,
        )
    except httpx.HTTPError as exc:
        logger.warning("TinyFish fetch request failed (%s)", type(exc).__name__)
        raise WebResearchError("The page could not be read right now.") from exc
    if response.status_code != 200:
        raise _error_for(response)
    body = response.json()
    results = body.get("results") or []
    if not results:
        errors = body.get("errors") or [{}]
        raise WebResearchError(f"The page could not be read ({errors[0].get('error', 'unknown error')}).")
    page = results[0]
    text = page.get("text") if isinstance(page.get("text"), str) else ""
    return {
        "title": str(page.get("title") or "")[:200],
        "url": str(page.get("final_url") or page.get("url") or url),
        "text": text[:MAX_PAGE_CHARS],
        "truncated": len(text) > MAX_PAGE_CHARS,
    }
