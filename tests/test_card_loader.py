"""Tests for src/card_loader module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.card_loader import (
    get_data_path,
    load_deck,
    normalize_card_keywords,
    normalize_deck_keywords,
    validate_card_fields,
    validate_deck,
    REQUIRED_FIELDS,
    KEYWORD_FIELDS,
)


class TestGetDataPath:
    def test_returns_path_to_deck_file(self):
        path = get_data_path()
        assert path.exists()
        assert path.name == "cigano_deck.json"


class TestLoadDeck:
    def test_loads_36_cards(self):
        deck = load_deck()
        assert len(deck) == 36

    def test_cards_have_required_fields(self):
        deck = load_deck()
        for card in deck:
            for field in REQUIRED_FIELDS:
                assert field in card, f"Missing {field}"

    def test_themes_are_normalized_lowercase(self):
        deck = load_deck()
        for card in deck:
            for theme in card["themes"]:
                assert theme == theme.lower().strip()


class TestValidateCardFields:
    def test_raises_for_missing_field(self):
        card = {"id": 1, "name": "Test"}
        with pytest.raises(ValueError, match="missing required field"):
            validate_card_fields(card, 0)

    def test_does_not_raise_for_valid_card(self):
        card = {
            "id": 1,
            "name": "Test",
            "alternate_names": [],
            "themes": ["a", "b"],
            "meaning": "test",
            "directions": {"upright": "a", "reversed": "b"},
            "emotional_associations": [],
            "contextual_notes": "test",
        }
        validate_card_fields(card, 0)


class TestNormalizeKeywords:
    def test_normalizes_themes_to_lowercase(self):
        card = {
            "id": 1,
            "name": "Test",
            "alternate_names": ["ABC"],
            "themes": ["LOVE", "HATE"],
            "meaning": "test",
            "directions": {"upright": "a", "reversed": "b"},
            "emotional_associations": ["JOY"],
            "contextual_notes": "test",
        }
        normalized = normalize_card_keywords(card)
        assert normalized["themes"] == ["love", "hate"]
        assert normalized["alternate_names"] == ["abc"]
        assert normalized["emotional_associations"] == ["joy"]
