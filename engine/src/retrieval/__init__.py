# SPDX-License-Identifier: MIT
"""Retrieval pipeline — Embedding + Cross-encoder."""

from __future__ import annotations

import functools
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Document:
    text: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class ScoredDocument:
    document: Document
    score: float = 0.0


class EmbeddingProvider(ABC):
    """Abstract base class for text embedding providers."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class DashScopeEmbedding(EmbeddingProvider):
    """Embedding via Alibaba Cloud DashScope API with LRU cache and batching."""

    def __init__(self, api_key: str = "", model: str = "text-embedding-v4"):
        self.api_key = api_key
        self.model = model

    @functools.lru_cache(maxsize=512)
    def _embed_single(self, text: str) -> tuple[float, ...]:
        import dashscope

        if self.api_key:
            dashscope.api_key = self.api_key
        try:
            resp = dashscope.TextEmbedding.call(model=self.model, input=text)
            if resp.status_code != 200:
                raise RuntimeError(f"DashScope API error (status={resp.status_code}): {resp}")
            emb = resp.output["embeddings"][0]["embedding"]
            return tuple(emb)
        except Exception as e:
            logger.error("DashScope embed failed for text (len=%d): %s", len(text), e)
            raise

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(self._embed_single(t)) for t in texts]


class LMStudioEmbedding(EmbeddingProvider):
    """Embedding via LM Studio (OpenAI-compatible API) with LRU cache and batching."""

    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model or "text-embedding-ada-002"

    @functools.lru_cache(maxsize=512)
    def _embed_single(self, text: str) -> tuple[float, ...]:
        from openai import OpenAI

        try:
            client = OpenAI(base_url=self.base_url, api_key="not-needed", max_retries=0)
            resp = client.embeddings.create(
                input=text,
                model=self.model,
                timeout=30,
            )
            return tuple(resp.data[0].embedding)
        except Exception as e:
            logger.error("LM Studio embed failed for text (len=%d): %s", len(text), e)
            raise

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(self._embed_single(t)) for t in texts]
