# SPDX-License-Identifier: MIT
"""Extract engine — converts HTML to structured plain text."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExtractedContent:
    """Structured content extracted from HTML."""

    title: str = ""
    text: str = ""
    author: str = ""
    date: str = ""
    url: str = ""
    metadata: dict = field(default_factory=dict)


class ExtractEngine:
    """Content extraction using trafilatura.

    Extracts main article content, title, author, and date from HTML pages.
    """

    def __init__(self, max_content_length: int = 10000):
        self.max_content_length = max_content_length

    def extract(self, html: str, url: str = "") -> ExtractedContent:
        """Extract structured content from HTML."""
        import trafilatura

        result = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            output_format="txt",
            with_metadata=True,
        )

        if result is None:
            return ExtractedContent(url=url)

        text = result.text if hasattr(result, "text") else str(result)
        if len(text) > self.max_content_length:
            text = text[: self.max_content_length] + "..."

        return ExtractedContent(
            title=getattr(result, "title", ""),
            text=text,
            author=getattr(result, "author", ""),
            date=getattr(result, "date", ""),
            url=url,
        )
