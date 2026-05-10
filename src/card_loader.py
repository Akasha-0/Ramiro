"""Card loader module for Baralho Cigano deck data."""

import json
import os
from pathlib import Path
from typing import List, Dict, Any


def get_data_path() -> Path:
    """Get the path to the cigano_deck.json data file.

    Returns:
        Path to the data file.
    """
    return Path(__file__).parent.parent / "data" / "cigano_deck.json"


def load_deck() -> List[Dict[str, Any]]:
    """Load the Baralho Cigano deck from JSON data file.

    Returns:
        List of card dictionaries containing all 36 cards with their data.

    Raises:
        FileNotFoundError: If the deck data file does not exist.
        json.JSONDecodeError: If the deck data file contains invalid JSON.
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

    return deck