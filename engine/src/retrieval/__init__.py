# SPDX-License-Identifier: MIT
"""Retrieval pipeline — Embedding + Cross-encoder."""

from __future__ import annotations

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
    """Embedding via Alibaba Cloud DashScope API (text-embedding-v4)."""

    def __init__(self, api_key: str = "", model: str = "text-embedding-v4"):
        self.api_key = api_key
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        import dashscope
        if self.api_key:
            dashscope.api_key = self.api_key

        results = []
        for text in texts:
            resp = dashscope.TextEmbedding.call(
                model=self.model,
                input=text,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"DashScope API error: {resp}")
            results.append(resp.output["embeddings"][0]["embedding"])
        return results


class LMStudioEmbedding(EmbeddingProvider):
    """Embedding via LM Studio (OpenAI-compatible local API)."""

    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI
        client = OpenAI(base_url=self.base_url, api_key="not-needed")
        results = []
        for text in texts:
            resp = client.embeddings.create(input=text, model=self.model or "text-embedding-ada-002")
            results.append(resp.data[0].embedding)
        return results
