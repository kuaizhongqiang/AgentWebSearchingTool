# SPDX-License-Identifier: MIT
"""Tests for the extract engine."""

from src.extract import ExtractEngine, ExtractedContent


class TestExtractedContent:
    def test_defaults(self):
        c = ExtractedContent()
        assert c.title == ""
        assert c.text == ""
        assert c.url == ""


class TestExtractEngine:
    def test_extract_empty_html(self):
        engine = ExtractEngine()
        result = engine.extract("", url="https://example.com")
        assert result.url == "https://example.com"

    def test_extract_simple_html(self):
        engine = ExtractEngine()
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <article>
                <h1>Hello World</h1>
                <p>This is a test paragraph.</p>
            </article>
        </body>
        </html>
        """
        result = engine.extract(html, url="https://example.com")
        # trafilatura should extract some text
        assert result.text is not None
