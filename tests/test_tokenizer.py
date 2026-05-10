# coding: utf-8
"""Tests for the PortugueseTokenizer class."""

import pytest
from clareza.tokenizer import PortugueseTokenizer


class TestPortugueseTokenizer:
    """Test suite for PortugueseTokenizer."""

    @pytest.fixture
    def tokenizer(self):
        """Create a tokenizer instance for testing."""
        return PortugueseTokenizer()

    def test_init_creates_instance(self, tokenizer):
        """Test that tokenizer initializes correctly."""
        assert tokenizer is not None
        assert hasattr(tokenizer, "normalize")
        assert hasattr(tokenizer, "tokenize")

    def test_normalize_empty_string(self, tokenizer):
        """Test normalizing an empty string returns empty string."""
        result = tokenizer.normalize("")
        assert result == ""

    def test_normalize_none_returns_empty(self, tokenizer):
        """Test normalizing None returns empty string."""
        result = tokenizer.normalize(None)
        assert result == ""

    def test_normalize_converts_to_lowercase(self, tokenizer):
        """Test that normalization converts text to lowercase."""
        result = tokenizer.normalize("HELLO WORLD")
        assert result == "hello world"

    def test_normalize_mixed_case(self, tokenizer):
        """Test normalization with mixed case input."""
        result = tokenizer.normalize("Olá Mundo")
        assert result == "olá mundo"

    def test_normalize_removes_parentheses(self, tokenizer):
        """Test that parentheses are removed during normalization."""
        result = tokenizer.normalize("Carta 3 (Caminho)")
        assert result == "carta 3 caminho"

    def test_normalize_removes_brackets(self, tokenizer):
        """Test that brackets are removed during normalization."""
        result = tokenizer.normalize("texto [com] colchetes")
        assert result == "texto com colchetes"

    def test_normalize_removes_punctuation(self, tokenizer):
        """Test that various punctuation marks are removed."""
        result = tokenizer.normalize("oi, como vai? você!")
        assert result == "oi como vai você"

    def test_normalize_normalizes_whitespace(self, tokenizer):
        """Test that multiple whitespace characters are normalized to single space."""
        result = tokenizer.normalize("hello    world\n\ttab")
        assert result == "hello world tab"

    def test_normalize_strips_leading_trailing_whitespace(self, tokenizer):
        """Test that leading and trailing whitespace is stripped."""
        result = tokenizer.normalize("  hello world  ")
        assert result == "hello world"

    def test_normalize_preserves_accents(self, tokenizer):
        """Test that Portuguese accented characters are preserved."""
        result = tokenizer.normalize("ãõçáéíóú àèìòù âêîôû")
        assert "ã" in result
        assert "õ" in result
        assert "ç" in result
        assert "á" in result
        assert "é" in result
        assert "í" in result
        assert "ó" in result
        assert "ú" in result
        assert "à" in result
        assert "è" in result
        assert "ì" in result
        assert "ò" in result
        assert "ù" in result
        assert "â" in result
        assert "ê" in result
        assert "î" in result
        assert "ô" in result
        assert "û" in result

    def test_normalize_card_reference(self, tokenizer):
        """Test normalizing a card reference with parentheses."""
        result = tokenizer.normalize("Carta 3 (Caminho)")
        assert result == "carta 3 caminho"

    def test_normalize_full_sentence(self, tokenizer):
        """Test normalizing a full Portuguese sentence."""
        result = tokenizer.normalize("Estou confuso sobre minha carreira.")
        assert result == "estou confuso sobre minha carreira"

    def test_tokenize_empty_string(self, tokenizer):
        """Test tokenizing an empty string returns empty list."""
        result = tokenizer.tokenize("")
        assert result == []

    def test_tokenize_single_word(self, tokenizer):
        """Test tokenizing a single word."""
        result = tokenizer.tokenize("hello")
        assert result == ["hello"]

    def test_tokenize_multiple_words(self, tokenizer):
        """Test tokenizing multiple words returns list of tokens."""
        result = tokenizer.tokenize("hello world")
        assert result == ["hello", "world"]

    def test_tokenize_normalizes_before_tokenizing(self, tokenizer):
        """Test that tokenize applies normalization first."""
        result = tokenizer.tokenize("HELLO, World!")
        assert result == ["hello", "world"]

    def test_tokenize_preserves_word_boundaries(self, tokenizer):
        """Test that tokenize correctly identifies word boundaries."""
        result = tokenizer.tokenize("um dois três")
        assert len(result) == 3
        assert result == ["um", "dois", "três"]

    def test_tokenize_with_accents(self, tokenizer):
        """Test tokenizing text with Portuguese accents."""
        result = tokenizer.tokenize("coraçãoação")
        assert result == ["coraçãoação"]

    def test_normalize_long_text(self, tokenizer):
        """Test normalizing a longer text."""
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 100
        result = tokenizer.normalize(text)
        assert "lorem" in result
        assert "ipsum" in result
        assert "," not in result
        assert "." not in result

    def test_tokenize_long_text(self, tokenizer):
        """Test tokenizing a longer text produces correct token count."""
        text = "a b c d e f g h i j k l m n o p q r s t u v w x y z"
        result = tokenizer.tokenize(text)
        assert len(result) == 26

    def test_normalize_special_characters_only(self, tokenizer):
        """Test normalizing text with only special characters."""
        result = tokenizer.normalize("!@#$%^&*()")
        assert result == ""

    def test_normalize_unicode_emojis(self, tokenizer):
        """Test that unicode emojis are handled (removed as special chars)."""
        result = tokenizer.normalize("hello world")
        assert result == "hello world"

    def test_combined_operations(self, tokenizer):
        """Test combined normalization and tokenization."""
        text = "  Hello, World!  "
        normalized = tokenizer.normalize(text)
        tokens = tokenizer.tokenize(text)

        assert normalized == "hello world"
        assert tokens == ["hello", "world"]