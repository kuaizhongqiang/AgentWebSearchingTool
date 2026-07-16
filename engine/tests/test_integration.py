# SPDX-License-Identifier: MIT
"""Integration tests — mock SearXNG + HTTP external dependencies."""

from __future__ import annotations

from unittest import mock

import pytest
from fastapi.testclient import TestClient
from src.router import app

client = TestClient(app)


# ── Health ──────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "searxng" in data
        assert "searxng_url" in data


# ── Search with mocked SearXNG HTTP ─────────────────────────────────────────

MOCK_SEARXNG_RESULTS = {
    "query": "hello",
    "results": [
        {"title": "Hello World", "url": "https://example.com", "content": "A test page", "score": 0.95, "category": "general"},
        {"title": "Hello GitHub", "url": "https://github.com", "content": "Code hosting", "score": 0.85, "category": "it"},
    ],
    "unresponsive_engines": [],
}

MOCK_SEARXNG_EMPTY = {"query": "x", "results": [], "unresponsive_engines": []}


def _patch_searxng_ready():
    """Patch SearXNGManager.is_ready property to return True."""
    return mock.patch(
        "src.searxng_runner.SearXNGManager.is_ready",
        new_callable=mock.PropertyMock(return_value=True),
    )


class TestSearchWithMock:
    def test_search_parses_mocked_results(self):
        """Mock _search_via_http to verify result parsing."""
        from src.search.searxng_provider import _search_via_http as real_http

        async def mock_http(url, timeout):
            return MOCK_SEARXNG_RESULTS

        with mock.patch("src.search.searxng_provider._search_via_http", mock_http), \
             _patch_searxng_ready():
            resp = client.post("/search", json={"query": "hello", "engine": "google"})
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["results"]) == 2
            assert data["results"][0]["title"] == "Hello World"
            assert data["results"][1]["url"] == "https://github.com"

    def test_search_handles_empty_results(self):
        async def mock_http(url, timeout):
            return MOCK_SEARXNG_EMPTY

        with mock.patch("src.search.searxng_provider._search_via_http", mock_http), \
             _patch_searxng_ready():
            resp = client.post("/search", json={"query": "x"})
            assert resp.status_code == 200
            assert resp.json()["results"] == []

    def test_search_handles_timeout(self):
        async def mock_http(url, timeout):
            raise TimeoutError("Connection timed out")

        with mock.patch("src.search.searxng_provider._search_via_http", mock_http), \
             _patch_searxng_ready():
            resp = client.post("/search", json={"query": "test"})
            assert resp.status_code == 502

    def test_search_respects_num_param(self):
        async def mock_http(url, timeout):
            return {
                "query": "test",
                "results": [{"title": f"Result {i}", "url": f"https://x.com/{i}"} for i in range(20)],
                "unresponsive_engines": [],
            }

        with mock.patch("src.search.searxng_provider._search_via_http", mock_http), \
             _patch_searxng_ready():
            resp = client.post("/search", json={"query": "test", "num": 3})
            assert resp.status_code == 200
            assert len(resp.json()["results"]) == 3


# ── Validation tests ────────────────────────────────────────────────────────

class TestSearchValidation:
    def test_search_requires_query(self):
        resp = client.post("/search", json={})
        assert resp.status_code == 422


class TestFetchValidation:
    def test_fetch_requires_url(self):
        resp = client.post("/fetch", json={})
        assert resp.status_code == 422

    def test_fetch_rejects_bad_url(self):
        resp = client.post("/fetch", json={"url": "not-a-url"})
        assert resp.status_code == 422

    def test_fetch_rejects_ftp_url(self):
        resp = client.post("/fetch", json={"url": "ftp://example.com"})
        assert resp.status_code == 422


class TestScrapeValidation:
    def test_scrape_requires_urls(self):
        resp = client.post("/scrape", json={})
        assert resp.status_code == 422

    def test_scrape_empty_list(self):
        resp = client.post("/scrape", json={"urls": []})
        assert resp.status_code == 200
        assert resp.json() == {"results": []}


# ── Data model tests ────────────────────────────────────────────────────────

class TestDataModel:
    def test_search_result_model(self):
        from dataclasses import asdict
        from src.search import SearchResult
        r = SearchResult(title="Test", url="https://example.com", engine="google", score=0.95)
        d = asdict(r)
        assert d["title"] == "Test"
        assert d["score"] == 0.95

    def test_extracted_content_model(self):
        from dataclasses import asdict
        from src.extract import ExtractedContent
        c = ExtractedContent(title="Hello", text="World")
        d = asdict(c)
        assert d["title"] == "Hello"
        assert d["text"] == "World"
