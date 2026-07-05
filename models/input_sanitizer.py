"""Input sanitization pipeline — strips dangerous content before preprocessing."""

import re
import unicodedata
from typing import Any

_MAX_INPUT_LENGTH = 10000
_MAX_URL_LENGTH = 2048

_SUSPICIOUS_PATTERNS: list[re.Pattern] = [
    re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*embed\s+[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*object\s+[^>]*>.*?<\s*/\s*object\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"on\w+\s*=\s*['\"][^'\"]*['\"]", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
]

_PHONE_REGEX = re.compile(
    r"\+?\d[\d\s\-().]{6,20}\d"
)

_URL_REGEX = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+\.[^\s<>\"']{2,}"
)

_EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)


class SanitizerReport:
    """Structured report of what the sanitizer found and removed."""

    def __init__(self) -> None:
        self.original_length: int = 0
        self.final_length: int = 0
        self.suspicious_scripts_removed: int = 0
        self.urls_found: list[str] = []
        self.emails_found: list[str] = []
        self.phones_found: list[str] = []
        self.truncated: bool = False
        self.normalized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_length": self.original_length,
            "final_length": self.final_length,
            "suspicious_scripts_removed": self.suspicious_scripts_removed,
            "urls_found": self.urls_found,
            "emails_found": self.emails_found,
            "phones_found": self.phones_found,
            "truncated": self.truncated,
            "normalized": self.normalized,
        }


def sanitize(text: str, max_length: int = _MAX_INPUT_LENGTH) -> tuple[str, SanitizerReport]:
    """Clean *text* for safe downstream processing.

    Returns (cleaned_string, report).
    """
    report = SanitizerReport()
    report.original_length = len(text)

    if not text:
        return "", report

    # 1. Normalise Unicode (NFKC) to prevent homoglyph attacks.
    text = unicodedata.normalize("NFKC", text)
    report.normalized = True

    # 2. Strip null bytes and other control characters (except newline/tab).
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 3. Truncate excessive length.
    if len(text) > max_length:
        text = text[:max_length]
        report.truncated = True

    # 4. Remove HTML/script injection patterns.
    for pattern in _SUSPICIOUS_PATTERNS:
        stripped = pattern.sub("", text)
        if len(stripped) < len(text):
            report.suspicious_scripts_removed += 1
        text = stripped

    # 5. Extract URLs (for downstream analysis, not stripped).
    report.urls_found = _URL_REGEX.findall(text)

    # 6. Extract email addresses.
    report.emails_found = _EMAIL_REGEX.findall(text)

    # 7. Extract phone numbers.
    report.phones_found = _PHONE_REGEX.findall(text)

    report.final_length = len(text)
    return text.strip(), report


def is_suspicious_input(text: str) -> bool:
    """Quick pre-check — returns True if the text likely contains XSS / injection."""
    cleaned, report = sanitize(text)
    return report.suspicious_scripts_removed > 0


def detect_data_leakage(text: str) -> dict[str, list[str]]:
    """Scan for potentially sensitive data embedded in the message."""
    _, report = sanitize(text)
    return {
        "urls": report.urls_found,
        "emails": report.emails_found,
        "phones": report.phones_found,
    }
