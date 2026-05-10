"""Card loader module for Baralho Cigano deck data."""

import json
from pathlib import Path
from typing import List, Dict, Any


# Required fields that each card must have
REQUIRED_FIELDS = [
    "id",
    "name",
    "alternate_names",
    "themes",
    "meaning",
    "directions",
    "emotional_associations",
    "contextual_notes",
]

# Fields containing keywords that need normalization
KEYWORD_FIELDS = [
    "themes",
    "alternate_names",
    "emotional_associations",
]


def get_data_path() -> Path:
    """Get the path to the cigano_deck.json data file.

    Returns:
        Path to the data file.
    """
    return Path(__file__).parent.parent / "data" / "cigano_deck.json"


def validate_card_fields(card: Dict[str, Any], card_index: int) -> None:
    """Validate that a card has all required fields.

    Args:
        card: The card dictionary to validate.
        card_index: The index of the card (for error messages).

    Raises:
        ValueError: If any required field is missing from the card.
    """
    for field in REQUIRED_FIELDS:
        if field not in card:
            raise ValueError(
                f"Card at index {card_index} missing required field: '{field}'"
            )


def validate_deck(deck: List[Dict[str, Any]]) -> None:
    """Validate that the deck contains all required fields for each card.

    Args:
        deck: The loaded deck data.

    Raises:
        ValueError: If any card is missing required fields.
    """
    for index, card in enumerate(deck):
        if not isinstance(card, dict):
            raise ValueError(f"Card at index {index} is not a dictionary")
        validate_card_fields(card, index)


def normalize_card_keywords(card: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize keyword fields in a card to lowercase and stripped.

    Args:
        card: The card dictionary to normalize.

    Returns:
        A new card dictionary with normalized keyword fields.
    """
    normalized = card.copy()
    for field in KEYWORD_FIELDS:
        if field in card and isinstance(card[field], list):
            normalized[field] = [keyword.lower().strip() for keyword in card[field]]
    return normalized


def normalize_deck_keywords(deck: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize keyword fields in all cards of the deck.

    Args:
        deck: The list of card dictionaries to normalize.

    Returns:
        A new list of card dictionaries with normalized keyword fields.
    """
    return [normalize_card_keywords(card) for card in deck]


def load_deck() -> List[Dict[str, Any]]:
    """Load the Baralho Cigano deck from JSON data file.

    Returns:
        List of card dictionaries containing all 36 cards with their data.

    Raises:
        FileNotFoundError: If the deck data file does not exist.
        json.JSONDecodeError: If the deck data file contains invalid JSON.
        ValueError: If the deck data is not a valid list of cards or has missing required fields.
    """
    data_path = get_data_path()

    if not data_path.exists():
        raise FileNotFoundError(f"Deck data file not found: {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        deck = json.load(f)

    if not isinstance(deck, list):
        raise ValueError("Deck data must be a list of cards")

    if len(deck) != 36:
        raise ValueError(f"Expected 36 cards, got {len(deck)}")

    validate_deck(deck)

    return normalize_deck_keywords(deck)