"""Tests for XSS prevention in word_analyzer HTML rendering."""

import pytest

from models.word_analyzer import WordAnalyzer


class TestXssPrevention:
    """User-supplied message text must be HTML-escaped before rendering."""

    def setup_method(self):
        self.analyzer = WordAnalyzer()

    def test_script_tag_not_executed(self):
        result = self.analyzer.analyze_text("<script>alert('xss')</script>")
        html = self.analyzer.create_highlighted_html(result)
        assert "&lt;script&gt;" in html or "script" not in html.lower().replace("&lt;", ""), (
            "raw <script> must not appear in output"
        )

    def test_html_entities_escaped(self):
        result = self.analyzer.analyze_text("<b>bold</b> & <i>italic</i>")
        html = self.analyzer.create_highlighted_html(result)
        assert "&lt;b&gt;" in html or "&amp;" in html

    def test_normal_text_renders_correctly(self):
        result = self.analyzer.analyze_text("Hello world")
        html = self.analyzer.create_highlighted_html(result)
        assert "Hello" in html or "hello" in html.lower()

    def test_tooltip_escaped(self):
        result = self.analyzer.analyze_text('test"onmouseover="evil')
        html = self.analyzer.create_highlighted_html(result)
        assert "&quot;" in html or "evil" not in html
