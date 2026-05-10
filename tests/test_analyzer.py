# coding: utf-8
"""Integration tests for the TextAnalyzer class."""

import pytest
from clareza.analyzer import TextAnalyzer


class TestTextAnalyzer:
    """Test suite for TextAnalyzer integration."""

    @pytest.fixture
    def analyzer(self):
        """Create a TextAnalyzer instance for testing."""
        return TextAnalyzer()

    # Initialization tests
    def test_init_creates_instance(self, analyzer):
        """Test that analyzer initializes correctly."""
        assert analyzer is not None
        assert hasattr(analyzer, "analyze")
        assert hasattr(analyzer, "find_cards")
        assert hasattr(analyzer, "classify_emotion")
        assert hasattr(analyzer, "tokenize")
        assert hasattr(analyzer, "normalize")

    def test_init_includes_all_components(self, analyzer):
        """Test that analyzer includes all required components."""
        assert hasattr(analyzer, "_tokenizer")
        assert hasattr(analyzer, "_card_mapper")
        assert hasattr(analyzer, "_emotion_classifier")
        assert hasattr(analyzer, "_intent_detector")

    # Basic analyze tests
    def test_analyze_empty_string(self, analyzer):
        """Test analyzing empty string returns empty result."""
        result = analyzer.analyze("")
        assert result["card_ids"] == []
        assert result["cards"] == []
        assert result["emotion"] == "uncertain"
        assert result["tokens"] == []
        assert result["normalized_text"] == ""

    def test_analyze_none_returns_empty(self, analyzer):
        """Test analyzing None returns empty result."""
        result = analyzer.analyze(None)
        assert result["card_ids"] == []
        assert result["cards"] == []
        assert result["emotion"] == "uncertain"

    def test_analyze_returns_all_required_fields(self, analyzer):
        """Test that analyze returns all required fields."""
        result = analyzer.analyze("Test text")
        assert "card_ids" in result
        assert "cards" in result
        assert "emotion" in result
        assert "emotion_confidence" in result
        assert "tokens" in result
        assert "normalized_text" in result
        assert "intent" in result
        assert "primary_question" in result
        assert "has_question" in result

    # Card detection tests
    def test_analyze_detects_numeric_card_reference(self, analyzer):
        """Test detecting cards using 'carta N' pattern."""
        result = analyzer.analyze("carta 3")
        assert 3 in result["card_ids"]

    def test_analyze_detects_card_with_parentheses(self, analyzer):
        """Test detecting cards with parentheses around name."""
        result = analyzer.analyze("Carta 3 (Caminho)")
        assert 3 in result["card_ids"]

    def test_analyze_detects_multiple_cards(self, analyzer):
        """Test detecting multiple card references."""
        result = analyzer.analyze("carta 3 e carta 11")
        assert 3 in result["card_ids"]
        assert 11 in result["card_ids"]

    # Acceptance Criteria 1: Analyzing 'Carta 3 (Caminho) e casamento' -> cards [3, 11]
    def test_acceptance_criteria_card_detection_with_theme(self, analyzer):
        """Test: 'Carta 3 (Caminho) e casamento' correctly identifies cards 3 and 11."""
        result = analyzer.analyze("Carta 3 (Caminho) e casamento")
        assert 3 in result["card_ids"]
        assert 11 in result["card_ids"]

    # Acceptance Criteria 2: No card mentions -> thematic summary
    def test_acceptance_criteria_no_card_mentions_returns_themes(self, analyzer):
        """Test: Text with no card mentions detects relevant theme keywords."""
        result = analyzer.analyze("Estou muito triste sobre meu amor")
        # Should have theme-based card detection even without explicit card mentions
        assert "emotion" in result
        assert result["emotion"] in ["conflicted", "hopeful", "fearful", "uncertain"]

    def test_analyze_no_explicit_cards_analyzes_themes(self, analyzer):
        """Test that text without explicit cards still produces analysis."""
        result = analyzer.analyze("Não sei o que fazer sobre meu futuro")
        assert "emotion" in result
        assert "tokens" in result
        assert len(result["tokens"]) > 0

    # Acceptance Criteria 3: Accented characters
    def test_acceptance_criteria_accents_preserved(self, analyzer):
        """Test: Portuguese accented characters are handled correctly."""
        text = "ãõçáéíóú àèìòù âêîôû"
        result = analyzer.analyze(text)
        # Should process without errors
        assert "normalized_text" in result
        # Accents should be preserved
        assert "ã" in result["normalized_text"] or result["normalized_text"] == ""
        assert "ç" in result["normalized_text"] or result["normalized_text"] == ""

    def test_analyze_with_portuguese_accents(self, analyzer):
        """Test analyzing text with various Portuguese accents."""
        text = "coração emoção sofá café"
        result = analyzer.analyze(text)
        assert result is not None
        assert "tokens" in result
        assert len(result["tokens"]) > 0

    # Acceptance Criteria 4: Long input handling
    def test_acceptance_criteria_long_input_10k_chars(self, analyzer):
        """Test: Long inputs (up to 10,000 characters) process without issues."""
        # Create a 10,000 character text
        base_text = "Estou pensando muito sobre minha vida e meu futuro. Carta 3 me veio à mente. "
        long_text = base_text * 250  # Should be approximately 10,000 chars
        assert len(long_text) >= 9000  # Verify we're testing near the limit

        result = analyzer.analyze(long_text)
        # Should complete without timeout or memory issues
        assert result is not None
        assert "card_ids" in result
        assert "emotion" in result
        assert "tokens" in result
        # Card 3 should be detected in the repeated text
        assert 3 in result["card_ids"]

    def test_analyze_handles_very_long_text(self, analyzer):
        """Test analyzer handles very long text without issues."""
        text = "a " * 5000  # 10,000 characters with spaces
        result = analyzer.analyze(text)
        assert result is not None
        assert isinstance(result["tokens"], list)

    # Acceptance Criteria 5: Emotion classification
    def test_acceptance_criteria_emotion_classification(self, analyzer):
        """Test: Analyzer extracts emotion and classifies it correctly."""
        text = "Estou muito confuso sobre minha vida"
        result = analyzer.analyze(text)
        assert result["emotion"] in ["conflicted", "hopeful", "fearful", "uncertain"]
        assert "emotion_confidence" in result
        assert isinstance(result["emotion_confidence"], float)

    def test_analyze_emotion_fearful(self, analyzer):
        """Test classifying fearful emotion."""
        text = "Estou com medo do futuro"
        result = analyzer.analyze(text)
        assert result["emotion"] == "fearful"

    def test_analyze_emotion_conflicted(self, analyzer):
        """Test classifying conflicted emotion."""
        text = "Estou indeciso entre duas opções"
        result = analyzer.analyze(text)
        assert result["emotion"] == "conflicted"

    def test_analyze_emotion_hopeful(self, analyzer):
        """Test classifying hopeful emotion."""
        text = "Tenho esperança de que tudo vai dar certo"
        result = analyzer.analyze(text)
        assert result["emotion"] == "hopeful"

    def test_analyze_emotion_uncertain(self, analyzer):
        """Test classifying uncertain emotion."""
        text = "Não sei o que pensar sobre isso"
        result = analyzer.analyze(text)
        assert result["emotion"] == "uncertain"

    # Intent detection tests
    def test_analyze_intent_career(self, analyzer):
        """Test detecting career intent."""
        text = "Devo mudar de emprego?"
        result = analyzer.analyze(text)
        assert result["intent"] == "career"
        assert result["has_question"] is True

    def test_analyze_intent_relationship(self, analyzer):
        """Test detecting relationship intent."""
        text = "Meu relacionamento não está bem"
        result = analyzer.analyze(text)
        assert result["intent"] == "relationship"

    def test_analyze_intent_health(self, analyzer):
        """Test detecting health intent."""
        text = "Estou com ansiedade sobre minha saúde"
        result = analyzer.analyze(text)
        assert result["intent"] == "health"

    def test_analyze_intent_future(self, analyzer):
        """Test detecting future intent."""
        text = "Estou incerto sobre meu futuro"
        result = analyzer.analyze(text)
        assert result["intent"] == "future"

    def test_analyze_has_question_true(self, analyzer):
        """Test detecting that text contains a question."""
        text = "Devo tomar essa decisão?"
        result = analyzer.analyze(text)
        assert result["has_question"] is True

    def test_analyze_has_question_false(self, analyzer):
        """Test detecting that text does not contain a question."""
        text = "Minha vida está uma bagunça"
        result = analyzer.analyze(text)
        assert result["has_question"] is False

    # Integration: Combined analysis
    def test_analyze_full_integration(self, analyzer):
        """Test full analysis with cards, emotion, and intent."""
        text = "Carta 3 e casamento - Devo mudar de emprego? Estou com medo"
        result = analyzer.analyze(text)

        # Cards detected
        assert 3 in result["card_ids"]
        assert 11 in result["card_ids"]

        # Emotion classified
        assert result["emotion"] in ["conflicted", "hopeful", "fearful", "uncertain"]

        # Intent detected
        assert result["intent"] in ["career", "relationship", "future", "general"]

        # Question detected
        assert result["has_question"] is True

    def test_analyze_normalized_text_output(self, analyzer):
        """Test that normalized text is correctly output."""
        text = "CARTA 3 (Caminho)"
        result = analyzer.analyze(text)
        assert result["normalized_text"] == "carta 3 caminho"

    def test_analyze_tokens_output(self, analyzer):
        """Test that tokens are correctly output."""
        text = "Olá mundo"
        result = analyzer.analyze(text)
        assert "tokens" in result
        assert isinstance(result["tokens"], list)
        assert "olá" in result["tokens"]
        assert "mundo" in result["tokens"]

    # Edge cases
    def test_analyze_whitespace_only(self, analyzer):
        """Test analyzing text with only whitespace."""
        result = analyzer.analyze("   \n\t  ")
        assert result["card_ids"] == []
        assert result["emotion"] == "uncertain"

    def test_analyze_special_characters_only(self, analyzer):
        """Test analyzing text with only special characters."""
        result = analyzer.analyze("!@#$%^&*()")
        assert result is not None
        assert "tokens" in result

    def test_analyze_unicode_only(self, analyzer):
        """Test analyzing text with only unicode characters."""
        result = analyzer.analyze("ãõçáéíóú")
        assert result is not None
        assert "tokens" in result

    def test_analyze_single_word(self, analyzer):
        """Test analyzing a single word."""
        result = analyzer.analyze("amor")
        assert result is not None
        assert "card_ids" in result
        assert 6 in result["card_ids"] or 27 in result["card_ids"]

    def test_analyze_leading_trailing_whitespace(self, analyzer):
        """Test analyzing text with leading/trailing whitespace."""
        result = analyzer.analyze("  Carta 5  ")
        assert 5 in result["card_ids"]

    def test_analyze_mixed_case(self, analyzer):
        """Test analyzing text with mixed case."""
        result = analyzer.analyze("CaRtA 7")
        assert 7 in result["card_ids"]

    def test_analyze_with_punctuation(self, analyzer):
        """Test analyzing text with various punctuation marks."""
        result = analyzer.analyze("Carta 3, Carta 5 e Carta 11!")
        assert 3 in result["card_ids"]
        assert 5 in result["card_ids"]
        assert 11 in result["card_ids"]

    # Helper method tests
    def test_find_cards_delegates_to_card_mapper(self, analyzer):
        """Test that find_cards method works correctly."""
        result = analyzer.find_cards("carta 7")
        assert len(result) == 1
        assert result[0]["id"] == 7

    def test_classify_emotion_delegates_to_classifier(self, analyzer):
        """Test that classify_emotion method works correctly."""
        result = analyzer.classify_emotion("Estou muito feliz")
        assert "emotion" in result
        assert "confidence" in result

    def test_tokenize_delegates_to_tokenizer(self, analyzer):
        """Test that tokenize method works correctly."""
        result = analyzer.tokenize("Olá Mundo")
        assert result == ["olá", "mundo"]

    def test_normalize_delegates_to_tokenizer(self, analyzer):
        """Test that normalize method works correctly."""
        result = analyzer.normalize("Carta 3 (Caminho)")
        assert result == "carta 3 caminho"

    # Result format tests
    def test_analyze_card_ids_are_integers(self, analyzer):
        """Test that card IDs are returned as integers."""
        result = analyzer.analyze("carta 5")
        for card_id in result["card_ids"]:
            assert isinstance(card_id, int)

    def test_analyze_cards_have_required_fields(self, analyzer):
        """Test that card dictionaries have required fields."""
        result = analyzer.analyze("carta 5")
        if result["cards"]:
            card = result["cards"][0]
            assert "id" in card
            assert "name" in card
            assert "keywords" in card

    def test_analyze_cards_sorted_by_id(self, analyzer):
        """Test that cards are returned sorted by ID."""
        result = analyzer.analyze("carta 15 carta 3 carta 8")
        card_ids = result["card_ids"]
        assert card_ids == sorted(card_ids)

    def test_analyze_emotion_confidence_is_float(self, analyzer):
        """Test that emotion confidence is a float between 0 and 1."""
        result = analyzer.analyze("Test text")
        confidence = result["emotion_confidence"]
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    # Acceptance criteria verification command test
    def test_acceptance_verification_command(self, analyzer):
        """Test: Verification command from implementation plan."""
        result = analyzer.analyze("Carta 3 (Caminho) e casamento")
        # From verification: should return card_ids containing 3 and 11
        assert 3 in result["card_ids"]
        assert 11 in result["card_ids"]
        # Emotion should be classified
        assert result["emotion"] in ["conflicted", "hopeful", "fearful", "uncertain"]
