"""Tests for SMS encoding and character analysis."""

from models.encoding_analyzer import (
    analyze_message_complexity,
    detect_encoding_type,
    detect_suspicious_chars,
    analyze_character_categories,
)


def test_plain_ascii_message():
    result = analyze_message_complexity("Hello, this is a normal message")
    assert result["complexity_score"] == 0.0
    assert result["risk_level"] == "none"


def test_empty_message():
    result = analyze_message_complexity("")
    assert result["complexity_score"] == 0.0
    assert result["risk_level"] == "none"


def test_unicode_chars_increase_complexity():
    result = analyze_message_complexity("Café résumé ñoño")
    assert result["complexity_score"] > 0.0
    assert result["risk_level"] in ("low", "medium")


def test_emoji_detection():
    cats = analyze_character_categories("Hello 😀🎉")
    assert cats["emoji"] >= 2
    assert cats["ascii"] >= 5


def test_html_entities_detected():
    findings = detect_encoding_type("&amp;&lt;&gt;")
    types = [f["encoding"] for f in findings]
    assert "html_entities" in types


def test_percent_encoding_detected():
    findings = detect_encoding_type("%68%65%6C%6C%6F")
    types = [f["encoding"] for f in findings]
    assert "percent_encoding" in types


def test_hex_encoding_detected():
    findings = detect_encoding_type("68656c6c6f")
    types = [f["encoding"] for f in findings]
    assert "hex_encoded" in types


def test_suspicious_unicode_detection():
    findings = detect_suspicious_chars("\u200B\u200C\u200D")  # zero-width chars
    categories = [f["category"] for f in findings]
    assert "rtl_overrides" in categories


def test_character_distribution():
    cats = analyze_character_categories("ABC123")
    assert cats["ascii"] == 6
    assert cats["emoji"] == 0
    assert cats["other"] == 0


def test_mixed_script_analysis():
    cats = analyze_character_categories("Hello Привет 你好")
    assert cats["ascii"] == 5
    assert cats["cyrillic"] >= 6
    assert cats["cjk"] >= 2


def test_complexity_score_range():
    result = analyze_message_complexity(
        "Normal text with some café and résumé"
    )
    assert 0.0 <= result["complexity_score"] <= 1.0


def test_high_complexity_obfuscated_message():
    result = analyze_message_complexity(
        "%68%65%6C%6C%6F \u200B &amp; &#x48;&#x65;&#x6C;&#x6C;&#x6F;"
    )
    assert result["complexity_score"] > 0.5
