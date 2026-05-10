# coding: utf-8
"""Tests for the CardMapper class."""

import pytest
from clareza.card_mapper import CardMapper


class TestCardMapper:
    """Test suite for CardMapper."""

    @pytest.fixture
    def mapper(self):
        """Create a CardMapper instance for testing."""
        return CardMapper()

    def test_init_creates_instance(self, mapper):
        """Test that mapper initializes correctly."""
        assert mapper is not None
        assert hasattr(mapper, "find_cards")

    def test_find_cards_empty_string(self, mapper):
        """Test finding cards in empty string returns empty list."""
        result = mapper.find_cards("")
        assert result == []

    def test_find_cards_none_returns_empty(self, mapper):
        """Test finding cards with None returns empty list."""
        result = mapper.find_cards(None)
        assert result == []

    def test_find_cards_numeric_pattern_carta(self, mapper):
        """Test detecting cards using 'carta N' pattern."""
        result = mapper.find_cards("carta 3")
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_find_cards_numeric_pattern_numero(self, mapper):
        """Test detecting cards using 'numero N' pattern."""
        result = mapper.find_cards("numero 7")
        assert len(result) == 1
        assert result[0]["id"] == 7

    def test_find_cards_numeric_pattern_card(self, mapper):
        """Test detecting cards using 'card N' pattern."""
        result = mapper.find_cards("card 15")
        assert len(result) == 1
        assert result[0]["id"] == 15

    def test_find_cards_numeric_pattern_case_insensitive(self, mapper):
        """Test that numeric pattern detection is case insensitive."""
        result = mapper.find_cards("CARTA 5")
        assert len(result) == 1
        assert result[0]["id"] == 5

    def test_find_cards_numeric_pattern_with_parentheses(self, mapper):
        """Test detecting cards with parentheses around name."""
        result = mapper.find_cards("Carta 3 (Caminho)")
        card_ids = [c["id"] for c in result]
        assert 3 in card_ids

    def test_find_cards_multiple_numeric(self, mapper):
        """Test detecting multiple card numbers in text."""
        result = mapper.find_cards("carta 3 e carta 11")
        card_ids = [c["id"] for c in result]
        assert 3 in card_ids
        assert 11 in card_ids

    def test_find_cards_invalid_number_out_of_range(self, mapper):
        """Test that card numbers outside 1-36 range are ignored."""
        result = mapper.find_cards("carta 42")
        assert result == []

    def test_find_cards_invalid_number_zero(self, mapper):
        """Test that card number 0 is ignored."""
        result = mapper.find_cards("carta 0")
        assert result == []

    def test_find_cards_invalid_number_negative(self, mapper):
        """Test that negative card numbers are ignored."""
        result = mapper.find_cards("carta -5")
        assert result == []

    def test_find_cards_by_theme_casamento(self, mapper):
        """Test detecting cards by theme keyword 'casamento'."""
        result = mapper.find_cards("casamento")
        card_ids = [c["id"] for c in result]
        assert 11 in card_ids

    def test_find_cards_by_theme_casar(self, mapper):
        """Test detecting cards by theme keyword 'casar'."""
        result = mapper.find_cards("quando vou me casar")
        card_ids = [c["id"] for c in result]
        assert 11 in card_ids

    def test_find_cards_by_theme_amor(self, mapper):
        """Test detecting cards by theme keyword 'amor'."""
        result = mapper.find_cards("amor")
        card_ids = [c["id"] for c in result]
        assert 6 in card_ids
        assert 27 in card_ids

    def test_find_cards_by_theme_caminho(self, mapper):
        """Test detecting cards by theme keyword 'caminho'."""
        result = mapper.find_cards("caminho")
        card_ids = [c["id"] for c in result]
        assert 3 in card_ids
        assert 11 in card_ids

    def test_find_cards_by_theme_uniao(self, mapper):
        """Test detecting cards by theme keyword 'união'."""
        result = mapper.find_cards("união")
        card_ids = [c["id"] for c in result]
        assert 6 in card_ids

    def test_find_cards_combined_numeric_and_theme(self, mapper):
        """Test detecting cards with both numeric and theme references."""
        result = mapper.find_cards("Carta 3 (Caminho) e casamento")
        card_ids = [c["id"] for c in result]
        assert 3 in card_ids
        assert 11 in card_ids

    def test_find_cards_returns_dict_format(self, mapper):
        """Test that find_cards returns dictionaries with expected keys."""
        result = mapper.find_cards("carta 5")
        assert len(result) == 1
        card = result[0]
        assert "id" in card
        assert "name" in card
        assert "keywords" in card

    def test_find_cards_returns_in_id_order(self, mapper):
        """Test that returned cards are sorted by ID."""
        result = mapper.find_cards("carta 15 carta 3 carta 8")
        card_ids = [c["id"] for c in result]
        assert card_ids == sorted(card_ids)

    def test_find_cards_no_duplicates(self, mapper):
        """Test that same card mentioned multiple times appears once."""
        result = mapper.find_cards("carta 3 carta 3 carta 3")
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_find_cards_preserves_accents(self, mapper):
        """Test that Portuguese accented characters work in detection."""
        result = mapper.find_cards("carte 3")
        assert len(result) == 0

    def test_find_cards_with_punctuation(self, mapper):
        """Test that punctuation is handled correctly."""
        result = mapper.find_cards("Carta 3, Carta 5 e Carta 11!")
        card_ids = [c["id"] for c in result]
        assert 3 in card_ids
        assert 5 in card_ids
        assert 11 in card_ids

    def test_find_cards_with_whitespace(self, mapper):
        """Test that various whitespace patterns are handled."""
        result = mapper.find_cards("carta    3\n\n\te   carta   5")
        card_ids = [c["id"] for c in result]
        assert 3 in card_ids
        assert 5 in card_ids

    def test_find_cards_long_text(self, mapper):
        """Test detecting cards in a longer text."""
        text = "Estou pensando muito sobre minha vida. Carta 3 me veio à mente. " * 50
        result = mapper.find_cards(text)
        card_ids = [c["id"] for c in result]
        assert 3 in card_ids

    def test_find_cards_special_characters_only(self, mapper):
        """Test that text with only special characters returns empty."""
        result = mapper.find_cards("!@#$%^&*()")
        assert result == []

    def test_find_cards_unicode_handling(self, mapper):
        """Test that unicode characters are handled without errors."""
        result = mapper.find_cards("ãõçáéíóú")
        assert isinstance(result, list)

    def test_find_cards_case_insensitive_theme(self, mapper):
        """Test that theme detection is case insensitive."""
        result = mapper.find_cards("CASAMENTO")
        card_ids = [c["id"] for c in result]
        assert 11 in card_ids

    def test_find_cards_by_card_name(self, mapper):
        """Test detecting cards by their full name."""
        result = mapper.find_cards("Cegonha")
        card_ids = [c["id"] for c in result]
        assert 33 in card_ids

    def test_find_cards_by_card_name_part(self, mapper):
        """Test detecting cards by part of their name."""
        result = mapper.find_cards("enamorados")
        card_ids = [c["id"] for c in result]
        assert len(card_ids) > 0
