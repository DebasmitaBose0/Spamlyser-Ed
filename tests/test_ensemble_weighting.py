"""Tests for ensemble classifier — confidence weighting and agreement penalty."""

import pytest


class TestConfidenceWeighting:
    def test_get_majority_label_spam_wins(self):
        from models.ensemble_classifier_method import EnsembleSpamClassifier

        classifier = EnsembleSpamClassifier(performance_tracker=None)
        predictions = {
            "model_a": {"label": "SPAM", "score": 0.9},
            "model_b": {"label": "SPAM", "score": 0.8},
            "model_c": {"label": "HAM", "score": 0.7},
        }
        result = classifier.confidence_weighted_voting(predictions)
        assert result["label"] == "SPAM"

    def test_confidently_wrong_model_penalised(self):
        from models.ensemble_classifier_method import EnsembleSpamClassifier

        classifier = EnsembleSpamClassifier(performance_tracker=None)
        # Two models agree on SPAM, one confidently disagrees with HAM
        predictions = {
            "model_a": {"label": "SPAM", "score": 0.9},
            "model_b": {"label": "SPAM", "score": 0.8},
            "model_c": {"label": "HAM", "score": 0.95},
        }
        result = classifier.confidence_weighted_voting(predictions)
        votes = {v["model"]: v for v in result.get("model_votes", [])}
        # model_c's adjusted weight should be penalised by agreement_penalty
        assert votes["model_c"]["weight_contribution_ham"] < 0.95, (
            "confidently wrong model should have reduced weight"
        )

    def test_majority_voting(self):
        from models.ensemble_classifier_method import EnsembleSpamClassifier

        classifier = EnsembleSpamClassifier(performance_tracker=None)
        predictions = {
            "a": {"label": "SPAM", "score": 0.9},
            "b": {"label": "HAM", "score": 0.8},
        }
        result = classifier.majority_voting(predictions)
        assert "label" in result
