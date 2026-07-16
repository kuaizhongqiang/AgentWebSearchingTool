# SPDX-License-Identifier: MIT
"""Search provider interface and data types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    """A single search result from any provider."""

    title: str
    url: str
    content: str = ""
    engine: str = ""
    score: float = 0.0
    category: str = "general"


@dataclass
class SearchResponse:
    """Normalized search response."""

    query: str
    results: list[SearchResult] = field(default_factory=list)
    unresponsive_engines: list[str] = field(default_factory=list)
    page: int = 1


class SearchProvider(ABC):
    """Abstract base class for search providers."""

    @abstractmethod
    async def search(
        self,
        query: str,
        num: int = 10,
        engine: str = "google",
        page: int = 1,
    ) -> SearchResponse:
        """Execute a search and return normalized results."""
        ...
