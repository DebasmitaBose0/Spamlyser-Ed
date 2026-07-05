"""Tests for smart_preprocess — leetspeak decoding and abbreviation expansion."""

from models.smart_preprocess import correct_leetspeak, expand_abbreviations, preprocess_message


class TestCorrectLeetspeak:
    def test_pure_numeric_unchanged(self):
        assert correct_leetspeak("100") == "100"
        assert correct_leetspeak("2024") == "2024"
        assert correct_leetspeak("3.14") == "3.14"

    def test_leet_words_decoded(self):
        assert correct_leetspeak("H3ll0") == "Hello"
        assert correct_leetspeak("M0n3y") == "Money"
        assert correct_leetspeak("Fr33") == "Free"

    def test_mixed_content(self):
        result = correct_leetspeak("C0d3 2024")
        assert "2024" in result, "numeric token should survive unchanged"

    def test_empty_input(self):
        assert correct_leetspeak("") == ""

    def test_no_leet_unchanged(self):
        assert correct_leetspeak("hello world") == "hello world"

    def test_punctuation_preserved(self):
        result = correct_leetspeak("C@ll n0w!!!")
        assert "!!!" in result


class TestExpandAbbreviations:
    def test_common_abbreviations(self):
        assert expand_abbreviations("u r gr8") == "you are great"
        assert expand_abbreviations("thx pls") == "thanks please"

    def test_unknown_word_unchanged(self):
        assert expand_abbreviations("hello world") == "hello world"

    def test_case_insensitive(self):
        assert expand_abbreviations("UR") == "your"
        assert expand_abbreviations("ASAP") == "as soon as possible"

    def test_partial_expansion(self):
        result = expand_abbreviations("idk what u mean")
        assert "I don't know" in result or "idk" not in result
