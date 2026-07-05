"""Unit tests for the ensemble classification pipeline and label normalisation."""

import json
import os

from models.label_normalizer import normalize_label


class TestLabelNormalizer:
    def test_spam_labels(self):
        assert normalize_label("SPAM", 0.95) == "SPAM"
        assert normalize_label("spam", 0.95) == "SPAM"
        assert normalize_label("LABEL_1", 0.95) == "SPAM"
        assert normalize_label("LABEL_0", 0.05) == "HAM"

    def test_ham_labels(self):
        assert normalize_label("HAM", 0.05) == "HAM"
        assert normalize_label("ham", 0.05) == "HAM"
        assert normalize_label("not_spam", 0.05) == "HAM"
        assert normalize_label("LABEL_0", 0.95) == "HAM"

    def test_confidence_threshold(self):
        assert normalize_label("SPAM", 0.95) == "SPAM"
        assert normalize_label("SPAM", 0.51) == "SPAM"
        assert normalize_label("HAM", 0.95) == "HAM"

    def test_mixed_case(self):
        assert normalize_label("SpAm", 0.95) == "SPAM"
        assert normalize_label("Ham", 0.05) == "HAM"
        assert normalize_label("Label_1", 0.90) == "SPAM"

    def test_edge_case_empty_label(self):
        result = normalize_label("", 0.5)
        assert result in ("SPAM", "HAM")

    def test_unknown_label_default(self):
        result = normalize_label("SOME_RANDOM_LABEL", 0.8)
        assert result == "SPAM", "unknown labels with high confidence should default to SPAM"


class TestSpamKeywords:
    def test_keywords_list_not_empty(self):
        from models.simple_explainer import SPAM_KEYWORDS

        assert len(SPAM_KEYWORDS) > 0, "spam keywords list should not be empty"

    def test_common_spam_terms_present(self):
        from models.simple_explainer import SPAM_KEYWORDS

        common = ["win", "free", "urgent", "click", "congrat"]
        found = [kw for kw in common if kw in SPAM_KEYWORDS]
        assert len(found) > 0, f"expected common spam terms in list, found {found}"
