# SPDX-License-Identifier: MIT
"""Fetch engine — hybrid HTTP + Playwright page fetcher."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    url: str = ""
    html: str = ""
    text: str = ""
    status_code: int = 0
    headers: dict[str, str] = field(default_factory=dict)
    fetched_with: str = "http"


class FetchEngine:
    """Hybrid fetch engine — HTTP first, Playwright fallback for JS pages."""

    JS_NEEDLE = re.compile(
        r"<script|ng-app|ng-view|react-root|__NUXT__|__NEXT_DATA__|"
        r'id="root"|id="app"|data-server-rendered',
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
        self._playwright = None
        self._robot_parsers: dict[str, RobotFileParser] = {}

    async def fetch(self, url: str) -> PageContent:
        if self.respect_robots_txt and not await self._check_robots_txt(url):
            logger.info("Blocked by robots.txt: %s", url)
            return PageContent(url=url, status_code=0)
        content = await self._http_fetch(url)
        if content.status_code == 200 and self._needs_js(content.html):
            logger.debug("JS-rendered, falling back to Playwright: %s", url)
            try:
                content = await self._browser_fetch(url)
                content.fetched_with = "playwright"
            except Exception as e:
                logger.warning("Playwright fetch failed for %s: %s", url, e)
        return content

    async def fetch_many(self, urls: list[str]) -> list[PageContent]:
        import asyncio
        sem = asyncio.Semaphore(self.max_concurrent)
        async def _f(url: str) -> PageContent:
            async with sem:
                return await self.fetch(url)
        return await asyncio.gather(*[_f(u) for u in urls], return_exceptions=False)

    async def close(self):
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning("Error closing browser: %s", e)
            self._browser = None
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning("Error stopping playwright: %s", e)
            self._playwright = None

    async def _check_robots_txt(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robot_parsers:
            rp = RobotFileParser()
            rp.set_url(f"{base}/robots.txt")
            try:
                rp.read()
            except Exception:
                return True
            self._robot_parsers[base] = rp
        return self._robot_parsers[base].can_fetch(self._get_user_agent(), url)

    async def _http_fetch(self, url: str) -> PageContent:
        import httpx
        headers = {"User-Agent": self._get_user_agent()}
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                return PageContent(url=str(resp.url), html=resp.text,
                                   status_code=resp.status_code, headers=dict(resp.headers))
        except Exception as e:
            logger.warning("HTTP fetch failed for %s: %s", url, e)
            return PageContent(url=url, status_code=0)

    async def _browser_fetch(self, url: str) -> PageContent:
        if self._browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
        page = await self._browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            return PageContent(url=page.url, html=content, status_code=200, fetched_with="playwright")
        finally:
            await page.close()

    def _needs_js(self, html: str) -> bool:
        return bool(self.JS_NEEDLE.search(html[:5000]))

    _user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    ]

    def _get_user_agent(self) -> str:
        if self.user_agent_rotation:
            import random
            return random.choice(self._user_agents)
        return self._user_agents[0]
