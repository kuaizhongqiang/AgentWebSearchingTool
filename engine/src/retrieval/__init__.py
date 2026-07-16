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
    """Embedding via Alibaba Cloud DashScope API with batch support and LRU cache."""

    def __init__(self, api_key: str = "", model: str = "text-embedding-v4"):
        self.api_key = api_key
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        import dashscope

        if self.api_key:
            dashscope.api_key = self.api_key

        # Batch call: DashScope API accepts input as a single string or list
        try:
            resp = dashscope.TextEmbedding.call(model=self.model, input=texts)
            if resp.status_code != 200:
                raise RuntimeError(f"DashScope API error (status={resp.status_code}): {resp}")
            # Response order matches input order
            return [item["embedding"] for item in resp.output["embeddings"]]
        except Exception as e:
            logger.error("DashScope batch embed failed (%d texts): %s", len(texts), e)
            raise


class LMStudioEmbedding(EmbeddingProvider):
    """Embedding via LM Studio (OpenAI-compatible API) with batch."""

    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model or "text-embedding-ada-002"

    def embed(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI

        try:
            client = OpenAI(base_url=self.base_url, api_key="not-needed", max_retries=0)
            # Batch call: OpenAI API accepts input as a list of strings
            resp = client.embeddings.create(input=texts, model=self.model, timeout=60)
            # Sort by index to preserve input order
            sorted_data = sorted(resp.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
        except Exception as e:
            logger.error("LM Studio batch embed failed (%d texts): %s", len(texts), e)
            raise
