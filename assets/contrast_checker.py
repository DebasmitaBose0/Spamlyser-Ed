"""
High Contrast Accessibility & WCAG Color Checker for Spamlyser UI
Provides accessibility verification utilities to ensure WCAG 2.1 AAA contrast compliance.
"""

from typing import Tuple, Dict


class ContrastChecker:
    """Calculates relative luminance and WCAG 2.1 contrast ratios for UI color hex codes."""

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    @staticmethod
    def _luminance(r: float, g: float, b: float) -> float:
        def adjust(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

    @classmethod
    def get_contrast_ratio(cls, hex1: str, hex2: str) -> float:
        """Calculates contrast ratio between two hex colors."""
        lum1 = cls._luminance(*cls._hex_to_rgb(hex1))
        lum2 = cls._luminance(*cls._hex_to_rgb(hex2))
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return round((lighter + 0.05) / (darker + 0.05), 2)

    @classmethod
    def evaluate_wcag(cls, fg_hex: str, bg_hex: str) -> Dict[str, Any]:
        """Evaluates WCAG 2.1 compliance levels (AA / AAA)."""
        ratio = cls.get_contrast_ratio(fg_hex, bg_hex)
        return {
            "ratio": ratio,
            "aa_normal": ratio >= 4.5,
            "aa_large": ratio >= 3.0,
            "aaa_normal": ratio >= 7.0,
        }
