# SPDX-License-Identifier: MIT
"""Tests for the retrieval module — embedding, cross-encoder, providers."""

from __future__ import annotations

import json
from unittest import mock

import httpx
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
        scores = ce.score("python programming",
                          ["python is a programming language", "the weather is nice"])
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


# ── DashScopeEmbedding (batch via mocked API) ───────────────────────────

class TestDashScopeEmbedding:
    def _make_batch_response(self, embeddings):
        """Simulate DashScope batch response."""
        resp = mock.MagicMock()
        resp.status_code = 200
        resp.output = {"embeddings": [{"embedding": emb, "text_index": i} for i, emb in enumerate(embeddings)]}
        return resp

    def test_batch_embed_returns_all_vectors(self):
        emb = DashScopeEmbedding(api_key="test-key")
        mock_resp = self._make_batch_response([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])

        with mock.patch("dashscope.TextEmbedding.call", return_value=mock_resp) as mock_call:
            results = emb.embed(["a", "b", "c"])
            assert len(results) == 3
            assert results[0] == [0.1, 0.2]
            assert results[2] == [0.5, 0.6]
            # Verify batch call: input should be the full list
            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["input"] == ["a", "b", "c"]

    def test_single_text_returns_one_vector(self):
        emb = DashScopeEmbedding(api_key="test-key")
        mock_resp = self._make_batch_response([[0.1, 0.2]])

        with mock.patch("dashscope.TextEmbedding.call", return_value=mock_resp):
            results = emb.embed(["single"])
            assert len(results) == 1

    def test_raises_on_api_error(self):
        emb = DashScopeEmbedding(api_key="test-key")
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 400

        with mock.patch("dashscope.TextEmbedding.call", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="DashScope API error"):
                emb.embed(["test"])

    def test_stores_api_key(self):
        emb = DashScopeEmbedding(api_key="my-key", model="test-model")
        assert emb.api_key == "my-key"
        assert emb.model == "test-model"


# ── LMStudioEmbedding (batch via mocked httpx transport) ───────────────

class TestLMStudioEmbedding:
    def _mock_openai_response(self, embeddings):
        """Build a raw OpenAI API response for embedding batch."""
        data = {
            "object": "list",
            "data": [{"object": "embedding", "index": i, "embedding": emb} for i, emb in enumerate(embeddings)],
            "model": "test-model",
            "usage": {"prompt_tokens": 4, "total_tokens": 4},
        }
        return httpx.Response(200, json=data)

    def test_batch_embed_returns_all_vectors(self):
        emb = LMStudioEmbedding(base_url="http://test:1234/v1", model="test-model")
        mock_resp = self._mock_openai_response([[0.1, 0.2], [0.3, 0.4]])

        def mock_send(request, **kwargs):
            body = json.loads(request.content)
            assert body["input"] == ["a", "b"]
            assert body["model"] == "test-model"
            return mock_resp

        transport = httpx.MockTransport(mock_send)
        http_client = httpx.Client(transport=transport)
        # Patch the OpenAI constructor to inject our mock http_client
        original_init = __import__("openai").OpenAI.__init__
        def patched_init(self, **kwargs):
            kwargs["http_client"] = http_client
            original_init(self, **kwargs)

        with mock.patch("openai.OpenAI.__init__", patched_init):
            results = emb.embed(["a", "b"])
            assert len(results) == 2
            assert results[1] == [0.3, 0.4]

    def test_single_text_returns_one_vector(self):
        emb = LMStudioEmbedding(base_url="http://test:1234/v1", model="test-model")
        mock_resp = self._mock_openai_response([[0.5]])

        transport = httpx.MockTransport(lambda r, **kw: mock_resp)
        http_client = httpx.Client(transport=transport)
        original_init = __import__("openai").OpenAI.__init__
        def patched_init(self, **kwargs):
            kwargs["http_client"] = http_client
            original_init(self, **kwargs)

        with mock.patch("openai.OpenAI.__init__", patched_init):
            results = emb.embed(["x"])
            assert len(results) == 1

    def test_raises_on_connection_error(self):
        emb = LMStudioEmbedding(base_url="http://unreachable:1234/v1", model="test-model")

        with pytest.raises(Exception):
            emb.embed(["test"])

    def test_fallback_model(self):
        emb = LMStudioEmbedding(base_url="http://test:1234/v1", model="")
        assert emb.model == "text-embedding-ada-002"


# ── /filter endpoint ───────────────────────────────────────────────────

class FakePipeline:
    top_k_final: int = 5
    def run(self, query, documents):
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

    def test_filter_custom_top_k(self):
        with mock.patch("src.router._get_retrieval_pipeline", return_value=FakePipeline()):
            resp = client.post("/filter", json={"query": "python", "documents": ["a", "b"], "top_k": 1})
            assert resp.status_code == 200
