"""Tests for the card_loader module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.card_loader import (
    REQUIRED_FIELDS,
    KEYWORD_FIELDS,
    get_data_path,
    load_deck,
    normalize_card_keywords,
    normalize_deck_keywords,
    validate_card_fields,
    validate_deck,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def valid_card() -> dict:
    """Return a valid card dictionary for testing."""
    return {
        "id": 1,
        "name": "The Fool",
        "name_pt": "O Louco",
        "alternate_names": ["The Fool", "Le Fou"],
        "themes": ["new beginning", "freedom", "adventure"],
        "meaning": "A fresh start, innocence, carefree spirit",
        "directions": {
            "upright": "New beginnings, innocence, carefree",
            "reversed": "Recklessness, risk-taking, holding back"
        },
        "emotional_associations": ["joy", "excitement", "wonder"],
        "contextual_notes": "Consider starting something new but be aware of risks."
    }


@pytest.fixture
def minimal_card() -> dict:
    """Return a card with only required fields."""
    return {
        "id": 1,
        "name": "Test Card",
        "alternate_names": ["Test"],
        "themes": ["test"],
        "meaning": "Test meaning",
        "directions": {"upright": "Test", "reversed": "Test"},
        "emotional_associations": ["test"],
        "contextual_notes": "Test notes"
    }


# ----------------------------------------------------------------------
# get_data_path tests
# ----------------------------------------------------------------------


class TestGetDataPath:
    """Tests for get_data_path function."""

    def test_returns_path_to_deck_json(self):
        """get_data_path should return path to cigano_deck.json."""
        path = get_data_path()
        assert path.name == "cigano_deck.json"
        assert path.exists()

    def test_path_points_to_data_directory(self):
        """get_data_path should return path in data directory."""
        path = get_data_path()
        assert path.parent.name == "data"


# ----------------------------------------------------------------------
# validate_card_fields tests
# ----------------------------------------------------------------------


class TestValidateCardFields:
    """Tests for validate_card_fields function."""

    def test_valid_card_passes_validation(self, valid_card):
        """A valid card should pass validation without raising."""
        # Should not raise any exception
        validate_card_fields(valid_card, 0)

    def test_missing_required_field_raises(self, valid_card):
        """Missing required field should raise ValueError."""
        del valid_card["name"]
        with pytest.raises(ValueError, match="missing required field: 'name'"):
            validate_card_fields(valid_card, 0)

    def test_card_index_in_error_message(self, valid_card):
        """Error message should include the card index."""
        del valid_card["meaning"]
        with pytest.raises(ValueError, match="index 5"):
            validate_card_fields(valid_card, 5)

    def test_all_required_fields_missing_raises(self, minimal_card):
        """Should raise for any missing required field."""
        minimal_card.pop("themes")
        with pytest.raises(ValueError, match="missing required field: 'themes'"):
            validate_card_fields(minimal_card, 0)


# ----------------------------------------------------------------------
# validate_deck tests
# ----------------------------------------------------------------------


class TestValidateDeck:
    """Tests for validate_deck function."""

    def test_valid_deck_passes_validation(self, valid_card):
        """A valid deck should pass validation."""
        deck = [valid_card]
        validate_deck(deck)  # Should not raise

    def test_non_dict_card_raises(self, valid_card):
        """Non-dictionary card should raise ValueError."""
        deck = [valid_card, "not a card", valid_card]
        with pytest.raises(ValueError, match="is not a dictionary"):
            validate_deck(deck)

    def test_multiple_invalid_cards_raises_on_first(self, minimal_card):
        """Should raise on first invalid card found."""
        invalid_card = minimal_card.copy()
        del invalid_card["meaning"]
        deck = [minimal_card, invalid_card, minimal_card]
        with pytest.raises(ValueError, match="index 1"):
            validate_deck(deck)

    def test_empty_deck_valid(self):
        """Empty deck passes validation (length check is separate)."""
        deck: list = []
        validate_deck(deck)  # Should not raise


# ----------------------------------------------------------------------
# normalize_card_keywords tests
# ----------------------------------------------------------------------


class TestNormalizeCardKeywords:
    """Tests for normalize_card_keywords function."""

    def test_normalizes_themes_to_lowercase(self):
        """Themes should be normalized to lowercase."""
        card = {"themes": ["LOVE", "JOY", "Peace"]}
        normalized = normalize_card_keywords(card)
        assert normalized["themes"] == ["love", "joy", "peace"]

    def test_normalizes_alternate_names_to_lowercase(self):
        """Alternate names should be normalized to lowercase."""
        card = {"alternate_names": ["THE FOOL", "Le Fou"]}
        normalized = normalize_card_keywords(card)
        assert normalized["alternate_names"] == ["the fool", "le fou"]

    def test_normalizes_emotional_associations_to_lowercase(self):
        """Emotional associations should be normalized to lowercase."""
        card = {"emotional_associations": ["JOY", "EXCITEMENT"]}
        normalized = normalize_card_keywords(card)
        assert normalized["emotional_associations"] == ["joy", "excitement"]

    def test_trims_whitespace(self):
        """Keywords should have whitespace trimmed."""
        card = {"themes": ["  love  ", "  joy"]}
        normalized = normalize_card_keywords(card)
        assert normalized["themes"] == ["love", "joy"]

    def test_does_not_modify_original_card(self):
        """Original card should not be modified."""
        card = {"themes": ["LOVE"]}
        _ = normalize_card_keywords(card)
        assert card["themes"] == ["LOVE"]

    def test_missing_keyword_field_preserved(self):
        """Missing keyword fields should not cause errors."""
        card = {"id": 1, "name": "Test"}
        normalized = normalize_card_keywords(card)
        assert normalized == card


# ----------------------------------------------------------------------
# normalize_deck_keywords tests
# ----------------------------------------------------------------------


class TestNormalizeDeckKeywords:
    """Tests for normalize_deck_keywords function."""

    def test_normalizes_all_cards(self):
        """All cards in deck should be normalized."""
        deck = [
            {"themes": ["LOVE"]},
            {"themes": ["JOY"]}
        ]
        normalized = normalize_deck_keywords(deck)
        assert normalized[0]["themes"] == ["love"]
        assert normalized[1]["themes"] == ["joy"]

    def test_returns_new_list(self):
        """Should return a new list, not modify original."""
        deck = [{"themes": ["LOVE"]}]
        normalized = normalize_deck_keywords(deck)
        assert normalized is not deck
        assert deck[0]["themes"] == ["LOVE"]


# ----------------------------------------------------------------------
# load_deck tests
# ----------------------------------------------------------------------


class TestLoadDeck:
    """Tests for load_deck function."""

    def test_loads_36_cards(self):
        """Should load exactly 36 cards."""
        deck = load_deck()
        assert len(deck) == 36

    def test_returns_list_of_dicts(self):
        """Should return a list of dictionaries."""
        deck = load_deck()
        assert isinstance(deck, list)
        assert all(isinstance(card, dict) for card in deck)

    def test_cards_have_required_fields(self):
        """All cards should have all required fields."""
        deck = load_deck()
        for card in deck:
            for field in REQUIRED_FIELDS:
                assert field in card, f"Card missing field: {field}"

    def test_cards_have_ids_1_to_36(self):
        """Cards should have IDs from 1 to 36."""
        deck = load_deck()
        ids = sorted([card["id"] for card in deck])
        assert ids == list(range(1, 37))

    def test_themes_are_normalized(self):
        """All themes should be lowercase and trimmed."""
        deck = load_deck()
        for card in deck:
            for theme in card["themes"]:
                assert theme == theme.lower().strip()

    def test_alternate_names_normalized(self):
        """Alternate names should be lowercase and trimmed."""
        deck = load_deck()
        for card in deck:
            for alt_name in card["alternate_names"]:
                assert alt_name == alt_name.lower().strip()

    def test_directions_has_upright_and_reversed(self):
        """Each card's directions should have upright and reversed keys."""
        deck = load_deck()
        for card in deck:
            directions = card["directions"]
            assert "upright" in directions
            assert "reversed" in directions

    def test_file_not_found_raises_error(self):
        """Missing data file should raise FileNotFoundError."""
        from src import card_loader as cl
        original_path = cl.get_data_path
        try:
            cl.get_data_path = lambda: Path("/nonexistent/path.json")
            with pytest.raises(FileNotFoundError, match="Deck data file not found"):
                cl.load_deck()
        finally:
            cl.get_data_path = original_path

    def test_invalid_json_raises_error(self):
        """Invalid JSON should raise json.JSONDecodeError."""
        from src import card_loader as cl

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("not valid json {{{")
            f.flush()
            temp_path = f.name

        original_path = cl.get_data_path
        try:
            cl.get_data_path = lambda: Path(temp_path)
            with pytest.raises(json.JSONDecodeError):
                cl.load_deck()
        finally:
            cl.get_data_path = original_path
            os.unlink(temp_path)

    def test_wrong_card_count_raises_error(self):
        """Wrong number of cards should raise ValueError."""
        from src import card_loader as cl

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump([{"id": 1, "name": "Test", "alternate_names": [],
                      "themes": ["test"], "meaning": "Test",
                      "directions": {"upright": "A", "reversed": "B"},
                      "emotional_associations": [], "contextual_notes": ""}], f)
            f.flush()
            temp_path = f.name

        original_path = cl.get_data_path
        try:
            cl.get_data_path = lambda: Path(temp_path)
            with pytest.raises(ValueError, match="Expected 36 cards, got 1"):
                cl.load_deck()
        finally:
            cl.get_data_path = original_path
            os.unlink(temp_path)

    def test_missing_required_field_raises_error(self):
        """Missing required field should raise ValueError."""
        from src import card_loader as cl

        card = {
            "id": 1,
            "name": "Test"
            # Missing other required fields
        }
        deck = [card] * 36

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(deck, f)
            f.flush()
            temp_path = f.name

        original_path = cl.get_data_path
        try:
            cl.get_data_path = lambda: Path(temp_path)
            with pytest.raises(ValueError, match="missing required field"):
                cl.load_deck()
        finally:
            cl.get_data_path = original_path
            os.unlink(temp_path)

    def test_non_list_data_raises_error(self):
        """Non-list data should raise ValueError."""
        from src import card_loader as cl

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({"cards": []}, f)  # Not a list
            f.flush()
            temp_path = f.name

        original_path = cl.get_data_path
        try:
            cl.get_data_path = lambda: Path(temp_path)
            with pytest.raises(ValueError, match="Deck data must be a list"):
                cl.load_deck()
        finally:
            cl.get_data_path = original_path
            os.unlink(temp_path)


# ----------------------------------------------------------------------
# Integration tests
# ----------------------------------------------------------------------


class TestIntegration:
    """Integration tests for card_loader with real data."""

    def test_full_deck_loaded_successfully(self):
        """Full deck should load without errors."""
        deck = load_deck()
        assert len(deck) == 36

    def test_all_cards_validated(self):
        """All loaded cards should pass validation."""
        deck = load_deck()
        validate_deck(deck)  # Should not raise

    def test_keywords_normalized_across_deck(self):
        """All keywords in deck should be normalized."""
        deck = load_deck()
        for card in deck:
            for theme in card["themes"]:
                assert theme == theme.lower()
                assert theme == theme.strip()