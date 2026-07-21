"""
Threat Category Confidence Threshold Configurator for Spamlyser
Allows dynamic configuration and filtering of threat categories by confidence thresholds.
"""

from typing import Dict, Any, List


class ThreatThresholdManager:
    """Manages customizable confidence thresholds for individual threat categories."""

    DEFAULT_THRESHOLDS = {
        "phishing": 0.70,
        "scam_urgent": 0.65,
        "financial_fraud": 0.75,
        "malware_link": 0.80,
    }

    def __init__(self, thresholds: Dict[str, float] = None):
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        if thresholds:
            self.thresholds.update(thresholds)

    def set_threshold(self, category: str, threshold: float) -> None:
        """Sets confidence threshold for a specific category (0.0 to 1.0)."""
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0")
        self.thresholds[category] = threshold

    def filter_threats(self, detected_threats: Dict[str, float]) -> Dict[str, float]:
        """Filters detected threats based on configured confidence thresholds."""
        filtered = {}
        for category, score in detected_threats.items():
            min_thresh = self.thresholds.get(category, 0.50)
            if score >= min_thresh:
                filtered[category] = score
        return filtered
