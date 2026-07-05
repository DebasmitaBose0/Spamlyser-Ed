"""Tests for EnsembleSpamClassifier dummy fallback and get_model_prediction."""

import pytest


class TestDummyEnsembleClassifier:
    def test_dummy_has_get_model_prediction(self):
        from app import EnsembleSpamClassifier, ModelPerformanceTracker

        tracker = ModelPerformanceTracker()
        classifier = EnsembleSpamClassifier(tracker)
        result = classifier.get_model_prediction("DistilBERT", "Hello world")
        assert isinstance(result, dict)
        assert "label" in result
        assert "score" in result
        assert "model" in result

    def test_dummy_get_all_predictions(self):
        from app import EnsembleSpamClassifier, ModelPerformanceTracker

        tracker = ModelPerformanceTracker()
        classifier = EnsembleSpamClassifier(tracker)
        predictions = {
            "DistilBERT": {"label": "HAM", "score": 0.9},
            "BERT": {"label": "SPAM", "score": 0.8},
        }
        results = classifier.get_all_predictions(predictions)
        assert isinstance(results, dict)
        for method in ("majority_voting", "weighted_average", "meta_ensemble"):
            assert method in results

    def test_dummy_get_ensemble_prediction(self):
        from app import EnsembleSpamClassifier, ModelPerformanceTracker

        tracker = ModelPerformanceTracker()
        classifier = EnsembleSpamClassifier(tracker)
        predictions = {
            "DistilBERT": {"label": "SPAM", "score": 0.95},
        }
        result = classifier.get_ensemble_prediction(predictions, "majority_voting")
        assert result["label"] in ("SPAM", "HAM")
