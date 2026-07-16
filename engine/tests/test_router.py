# SPDX-License-Identifier: MIT
"""Tests for the FastAPI router."""

from fastapi.testclient import TestClient
from src.router import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "searxng" in data
        assert "searxng_url" in data


class TestSearch:
    def test_search_requires_query(self):
        resp = client.post("/search", json={})
        assert resp.status_code == 422  # Validation error


class TestFetch:
    def test_fetch_requires_url(self):
        resp = client.post("/fetch", json={})
        assert resp.status_code == 422

    def test_fetch_bad_url(self):
        resp = client.post("/fetch", json={"url": "not-a-url"})
        assert resp.status_code == 422


class TestScrape:
    def test_scrape_requires_urls(self):
        resp = client.post("/scrape", json={})
        assert resp.status_code == 422
