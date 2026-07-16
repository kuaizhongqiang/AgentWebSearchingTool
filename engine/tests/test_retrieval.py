# SPDX-License-Identifier: MIT
"""Tests for the retrieval module — embedding and cross-encoder."""

from __future__ import annotations

from unittest import mock

import pytest
from fastapi.testclient import TestClient
from src.router import app
from src.retrieval import Document, ScoredDocument
from src.retrieval.pipeline import CrossEncoder, RetrievalPipeline

client = TestClient(app)


# ── Cross-encoder ───────────────────────────────────────────────────────

class TestCrossEncoder:
    def test_fallback_scores_higher_for_similar_texts(self):
        ce = CrossEncoder(model_name="")
        scores = ce.score("python programming", ["python is a programming language", "the weather is nice"])
        assert scores[0] > scores[1]

    def test_fallback_empty_texts(self):
        ce = CrossEncoder(model_name="")
        scores = ce.score("test", ["", "hello world"])
        assert scores[0] == 0.0

    def test_fallback_empty_query(self):
        ce = CrossEncoder(model_name="")
        scores = ce.score("", ["some text", "more text"])
        assert scores == [0.0, 0.0]

    def test_fallback_all_match(self):
        ce = CrossEncoder(model_name="")
        scores = ce.score("hello world", ["hello world foo", "goodbye world"])
        assert scores[0] > scores[1]


# ── Cosine similarity ───────────────────────────────────────────────────

class TestCosineSimilarity:
    def test_identical_vectors(self):
        sim = RetrievalPipeline._cosine_similarity([1, 0, 0], [1, 0, 0])
        assert abs(sim - 1.0) < 0.001

    def test_opposite_vectors(self):
        sim = RetrievalPipeline._cosine_similarity([1, 0], [-1, 0])
        assert abs(sim - (-1.0)) < 0.001

    def test_orthogonal_vectors(self):
        sim = RetrievalPipeline._cosine_similarity([1, 0], [0, 1])
        assert abs(sim) < 0.001

    def test_zero_vector(self):
        sim = RetrievalPipeline._cosine_similarity([0, 0], [1, 0])
        assert sim == 0.0


# ── RetrievalPipeline ───────────────────────────────────────────────────

class FakeEmbedder:
    """Deterministic fake embedder for testing."""
    def embed(self, texts):
        # Return one-hot-like vectors: text index determines which dimension is 1
        return [[1.0 if i == hash(t) % 10 else 0.0 for i in range(10)] for t in texts]


class TestRetrievalPipeline:
    def test_empty_query_returns_empty(self):
        pipeline = RetrievalPipeline(embedder=FakeEmbedder())
        assert pipeline.run("", [Document(text="hello")]) == []

    def test_empty_docs_returns_empty(self):
        pipeline = RetrievalPipeline(embedder=FakeEmbedder())
        assert pipeline.run("query", []) == []

    def test_coarse_filter_keeps_top_k(self):
        pipeline = RetrievalPipeline(embedder=FakeEmbedder(), top_k_coarse=3, top_k_final=2)
        docs = [Document(text=f"doc {i}") for i in range(10)]
        results = pipeline.run("test query", docs)
        assert len(results) <= 2

    def test_pipeline_returns_scored_documents(self):
        pipeline = RetrievalPipeline(embedder=FakeEmbedder(), top_k_coarse=5, top_k_final=3)
        docs = [Document(text=f"document number {i} about programming") for i in range(5)]
        results = pipeline.run("programming", docs)
        assert all(isinstance(r, ScoredDocument) for r in results)
        assert all(r.score >= 0 for r in results)


# ── /filter endpoint (with mocked pipeline) ─────────────────────────────

class FakePipeline:
    top_k_final: int = 5
    def run(self, query: str, documents: list[Document]) -> list[ScoredDocument]:
        return [ScoredDocument(document=doc, score=1.0 - i * 0.1) for i, doc in enumerate(documents[:self.top_k_final])]


class TestFilterEndpoint:
    def test_filter_requires_query(self):
        resp = client.post("/filter", json={})
        assert resp.status_code == 422

    def test_filter_requires_documents(self):
        resp = client.post("/filter", json={"query": "hello"})
        assert resp.status_code == 422

    def test_filter_accepts_valid_request(self):
        with mock.patch("src.router._get_retrieval_pipeline", return_value=FakePipeline()):
            resp = client.post("/filter", json={"query": "test", "documents": ["hello world"]})
            assert resp.status_code == 200
            data = resp.json()
            assert "results" in data
            assert data["query"] == "test"

    def test_filter_default_top_k(self):
        with mock.patch("src.router._get_retrieval_pipeline", return_value=FakePipeline()):
            resp = client.post("/filter", json={"query": "python", "documents": ["a", "b", "c", "d", "e", "f"]})
            assert resp.status_code == 200

    def test_filter_custom_top_k(self):
        with mock.patch("src.router._get_retrieval_pipeline", return_value=FakePipeline()):
            resp = client.post("/filter", json={"query": "python", "documents": ["a", "b"], "top_k": 1})
            assert resp.status_code == 200
