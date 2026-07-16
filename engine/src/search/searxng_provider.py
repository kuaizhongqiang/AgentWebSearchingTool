# SPDX-License-Identifier: MIT
"""SearXNG search provider — delegates search to the local SearXNG-core instance."""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx

from . import SearchProvider, SearchResponse, SearchResult

logger = logging.getLogger(__name__)


async def _search_via_http(url: str, timeout: float) -> dict:
    """HTTP client call extracted for test mocking."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


class SearXNGProvider(SearchProvider):
    """Search provider backed by a local SearXNG-core instance."""

    def __init__(self, searxng_url: str = "http://127.0.0.1:8888", timeout: float = 30.0):
        self.searxng_url = searxng_url.rstrip("/")
        self.timeout = timeout

    async def search(
        self,
        query: str,
        num: int = 10,
        engine: str = "google",
        page: int = 1,
    ) -> SearchResponse:
        params = {"q": query, "format": "json", "pageno": page, "engines": engine}
        url = f"{self.searxng_url}/search?{urlencode(params)}"
        logger.debug("SearXNG request: %s", url)

        data = await _search_via_http(url, self.timeout)

        results = [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                engine=engine,
                score=item.get("score", 0.0),
                category=item.get("category", "general"),
            )
            for item in data.get("results", [])
        ]

        unresponsive = [e[0] if isinstance(e, list) else str(e) for e in data.get("unresponsive_engines", [])]

        return SearchResponse(query=query, results=results[:num], unresponsive_engines=unresponsive, page=page)
