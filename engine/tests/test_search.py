# SPDX-License-Identifier: MIT
"""Tests for the search provider."""

import pytest
from src.search import SearchResult, SearchResponse
from src.search.searxng_provider import SearXNGProvider


@pytest.mark.asyncio
async def test_searxng_provider_initialization():
    provider = SearXNGProvider(searxng_url="http://127.0.0.1:8888")
    assert provider.searxng_url == "http://127.0.0.1:8888"
    assert provider.timeout == 30.0


class TestSearchResult:
    def test_search_result_defaults(self):
        r = SearchResult(title="Test", url="https://example.com")
        assert r.title == "Test"
        assert r.url == "https://example.com"
        assert r.content == ""
        assert r.engine == ""
        assert r.score == 0.0

    def test_search_result_full(self):
        r = SearchResult(
            title="Test",
            url="https://example.com",
            content="content",
            engine="google",
            score=0.95,
        )
        assert r.score == 0.95


class TestSearchResponse:
    def test_empty_response(self):
        resp = SearchResponse(query="hello")
        assert resp.query == "hello"
        assert resp.results == []
        assert resp.unresponsive_engines == []
