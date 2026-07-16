# SPDX-License-Identifier: MIT
"""Tests for the fetch engine."""

import pytest
from src.fetch import FetchEngine, PageContent


class TestPageContent:
    def test_defaults(self):
        p = PageContent(url="https://example.com")
        assert p.url == "https://example.com"
        assert p.html == ""
        assert p.status_code == 0

    def test_fetched_with_default(self):
        p = PageContent(url="https://example.com")
        assert p.fetched_with == "http"


class TestFetchEngine:
    def test_needs_js_detection(self):
        engine = FetchEngine()
        assert engine._needs_js("<html><script src='app.js'></script>")
        assert engine._needs_js('<div id="root"></div>')
        assert not engine._needs_js("<html><p>Hello</p></html>")

    def test_user_agent_default(self):
        engine = FetchEngine(user_agent_rotation=False)
        ua = engine._get_user_agent()
        assert "Chrome" in ua

    def test_robots_txt_respected_by_default(self):
        engine = FetchEngine()
        assert engine.respect_robots_txt is True

    def test_robots_txt_disabled(self):
        engine = FetchEngine(respect_robots_txt=False)
        assert engine.respect_robots_txt is False

    @pytest.mark.asyncio
    async def test_http_fetch_fails_gracefully(self):
        engine = FetchEngine()
        result = await engine._http_fetch("http://invalid-host-xyz.local/test")
        assert result.status_code != 200

    @pytest.mark.asyncio
    async def test_close_without_browser(self):
        engine = FetchEngine()
        await engine.close()  # should not raise
