"""Unit tests for the SMS preprocessing pipeline."""

from models.smart_preprocess import preprocess_message


class TestPreprocessMessage:
    def test_normal_text(self):
        result = preprocess_message("Hello, how are you?")
        assert result["cleaned"] is not None
        assert isinstance(result["features"], dict)
        assert isinstance(result["suspicious"], dict)

    def test_spam_keywords_detected(self):
        result = preprocess_message("WINNER!! Free ticket! Call now!")
        suspicious = result["suspicious"]
        assert any(
            v for v in suspicious.values() if v
        ), "expected at least one suspicious flag"

    def test_empty_input(self):
        result = preprocess_message("")
        assert result["cleaned"] == ""

    def test_whitespace_only(self):
        result = preprocess_message("   ")
        assert result["cleaned"].strip() == ""

    def test_special_characters(self):
        result = preprocess_message("!!! *** $$$ #@!")
        assert result["cleaned"] is not None

    def test_html_tags_stripped(self):
        result = preprocess_message("<script>alert('xss')</script>")
        cleaned = result["cleaned"]
        assert "<script>" not in cleaned, "HTML tags should be removed"

    def test_urls_preserved_for_analysis(self):
        result = preprocess_message("Check http://example.com out!")
        cleaned = result["cleaned"]
        assert "http" in cleaned, "URL content should be preserved"

    def test_very_long_message(self):
        long_msg = "A" * 5000
        result = preprocess_message(long_msg)
        assert len(result["cleaned"]) <= 5000, "long messages should be truncated"

    def test_features_returned(self):
        result = preprocess_message("Normal message here")
        features = result["features"]
        assert "word_count" in features
        assert "char_count" in features
        assert "exclamation_count" in features

    def test_unicode_supported(self):
        result = preprocess_message("Café résumé ñoño 中文 日本語")
        assert result["cleaned"] is not None
