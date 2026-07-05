"""Tests for word_analyzer — focusing on is_spammy / is_hammy logic."""

import pytest

from models.word_analyzer import WordAnalyzer


class TestWordAnalysisFlags:
    """Verify that spam/ham classification flags are mutually consistent."""

    def setup_method(self):
        self.analyzer = WordAnalyzer()

    def test_spam_message_has_spammy_words(self):
        result = self.analyzer.analyze_text(
            "WINNER!! Free ticket! Call now! Limited offer!"
        )
        words = result.get("words", [])
        spammy = [w for w in words if w["is_spammy"]]
        assert len(spammy) > 0, "spam message should have at least one spammy word"

    def test_ham_message_has_hammy_words(self):
        result = self.analyzer.analyze_text(
            "Hey, are we still meeting for coffee tomorrow?"
        )
        words = result.get("words", [])
        hammy = [w for w in words if w["is_hammy"]]
        assert len(hammy) > 0, "ham message should have at least one hammy word"

    def test_no_word_is_both_spammy_and_hammy(self):
        result = self.analyzer.analyze_text(
            "Congratulations! You won a free prize! Click here to claim."
        )
        words = result.get("words", [])
        for w in words:
            assert not (w["is_spammy"] and w["is_hammy"]), (
                f"word '{w['word']}' cannot be both spammy and hammy"
            )

    def test_influential_word_marked(self):
        result = self.analyzer.analyze_text("FREE money now!!!")
        words = result.get("words", [])
        influential = [w for w in words if w["is_influential"]]
        assert len(influential) > 0, "urgent words should be influential"
