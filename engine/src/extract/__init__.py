# SPDX-License-Identifier: MIT
"""Extract engine — converts HTML to structured plain text."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExtractedContent:
    title: str = ""
    text: str = ""
    author: str = ""
    date: str = ""
    url: str = ""
    metadata: dict = field(default_factory=dict)


class ExtractEngine:
    """Content extraction using trafilatura's bare_extraction."""

    def __init__(self, max_content_length: int = 10000):
        self.max_content_length = max_content_length

    def extract(self, html: str, url: str = "") -> ExtractedContent:
        import trafilatura

        result = trafilatura.bare_extraction(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            with_metadata=True,
        )

        if result is None:
            return ExtractedContent(url=url)

        text = result.text if hasattr(result, "text") and result.text else ""
        if len(text) > self.max_content_length:
            text = text[:self.max_content_length] + "..."

        return ExtractedContent(
            title=getattr(result, "title", "") or "",
            text=text,
            author=getattr(result, "author", "") or "",
            date=getattr(result, "date", "") or "",
            url=getattr(result, "url", "") or url,
        )
