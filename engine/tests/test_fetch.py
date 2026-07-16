# SPDX-License-Identifier: MIT
"""Tests for the fetch engine — with mock isolation for external HTTP."""

from __future__ import annotations
from unittest import mock

import httpx
import pytest
from src.fetch import FetchEngine, PageContent


def _mock_http_response(status=200, text="", url="https://example.com"):
    """Helper to create a mock httpx.Response."""
    return httpx.Response(status, text=text, request=httpx.Request("GET", url))


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
        assert FetchEngine().respect_robots_txt is True

    def test_robots_txt_disabled(self):
        assert FetchEngine(respect_robots_txt=False).respect_robots_txt is False

    def test_robots_txt_allows_when_parse_fails(self):
        engine = FetchEngine()
        import asyncio
        allowed = asyncio.run(engine._check_robots_txt("https://example.com/page"))
        assert allowed is True

    @pytest.mark.asyncio
    async def test_http_fetch_returns_mocked_content(self):
        engine = FetchEngine()
        async def mock_get(*a, **kw):
            return _mock_http_response(200, "<html><body>Mocked!</body></html>")

        with mock.patch("httpx.AsyncClient.get", mock_get):
            result = await engine._http_fetch("https://example.com")
            assert result.status_code == 200
            assert "Mocked!" in result.html

    @pytest.mark.asyncio
    async def test_http_fetch_handles_connection_error(self):
        engine = FetchEngine()
        async def mock_get(*a, **kw):
            raise httpx.ConnectError("refused", request=httpx.Request("GET", "https://example.com"))

        with mock.patch("httpx.AsyncClient.get", mock_get):
            result = await engine._http_fetch("https://example.com")
            assert result.status_code == 0

    @pytest.mark.asyncio
    async def test_fetch_skipped_by_robots_txt(self):
        engine = FetchEngine()
        with mock.patch.object(engine, "_check_robots_txt", return_value=False):
            with mock.patch("httpx.AsyncClient.get") as mock_http:
                result = await engine.fetch("https://example.com/blocked")
                assert result.status_code == 0
                mock_http.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_http_success_does_not_call_playwright(self):
        engine = FetchEngine()
        async def mock_get(*a, **kw):
            return _mock_http_response(200, "<html><body>No JS</body></html>")

        with mock.patch.object(engine, "_check_robots_txt", return_value=True):
            with mock.patch("httpx.AsyncClient.get", mock_get):
                with mock.patch.object(engine, "_browser_fetch") as mock_bf:
                    result = await engine.fetch("https://example.com")
                    assert result.status_code == 200
                    mock_bf.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_falls_back_to_playwright_for_js(self):
        engine = FetchEngine()
        async def mock_http(*a, **kw):
            return _mock_http_response(200, '<html><div id="root">JS app</div></html>')

        async def mock_browser(url):
            return PageContent(url="https://example.com", html="<html>Rendered</html>",
                               status_code=200, fetched_with="playwright")

        with mock.patch.object(engine, "_check_robots_txt", return_value=True):
            with mock.patch("httpx.AsyncClient.get", mock_http):
                with mock.patch.object(engine, "_browser_fetch", mock_browser):
                    result = await engine.fetch("https://example.com")
                    assert result.fetched_with == "playwright"

    @pytest.mark.asyncio
    async def test_close_without_browser(self):
        engine = FetchEngine()
        await engine.close()
