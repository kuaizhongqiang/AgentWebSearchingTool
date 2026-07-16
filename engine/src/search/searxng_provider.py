# SPDX-License-Identifier: MIT
"""SearXNG search provider — delegates search to the local SearXNG-core instance."""

from __future__ import annotations

import json
import logging
from urllib.parse import urlencode

import httpx

from . import SearchProvider, SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class SearXNGProvider(SearchProvider):
    """Search provider backed by a local SearXNG-core instance.

    Communicates via HTTP with the SearXNG JSON API.
    """

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
        """Execute search via SearXNG JSON API."""
        params = {
            "q": query,
            "format": "json",
            "pageno": page,
            "engines": engine,
        }

        url = f"{self.searxng_url}/search?{urlencode(params)}"
        logger.debug("SearXNG request: %s", url)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    engine=engine,
                    score=item.get("score", 0.0),
                    category=item.get("category", "general"),
                )
            )

        unresponsive = [
            e[0] if isinstance(e, list) else str(e)
            for e in data.get("unresponsive_engines", [])
        ]

        return SearchResponse(
            query=query,
            results=results[:num],
            unresponsive_engines=unresponsive,
            page=page,
        )
