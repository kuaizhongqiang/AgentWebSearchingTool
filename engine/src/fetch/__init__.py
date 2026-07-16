# SPDX-License-Identifier: MIT
"""Fetch engine — hybrid HTTP + Playwright page fetcher."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    """Fetched page content."""

    url: str
    html: str = ""
    text: str = ""
    status_code: int = 0
    headers: dict[str, str] = field(default_factory=dict)
    fetched_with: str = "http"  # "http" | "playwright"


class FetchEngine:
    """Hybrid fetch engine — HTTP first, Playwright fallback for JS pages.

    Uses the given HTTP fetcher and optional Playwright browser fetcher.
    If no browser fetcher is provided, falls back to HTTP only.
    """

    JS_NEEDLE = re.compile(
        r"<script|ng-app|ng-view|react-root|__NUXT__|__NEXT_DATA__|"
        r"id=\"root\"|id=\"app\"|data-server-rendered",
        re.I,
    )

    def __init__(
        self,
        request_interval: float = 1.0,
        max_concurrent: int = 5,
        respect_robots_txt: bool = True,
        user_agent_rotation: bool = False,
    ):
        self.request_interval = request_interval
        self.max_concurrent = max_concurrent
        self.respect_robots_txt = respect_robots_txt
        self.user_agent_rotation = user_agent_rotation
        self._browser = None

    async def fetch(self, url: str) -> PageContent:
        """Fetch a single page: HTTP first, fallback to Playwright if needed."""
        content = await self._http_fetch(url)

        if content.status_code == 200 and self._needs_js(content.html):
            logger.debug("JS-rendered page detected, falling back to Playwright: %s", url)
            try:
                content = await self._browser_fetch(url)
                content.fetched_with = "playwright"
            except Exception as e:
                logger.warning("Playwright fetch failed for %s: %s", url, e)

        return content

    async def fetch_many(self, urls: list[str]) -> list[PageContent]:
        """Fetch multiple pages concurrently (up to max_concurrent)."""
        import asyncio

        sem = asyncio.Semaphore(self.max_concurrent)

        async def _fetch_one(url: str) -> PageContent:
            async with sem:
                return await self.fetch(url)

        tasks = [_fetch_one(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def _http_fetch(self, url: str) -> PageContent:
        """Plain HTTP fetch using httpx."""
        import httpx

        headers = {"User-Agent": self._get_user_agent()}
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                return PageContent(
                    url=str(resp.url),
                    html=resp.text,
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                    fetched_with="http",
                )
        except Exception as e:
            logger.warning("HTTP fetch failed for %s: %s", url, e)
            return PageContent(url=url, status_code=0, fetched_with="http")

    async def _browser_fetch(self, url: str) -> PageContent:
        """Fetch using Playwright (headless Chromium)."""
        if self._browser is None:
            from playwright.async_api import async_playwright

            p = await async_playwright().start()
            self._browser = await p.chromium.launch(headless=True)
            self._playwright = p

        page = await self._browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            final_url = page.url
            return PageContent(
                url=final_url,
                html=content,
                status_code=200,
                fetched_with="playwright",
            )
        finally:
            await page.close()

    def _needs_js(self, html: str) -> bool:
        """Check if the page likely needs JS rendering."""
        return bool(self.JS_NEEDLE.search(html[:5000]))

    _user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    ]

    def _get_user_agent(self) -> str:
        if self.user_agent_rotation:
            import random
            return random.choice(self._user_agents)
        return self._user_agents[0]
