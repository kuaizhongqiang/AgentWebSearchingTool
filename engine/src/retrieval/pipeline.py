# SPDX-License-Identifier: MIT
"""Two-stage retrieval pipeline: embedding coarse filter → cross-encoder rerank."""

from __future__ import annotations

import logging
import math

from . import Document, ScoredDocument, EmbeddingProvider

logger = logging.getLogger(__name__)


class CrossEncoder:
    """Cross-encoder reranker using transformers, with optional model caching.

    Falls back to a cosine-similarity-based scorer when no model is configured.
    """

    def __init__(self, model_name: str = ""):
        self.model_name = model_name
        self._model = None
        self._tokenizer = None

    def _lazy_load(self):
        if self._model is not None:
            return
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        model_name = self.model_name or "BAAI/bge-reranker-base"
        logger.info("Loading cross-encoder model: %s", model_name)
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self._model.eval()

    def score(self, query: str, texts: list[str]) -> list[float]:
        """Score each (query, text) pair. Higher = more relevant."""
        if not self.model_name:
            return self._fallback_scores(query, texts)

        self._lazy_load()
        import torch

        pairs = [[query, text] for text in texts]
        inputs = self._tokenizer(pairs, padding=True, truncation=True, return_tensors="pt", max_length=512)
        with torch.no_grad():
            outputs = self._model(**inputs)
        scores = outputs.logits.squeeze(-1).tolist()
        return scores if isinstance(scores, list) else [scores]

    @staticmethod
    def _fallback_scores(query: str, texts: list[str]) -> list[float]:
        """Simple word-overlap similarity when no cross-encoder model is configured."""
        query_words = set(query.lower().split())
        if not query_words:
            return [0.0] * len(texts)
        scores = []
        for text in texts:
            text_words = set(text.lower().split())
            if not text_words:
                scores.append(0.0)
            else:
                jaccard = len(query_words & text_words) / len(query_words | text_words)
                scores.append(jaccard)
        return scores


class RetrievalPipeline:
    """Two-stage retrieval: embedding coarse filter → cross-encoder rerank."""

    def __init__(
        self,
        embedder: EmbeddingProvider,
        cross_encoder: CrossEncoder | None = None,
        top_k_coarse: int | None = None,
        top_k_final: int = 5,
    ):
        if top_k_coarse is None:
            top_k_coarse = top_k_final * 4  # sensible default
        self.embedder = embedder
        self.cross_encoder = cross_encoder or CrossEncoder()
        self.top_k_coarse = top_k_coarse
        self.top_k_final = top_k_final

    def run(self, query: str, documents: list[Document]) -> list[ScoredDocument]:
        """Run two-stage retrieval: coarse → rerank."""
        if not query or not documents:
            return []

        # Stage 1: Embedding-based coarse filter
        doc_texts = [d.text for d in documents]
        query_vec = self.embedder.embed([query])[0]
        doc_vecs = self.embedder.embed(doc_texts)

        # Cosine similarity
        candidates = []
        for i, doc_vec in enumerate(doc_vecs):
            sim = self._cosine_similarity(query_vec, doc_vec)
            candidates.append((i, sim))
        candidates.sort(key=lambda x: x[1], reverse=True)
        candidates = candidates[: self.top_k_coarse]

        # Stage 2: Cross-encoder rerank
        candidate_docs = [documents[i] for i, _ in candidates]
        candidate_texts = [d.text for d in candidate_docs]
        rerank_scores = self.cross_encoder.score(query, candidate_texts)

        results = [
            ScoredDocument(document=doc, score=score)
            for doc, score in zip(candidate_docs, rerank_scores)
        ]
        results.sort(key=lambda x: x.score, reverse=True)

        return results[: self.top_k_final]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
