"""SMS message encoding and character analysis utilities.

Detects encoding types, character sets, special characters, and potential
encoding-based obfuscation techniques used in spam messages.
"""

import re
from collections import Counter
from typing import Any


ENCODING_PATTERNS: dict[str, str] = {
    "base64": r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$",
    "hex_encoded": r"^(?:[0-9a-fA-F]{2}\s?)+$",
    "unicode_escape": r"\\u[0-9a-fA-F]{4}",
    "html_entities": r"&[#a-zA-Z0-9]+;",
    "percent_encoding": r"%[0-9a-fA-F]{2}",
    "punycode": r"xn--[a-zA-Z0-9]+",
}

SUSPICIOUS_UNICODE_CATEGORIES: dict[str, list[tuple[int, int]]] = {
    "confusables": [
        (0x00A0, 0x00A0),
        (0x2000, 0x206F),
        (0xFE00, 0xFE0F),
        (0xFF00, 0xFFEF),
    ],
    "rtl_overrides": [
        (0x200E, 0x200F),
        (0x202A, 0x202E),
        (0x2066, 0x2069),
    ],
    "homoglyphs": [
        (0x0391, 0x03A9),
        (0x0430, 0x044F),
        (0x0500, 0x052F),
    ],
}


def detect_encoding_type(text: str) -> list[dict[str, Any]]:
    """Detect encoding/obfuscation techniques used in the message."""
    findings: list[dict[str, Any]] = []
    for encoding_name, pattern in ENCODING_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            findings.append({
                "encoding": encoding_name,
                "matches": len(matches),
                "sample": matches[0][:50] if matches else "",
            })
    return findings


def analyze_character_categories(text: str) -> dict[str, int]:
    """Count characters by Unicode category."""
    categories: dict[str, int] = {
        "ascii": 0,
        "latin_extended": 0,
        "cyrillic": 0,
        "greek": 0,
        "cjk": 0,
        "emoji": 0,
        "math_symbols": 0,
        "other": 0,
    }
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251]"
    )
    for char in text:
        code = ord(char)
        if char.isascii():
            categories["ascii"] += 1
        elif emoji_pattern.match(char):
            categories["emoji"] += 1
        elif 0x00C0 <= code <= 0x024F:
            categories["latin_extended"] += 1
        elif 0x0400 <= code <= 0x04FF:
            categories["cyrillic"] += 1
        elif 0x0370 <= code <= 0x03FF:
            categories["greek"] += 1
        elif 0x4E00 <= code <= 0x9FFF or 0x3040 <= code <= 0x309F:
            categories["cjk"] += 1
        elif 0x2200 <= code <= 0x27FF:
            categories["math_symbols"] += 1
        else:
            categories["other"] += 1
    return categories


def detect_suspicious_chars(text: str) -> list[dict[str, Any]]:
    """Detect suspicious Unicode characters used for obfuscation."""
    findings: list[dict[str, Any]] = []
    for category, ranges in SUSPICIOUS_UNICODE_CATEGORIES.items():
        matched_chars: list[str] = []
        for char in text:
            code = ord(char)
            for start, end in ranges:
                if start <= code <= end:
                    matched_chars.append(f"U+{code:04X}")
                    break
        if matched_chars:
            findings.append({
                "category": category,
                "count": len(matched_chars),
                "characters": matched_chars[:10],
            })
    return findings


def analyze_message_complexity(text: str) -> dict[str, Any]:
    """Calculate overall message complexity and encoding risk score."""
    total_chars = len(text)
    if total_chars == 0:
        return {"complexity_score": 0.0, "risk_level": "none", "details": {}}

    encodings = detect_encoding_type(text)
    char_categories = analyze_character_categories(text)
    suspicious = detect_suspicious_chars(text)

    non_ascii = total_chars - char_categories.get("ascii", 0)
    ascii_ratio = char_categories.get("ascii", 0) / total_chars
    encoding_count = len(encodings)
    suspicious_count = sum(s["count"] for s in suspicious)

    complexity = 0.0
    if ascii_ratio < 0.8:
        complexity += 0.3
    if encoding_count > 0:
        complexity += 0.2 * min(encoding_count, 3)
    if suspicious_count > 0:
        complexity += 0.3 * min(suspicious_count / 5, 1)
    if non_ascii > 10:
        complexity += 0.2

    complexity = min(complexity, 1.0)

    if complexity > 0.7:
        risk_level = "high"
    elif complexity > 0.4:
        risk_level = "medium"
    elif complexity > 0.1:
        risk_level = "low"
    else:
        risk_level = "none"

    return {
        "complexity_score": round(complexity, 3),
        "risk_level": risk_level,
        "details": {
            "total_chars": total_chars,
            "non_ascii_chars": non_ascii,
            "ascii_ratio": round(ascii_ratio, 3),
            "encoding_techniques": encoding_count,
            "suspicious_unicode_spans": suspicious_count,
            "encodings_found": [e["encoding"] for e in encodings],
            "suspicious_categories": [s["category"] for s in suspicious],
            "char_distribution": char_categories,
        },
    }
