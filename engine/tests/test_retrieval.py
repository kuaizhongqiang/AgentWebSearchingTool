# SPDX-License-Identifier: MIT
"""Tests for the retrieval module — embedding, cross-encoder, providers."""

from __future__ import annotations

from unittest import mock

import pytest
from fastapi.testclient import TestClient
from src.router import app
from src.retrieval import Document, ScoredDocument, DashScopeEmbedding, LMStudioEmbedding
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
    def embed(self, texts):
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

    def test_top_k_coarse_default_when_none(self):
        pipeline = RetrievalPipeline(embedder=FakeEmbedder(), top_k_coarse=None, top_k_final=3)
        assert pipeline.top_k_coarse == 12  # 3 * 4


# ── DashScopeEmbedding (mocked) ─────────────────────────────────────────

class TestDashScopeEmbedding:
    def _make_mock_response(self, embedding, status_code=200):
        """Create a mock DashScope API response object."""
        resp = mock.MagicMock()
        resp.status_code = status_code
        resp.output = {"embeddings": [{"embedding": embedding}]}
        return resp

    def test_embed_calls_dashscope_api(self):
        emb = DashScopeEmbedding(api_key="test-key", model="text-embedding-v4")
        mock_resp = self._make_mock_response([0.1, 0.2, 0.3])

        with mock.patch("dashscope.TextEmbedding.call", return_value=mock_resp):
            result = emb.embed(["hello world"])
            assert len(result) == 1
            assert result[0] == [0.1, 0.2, 0.3]

    def test_embed_raises_on_api_error(self):
        emb = DashScopeEmbedding(api_key="test-key")
        mock_resp = self._make_mock_response([], status_code=400)

        with mock.patch("dashscope.TextEmbedding.call", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="DashScope API error"):
                emb.embed(["test"])

    def test_embed_clears_cache_on_diff_args(self):
        """Different texts should produce different cache entries."""
        emb = DashScopeEmbedding(api_key="test-key")
        call_count = 0

        def mock_call(**kwargs):
            nonlocal call_count
            call_count += 1
            return self._make_mock_response([0.5, 0.5])

        with mock.patch("dashscope.TextEmbedding.call", side_effect=mock_call):
            emb.embed(["text a"])
            emb.embed(["text a"])   # cached
            emb.embed(["text b"])   # new
            assert call_count == 2  # only 2 unique texts called


# ── LMStudioEmbedding (mocked) ──────────────────────────────────────────

class TestLMStudioEmbedding:
    def test_embed_calls_openai_api(self):
        emb = LMStudioEmbedding(base_url="http://localhost:1234/v1", model="test-model")
        mock_data = mock.MagicMock()
        mock_data.data = [mock.MagicMock()]
        mock_data.data[0].embedding = [0.1, 0.2, 0.3]

        with mock.patch("openai.OpenAI") as MockOpenAI:
            mock_client = MockOpenAI.return_value
            mock_client.embeddings.create.return_value = mock_data
            result = emb.embed(["hello"])
            assert result[0] == [0.1, 0.2, 0.3]
            mock_client.embeddings.create.assert_called_once()

    def test_embed_fallback_model(self):
        """When model is empty, should default to text-embedding-ada-002."""
        emb = LMStudioEmbedding(base_url="http://localhost:1234/v1", model="")
        assert emb.model == "text-embedding-ada-002"


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

    def test_filter_custom_top_k(self):
        with mock.patch("src.router._get_retrieval_pipeline", return_value=FakePipeline()):
            resp = client.post("/filter", json={"query": "python", "documents": ["a", "b"], "top_k": 1})
            assert resp.status_code == 200
