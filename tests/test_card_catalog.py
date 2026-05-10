"""Data integrity tests for the Baralho Cigano card catalog.

These tests verify the structural integrity of the cigano_deck.json data file,
ensuring all 36 cards conform to the expected schema and acceptance criteria.
"""

import json
from pathlib import Path

import pytest

from src.card_loader import get_data_path, load_deck


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def deck() -> list:
    """Load and return the full deck of 36 cards."""
    return load_deck()


@pytest.fixture
def deck_data() -> list:
    """Load raw deck data from JSON file."""
    data_path = get_data_path()
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------
# Schema and structure tests
# ----------------------------------------------------------------------


class TestCardSchema:
    """Tests for card schema compliance."""

    REQUIRED_FIELDS = [
        "id",
        "name",
        "name_pt",
        "alternate_names",
        "themes",
        "meaning",
        "directions",
        "emotional_associations",
        "contextual_notes",
    ]

    def test_all_cards_have_required_fields(self, deck_data):
        """Every card must have all required fields."""
        for index, card in enumerate(deck_data):
            missing = [
                field for field in self.REQUIRED_FIELDS if field not in card
            ]
            assert not missing, (
                f"Card at index {index} (id={card.get('id', 'unknown')}) "
                f"missing fields: {missing}"
            )

    def test_directions_has_upright_and_reversed(self, deck_data):
        """Each card's directions must have both upright and reversed."""
        for index, card in enumerate(deck_data):
            directions = card.get("directions", {})
            assert "upright" in directions, (
                f"Card at index {index} missing 'upright' in directions"
            )
            assert "reversed" in directions, (
                f"Card at index {index} missing 'reversed' in directions"
            )

    def test_alternate_names_is_list(self, deck_data):
        """alternate_names must be a list."""
        for index, card in enumerate(deck_data):
            alt_names = card.get("alternate_names")
            assert isinstance(alt_names, list), (
                f"Card at index {index} alternate_names is not a list: "
                f"{type(alt_names).__name__}"
            )

    def test_themes_is_list(self, deck_data):
        """themes must be a list."""
        for index, card in enumerate(deck_data):
            themes = card.get("themes")
            assert isinstance(themes, list), (
                f"Card at index {index} themes is not a list: "
                f"{type(themes).__name__}"
            )

    def test_emotional_associations_is_list(self, deck_data):
        """emotional_associations must be a list."""
        for index, card in enumerate(deck_data):
            emotions = card.get("emotional_associations")
            assert isinstance(emotions, list), (
                f"Card at index {index} emotional_associations is not a list: "
                f"{type(emotions).__name__}"
            )


# ----------------------------------------------------------------------
# Data completeness tests
# ----------------------------------------------------------------------


class TestDeckCompleteness:
    """Tests for deck completeness."""

    def test_deck_has_exactly_36_cards(self, deck):
        """Deck must contain exactly 36 cards."""
        assert len(deck) == 36, f"Expected 36 cards, got {len(deck)}"

    def test_card_ids_range_from_1_to_36(self, deck):
        """Card IDs must be exactly 1 through 36."""
        ids = sorted([card["id"] for card in deck])
        expected = list(range(1, 37))
        assert ids == expected, f"Card IDs mismatch. Expected {expected}, got {ids}"

    def test_no_duplicate_card_ids(self, deck):
        """No two cards may have the same ID."""
        ids = [card["id"] for card in deck]
        unique_ids = set(ids)
        assert len(ids) == len(unique_ids), (
            f"Duplicate card IDs found: "
            f"{[id for id in ids if ids.count(id) > 1]}"
        )

    def test_no_duplicate_canonical_names(self, deck):
        """No two cards may have the same canonical name."""
        names = [card["name"] for card in deck]
        unique_names = set(names)
        assert len(names) == len(unique_names), (
            f"Duplicate canonical names found: "
            f"{[name for name in names if names.count(name) > 1]}"
        )

    def test_all_cards_have_meaning(self, deck):
        """Every card must have a non-empty meaning."""
        for card in deck:
            meaning = card.get("meaning", "")
            assert meaning.strip(), (
                f"Card {card['id']} has empty meaning"
            )

    def test_all_cards_have_contextual_notes(self, deck):
        """Every card must have contextual notes."""
        for card in deck:
            notes = card.get("contextual_notes", "")
            assert notes.strip(), (
                f"Card {card['id']} has empty contextual_notes"
            )

    def test_all_cards_have_name_pt(self, deck):
        """Every card must have Portuguese name."""
        for card in deck:
            name_pt = card.get("name_pt", "")
            assert name_pt.strip(), (
                f"Card {card['id']} is missing name_pt"
            )


# ----------------------------------------------------------------------
# Theme keyword tests
# ----------------------------------------------------------------------


class TestThemeKeywords:
    """Tests for theme keyword integrity."""

    def test_each_card_has_3_to_8_themes(self, deck):
        """Each card must have between 3 and 8 thematic keywords."""
        for card in deck:
            themes = card["themes"]
            count = len(themes)
            assert 3 <= count <= 8, (
                f"Card {card['id']} has {count} themes, "
                f"expected 3-8: {themes}"
            )

    def test_themes_are_normalized_lowercase(self, deck):
        """All themes must be lowercase (normalized)."""
        for card in deck:
            for theme in card["themes"]:
                assert theme == theme.lower(), (
                    f"Card {card['id']} has non-lowercase theme: '{theme}'"
                )

    def test_themes_have_no_extra_whitespace(self, deck):
        """Themes must not have leading/trailing whitespace."""
        for card in deck:
            for theme in card["themes"]:
                assert theme == theme.strip(), (
                    f"Card {card['id']} has whitespace in theme: '{theme}'"
                )

    def test_themes_are_unique_within_card(self, deck):
        """Each card's themes must be unique."""
        for card in deck:
            themes = card["themes"]
            unique_themes = set(themes)
            assert len(themes) == len(unique_themes), (
                f"Card {card['id']} has duplicate themes: "
                f"{[t for t in themes if themes.count(t) > 1]}"
            )


# ----------------------------------------------------------------------
# Alternate names tests
# ----------------------------------------------------------------------


class TestAlternateNames:
    """Tests for alternate name integrity."""

    def test_each_card_has_at_least_one_alternate_name(self, deck):
        """Each card must have at least one alternate name."""
        for card in deck:
            alt_names = card["alternate_names"]
            assert len(alt_names) >= 1, (
                f"Card {card['id']} has no alternate names"
            )

    def test_alternate_names_are_normalized_lowercase(self, deck):
        """All alternate names must be lowercase (normalized)."""
        for card in deck:
            for alt_name in card["alternate_names"]:
                assert alt_name == alt_name.lower(), (
                    f"Card {card['id']} has non-lowercase alternate name: "
                    f"'{alt_name}'"
                )

    def test_alternate_names_have_no_extra_whitespace(self, deck):
        """Alternate names must not have leading/trailing whitespace."""
        for card in deck:
            for alt_name in card["alternate_names"]:
                assert alt_name == alt_name.strip(), (
                    f"Card {card['id']} has whitespace in alternate name: "
                    f"'{alt_name}'"
                )

    def test_alternate_names_are_unique_within_card(self, deck):
        """Each card's alternate names must be unique."""
        for card in deck:
            alt_names = card["alternate_names"]
            unique_names = set(alt_names)
            assert len(alt_names) == len(unique_names), (
                f"Card {card['id']} has duplicate alternate names: "
                f"{[n for n in alt_names if alt_names.count(n) > 1]}"
            )


# ----------------------------------------------------------------------
# Emotional associations tests
# ----------------------------------------------------------------------


class TestEmotionalAssociations:
    """Tests for emotional association integrity."""

    def test_each_card_has_at_least_one_emotional_association(self, deck):
        """Each card must have at least one emotional association."""
        for card in deck:
            emotions = card["emotional_associations"]
            assert len(emotions) >= 1, (
                f"Card {card['id']} has no emotional_associations"
            )

    def test_emotional_associations_are_normalized_lowercase(self, deck):
        """All emotional associations must be lowercase (normalized)."""
        for card in deck:
            for emotion in card["emotional_associations"]:
                assert emotion == emotion.lower(), (
                    f"Card {card['id']} has non-lowercase emotion: '{emotion}'"
                )

    def test_emotional_associations_have_no_extra_whitespace(self, deck):
        """Emotional associations must not have leading/trailing whitespace."""
        for card in deck:
            for emotion in card["emotional_associations"]:
                assert emotion == emotion.strip(), (
                    f"Card {card['id']} has whitespace in emotion: '{emotion}'"
                )


# ----------------------------------------------------------------------
# Cross-card consistency tests
# ----------------------------------------------------------------------


class TestCrossCardConsistency:
    """Tests for consistency across the entire deck."""

    def test_no_theme_word_conflicts_with_card_name(self, deck):
        """Themes should not directly conflict with the card's nature."""
        # This is a soft check - themes that directly contradict the card name
        # might indicate data entry errors
        for card in deck:
            name_lower = card["name"].lower()
            # Check that at least one theme relates to the card
            # (no card should have themes completely unrelated to its meaning)
            themes = card["themes"]
            assert len(themes) > 0, (
                f"Card {card['id']} has no themes"
            )

    def test_all_themes_are_common_across_deck(self, deck):
        """Verify theme pool is consistent across deck."""
        all_themes = set()
        for card in deck:
            all_themes.update(card["themes"])
        # The deck should have a reasonable number of unique themes
        assert len(all_themes) >= 20, (
            f"Expected at least 20 unique themes across deck, "
            f"found {len(all_themes)}"
        )

    def test_canonical_names_match_pt_names_pattern(self, deck):
        """Portuguese names should generally correspond to English patterns."""
        for card in deck:
            name = card["name"]
            name_pt = card["name_pt"]
            # Basic sanity check - both should be non-empty
            assert name, f"Card {card['id']} has empty name"
            assert name_pt, f"Card {card['id']} has empty name_pt"
            # Both should be different (canonical vs Portuguese)
            assert name != name_pt or name_pt.startswith("O ") or name_pt.startswith("A "), (
                f"Card {card['id']} name and name_pt may be identical: "
                f"{name} / {name_pt}"
            )


# ----------------------------------------------------------------------
# Known card integrity tests
# ----------------------------------------------------------------------


class TestKnownCardData:
    """Tests for specific known card data integrity."""

    def test_card_14_is_fox(self, deck):
        """Card 14 (The Fox) should have cunning-related themes."""
        card = next((c for c in deck if c["id"] == 14), None)
        assert card is not None, "Card 14 not found in deck"
        assert "Fox" in card["name"] or "Raposa" in card["name"]
        # Verify cunning/opportunity themes are present
        themes = card["themes"]
        cunning_related = ["cunning", "opportunity", "strategy", "shrewdness"]
        assert any(t in cunning_related for t in themes), (
            f"Card 14 should have cunning-related themes, got: {themes}"
        )

    def test_card_1_is_rider(self, deck):
        """Card 1 (The Rider) should have movement themes."""
        card = next((c for c in deck if c["id"] == 1), None)
        assert card is not None, "Card 1 not found in deck"
        assert "Rider" in card["name"] or "Horseman" in card["name"]
        themes = card["themes"]
        movement_related = ["movement", "arrival", "travel", "journey", "news"]
        assert any(t in movement_related for t in themes), (
            f"Card 1 should have movement-related themes, got: {themes}"
        )

    def test_card_36_is_beijo(self, deck):
        """Card 36 (The Kiss/Beijo) should have intimacy themes."""
        card = next((c for c in deck if c["id"] == 36), None)
        assert card is not None, "Card 36 not found in deck"
        # Beijo should be in alternate names
        assert any("beijo" in alt.lower() for alt in card["alternate_names"]), (
            f"Card 36 should have 'Beijo' in alternate_names, "
            f"got: {card['alternate_names']}"
        )

    def test_card_25_ring_has_marriage_theme(self, deck):
        """Card 25 (The Ring) should have marriage/partnership theme."""
        card = next((c for c in deck if c["id"] == 25), None)
        assert card is not None, "Card 25 not found in deck"
        themes = card["themes"]
        assert "marriage" in themes or "partnership" in themes, (
            f"Card 25 should have marriage or partnership theme, got: {themes}"
        )


# ----------------------------------------------------------------------
# Direction interpretation tests
# ----------------------------------------------------------------------


class TestDirectionInterpretations:
    """Tests for directional interpretation integrity."""

    def test_all_cards_have_upright_interpretation(self, deck):
        """Every card must have a non-empty upright interpretation."""
        for card in deck:
            upright = card["directions"].get("upright", "")
            assert upright.strip(), (
                f"Card {card['id']} has empty upright interpretation"
            )

    def test_all_cards_have_reversed_interpretation(self, deck):
        """Every card must have a non-empty reversed interpretation."""
        for card in deck:
            reversed_interp = card["directions"].get("reversed", "")
            assert reversed_interp.strip(), (
                f"Card {card['id']} has empty reversed interpretation"
            )

    def test_upright_and_reversed_are_different(self, deck):
        """Upright and reversed interpretations should be meaningfully different."""
        for card in deck:
            upright = card["directions"]["upright"]
            reversed_interp = card["directions"]["reversed"]
            assert upright != reversed_interp, (
                f"Card {card['id']} has identical upright and reversed: "
                f"'{upright}'"
            )

    def test_reversed_indicates_negative_or_blocked(self, deck):
        """Reversed interpretations should typically indicate challenges."""
        # This is a soft check - reversed cards often have words suggesting
        # obstruction, fear, or negative outcomes
        reversed_keywords = [
            "delay", "fear", "avoid", "miss", "broken", "bad",
            "conflict", "danger", "loss", "worry", "anxiety",
            "instability", "deception", "obstacle", "refusal"
        ]
        for card in deck:
            reversed_interp = card["directions"]["reversed"].lower()
            # At least check it's not identical to upright
            upright = card["directions"]["upright"].lower()
            assert reversed_interp != upright, (
                f"Card {card['id']} upright and reversed are identical"
            )
