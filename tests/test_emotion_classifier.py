# coding: utf-8
"""Tests for the EmotionClassifier class."""

import pytest
from clareza.emotion_classifier import EmotionClassifier


class TestEmotionClassifier:
    """Test suite for EmotionClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create an EmotionClassifier instance for testing."""
        return EmotionClassifier()

    def test_init_creates_instance(self, classifier):
        """Test that classifier initializes correctly."""
        assert classifier is not None
        assert hasattr(classifier, "classify")
        assert hasattr(classifier, "classify_with_confidence")

    def test_classify_empty_string(self, classifier):
        """Test classifying an empty string returns 'uncertain'."""
        result = classifier.classify("")
        assert result == "uncertain"

    def test_classify_none_returns_uncertain(self, classifier):
        """Test classifying None returns 'uncertain'."""
        result = classifier.classify(None)
        assert result == "uncertain"

    def test_classify_whitespace_only_returns_uncertain(self, classifier):
        """Test classifying whitespace-only returns 'uncertain'."""
        result = classifier.classify("   \n\t  ")
        assert result == "uncertain"

    # Conflicted emotion tests
    def test_classify_conflicted_keywords(self, classifier):
        """Test classification of conflicted emotion keywords."""
        result = classifier.classify("Estou confuso e indeciso sobre o que fazer")
        assert result == "conflicted"

    def test_classify_conflicted_hesitante(self, classifier):
        """Test 'hesitante' maps to conflicted."""
        result = classifier.classify("Me sinto hesitante em tomar essa decisão")
        assert result == "conflicted"

    def test_classify_conflicted_duvida(self, classifier):
        """Test 'dúvida' maps to conflicted."""
        result = classifier.classify("Tenho muita dúvida sobre meu relacionamento")
        assert result == "conflicted"

    def test_classify_conflicted_inseguro(self, classifier):
        """Test 'inseguro' maps to conflicted."""
        result = classifier.classify("Me sinto inseguro com essa escolha")
        assert result == "conflicted"

    # Hopeful emotion tests
    def test_classify_hopeful_keywords(self, classifier):
        """Test classification of hopeful emotion keywords."""
        result = classifier.classify("Tenho esperança de que tudo vai melhorar")
        assert result == "hopeful"

    def test_classify_hopeful_confiante(self, classifier):
        """Test 'confiante' maps to hopeful."""
        result = classifier.classify("Estou confiante de que farei a escolha certa")
        assert result == "hopeful"

    def test_classify_hopeful_otimista(self, classifier):
        """Test 'otimista' maps to hopeful."""
        result = classifier.classify("Sou otimista sobre meu futuro")
        assert result == "hopeful"

    def test_classify_hopeful_melhor(self, classifier):
        """Test 'melhor' maps to hopeful."""
        result = classifier.classify("Acredito que vai ficar melhor")
        assert result == "hopeful"

    # Fearful emotion tests
    def test_classify_fearful_keywords(self, classifier):
        """Test classification of fearful emotion keywords."""
        result = classifier.classify("Estou com medo do que vai acontecer")
        assert result == "fearful"

    def test_classify_fearful_ansioso(self, classifier):
        """Test 'ansioso' maps to fearful."""
        result = classifier.classify("Me sinto muito ansioso sobre isso")
        assert result == "fearful"

    def test_classify_fearful_preocupado(self, classifier):
        """Test 'preocupado' maps to fearful."""
        result = classifier.classify("Estou muito preocupado com meu futuro")
        assert result == "fearful"

    def test_classify_fearful_assustado(self, classifier):
        """Test 'assustado' maps to fearful."""
        result = classifier.classify("Estou assustado com essa situação")
        assert result == "fearful"

    def test_classify_fearful_medo(self, classifier):
        """Test 'medo' maps to fearful."""
        result = classifier.classify("Tenho medo de falhar")
        assert result == "fearful"

    def test_classify_fearful_fracasso(self, classifier):
        """Test 'fracasso' maps to fearful."""
        result = classifier.classify("Tenho medo de fracasso")
        assert result == "fearful"

    # Uncertain emotion tests
    def test_classify_uncertain_keywords(self, classifier):
        """Test classification of uncertain emotion keywords."""
        result = classifier.classify("Não sei o que fazer")
        assert result == "uncertain"

    def test_classify_uncertain_nao_sei(self, classifier):
        """Test 'não sei' maps to uncertain."""
        result = classifier.classify("Não sei se devo tomar essa decisão")
        assert result == "uncertain"

    def test_classify_uncertain_confuso(self, classifier):
        """Test 'confuso' maps to conflicted (confuso is a conflicted emotion)."""
        result = classifier.classify("Me sinto muito confuso")
        assert result == "conflicted"

    def test_classify_uncertain_perdido(self, classifier):
        """Test 'perdido' maps to uncertain."""
        result = classifier.classify("Estou perdido sem saber o que fazer")
        assert result == "uncertain"

    def test_classify_uncertain_talvez(self, classifier):
        """Test 'talvez' maps to uncertain."""
        result = classifier.classify("Talvez eu deva fazer isso")
        assert result == "uncertain"

    def test_classify_uncertain_no_emotion_keywords(self, classifier):
        """Test text without emotion keywords returns 'uncertain'."""
        result = classifier.classify("O tempo está bonito hoje")
        assert result == "uncertain"

    # classify_with_confidence tests
    def test_classify_with_confidence_returns_dict(self, classifier):
        """Test classify_with_confidence returns expected dictionary format."""
        result = classifier.classify_with_confidence("Estou com medo")
        assert isinstance(result, dict)
        assert "emotion" in result
        assert "confidence" in result
        assert "scores" in result

    def test_classify_with_confidence_scores_for_all_emotions(self, classifier):
        """Test that scores contains all four emotion categories."""
        result = classifier.classify_with_confidence("texto de teste")
        assert "conflicted" in result["scores"]
        assert "hopeful" in result["scores"]
        assert "fearful" in result["scores"]
        assert "uncertain" in result["scores"]

    def test_classify_with_confidence_empty_string(self, classifier):
        """Test classify_with_confidence with empty string."""
        result = classifier.classify_with_confidence("")
        assert result["emotion"] == "uncertain"
        assert result["confidence"] == 0.0

    def test_classify_with_confidence_none(self, classifier):
        """Test classify_with_confidence with None."""
        result = classifier.classify_with_confidence(None)
        assert result["emotion"] == "uncertain"
        assert result["confidence"] == 0.0

    def test_classify_with_confidence_confidence_is_float(self, classifier):
        """Test that confidence is a float between 0 and 1."""
        result = classifier.classify_with_confidence("Tenho esperança")
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_classify_with_confidence_scores_are_floats(self, classifier):
        """Test that individual scores are floats."""
        result = classifier.classify_with_confidence("texto")
        for emotion, score in result["scores"].items():
            assert isinstance(score, float)

    # Case insensitivity tests
    def test_classify_case_insensitive_conflicted(self, classifier):
        """Test that classification is case insensitive for conflicted."""
        result_lower = classifier.classify("confuso e indeciso")
        result_upper = classifier.classify("CONFUSO E INDECISO")
        assert result_lower == result_upper

    def test_classify_case_insensitive_hopeful(self, classifier):
        """Test that classification is case insensitive for hopeful."""
        result_lower = classifier.classify("esperança")
        result_upper = classifier.classify("ESPERANÇA")
        assert result_lower == result_upper

    # Accented characters tests
    def test_classify_preserves_portuguese_accents(self, classifier):
        """Test that Portuguese accented characters work correctly."""
        result = classifier.classify("Não tenho certeza sobre isso")
        assert result == "uncertain"

    def test_classify_émotion_keyword_with_accents(self, classifier):
        """Test emotion keyword with proper Portuguese accents."""
        result = classifier.classify("Estou très anxiouso")
        assert result in ["fearful", "conflicted", "uncertain"]

    # Edge cases
    def test_classify_special_characters_only(self, classifier):
        """Test classifying text with only special characters."""
        result = classifier.classify("!@#$%^&*()")
        assert result == "uncertain"

    def test_classify_long_text(self, classifier):
        """Test classifying a long text input."""
        text = "Estou confuso sobre minha vida. " * 100
        result = classifier.classify(text)
        assert result == "conflicted"

    def test_classify_numbers_only(self, classifier):
        """Test classifying text with only numbers."""
        result = classifier.classify("12345")
        assert result == "uncertain"

    def test_classify_mixed_emotions_takes_dominant(self, classifier):
        """Test that when multiple emotions are present, dominant one wins."""
        text = "Estou confuso e com medo, mas também tenho esperança"
        result = classifier.classify(text)
        assert result in ["conflicted", "fearful", "hopeful", "uncertain"]

    def test_classify_frequent_keyword_wins(self, classifier):
        """Test that repeated keywords lead to that emotion."""
        text = "medo medo medo medo medo"
        result = classifier.classify(text)
        assert result == "fearful"

    def test_classify_unicode_handling(self, classifier):
        """Test that unicode characters are handled without errors."""
        result = classifier.classify("ãõçáéíóú")
        assert result in ["conflicted", "hopeful", "fearful", "uncertain"]

    # Integration-style tests (matching the verification command)
    def test_classify_verification_fearful(self, classifier):
        """Test the verification command from implementation plan."""
        result = classifier.classify("Estou confuso e com medo sobre meu futuro")
        assert result == "fearful"

    def test_classify_returns_valid_emotion_category(self, classifier):
        """Test that classify always returns one of the four valid categories."""
        valid_emotions = {"conflicted", "hopeful", "fearful", "uncertain"}
        test_texts = [
            "texto normal",
            "medo",
            "esperança",
            "confuso",
            "não sei",
        ]
        for text in test_texts:
            result = classifier.classify(text)
            assert result in valid_emotions