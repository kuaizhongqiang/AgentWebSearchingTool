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
        assert p.fetched_with == "http"


class TestFetchEngine:
    def test_needs_js_detection(self):
        engine = FetchEngine()

        # Pages with JS indicators
        assert engine._needs_js("<html><script src='app.js'></script>")
        assert engine._needs_js('<div id="root"></div>')
        assert engine._needs_js("<html><div ng-app='myApp'></div>")

        # Plain HTML
        assert not engine._needs_js("<html><p>Hello</p></html>")
        assert not engine._needs_js("<html><div>No JS here</div></html>")

    def test_user_agent_default(self):
        engine = FetchEngine(user_agent_rotation=False)
        ua = engine._get_user_agent()
        assert "Chrome" in ua
        assert "Windows" in ua

    @pytest.mark.asyncio
    async def test_http_fetch_fails_gracefully(self):
        """Fetching an invalid URL should not raise an exception."""
        engine = FetchEngine()
        result = await engine._http_fetch("http://invalid-host-xyz.local/nonexistent")
        assert result.status_code != 200  # any error status is fine
        assert "invalid-host-xyz.local" in result.url
