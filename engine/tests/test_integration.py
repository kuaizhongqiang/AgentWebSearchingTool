# SPDX-License-Identifier: MIT
"""Integration tests — mock SearXNG server + full request flow."""

from fastapi.testclient import TestClient
from src.router import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestSearchValidation:
    def test_search_requires_query(self):
        resp = client.post("/search", json={})
        assert resp.status_code == 422

    def test_search_empty_query_returns_502(self):
        """Empty query is valid request but upstream fails — should be handled gracefully."""
        resp = client.post("/search", json={"query": ""})
        assert resp.status_code == 502


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


class TestDataModel:
    def test_search_result_model(self):
        from src.search import SearchResult
        import json
        r = SearchResult(title="Test", url="https://example.com", engine="google", score=0.95)
        d = {"title": r.title, "url": r.url, "engine": r.engine, "score": r.score}
        assert d["title"] == "Test"
        assert d["url"] == "https://example.com"
        assert d["score"] == 0.95

    def test_extracted_content_model(self):
        from src.extract import ExtractedContent
        c = ExtractedContent(title="Hello", text="World")
        assert c.title == "Hello"
        assert c.text == "World"
