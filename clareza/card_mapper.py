# coding: utf-8
"""Card mapper module for detecting card references in text."""

import json
import re
from pathlib import Path
from typing import Any


class CardMapper:
    """Mapper for detecting card references in Portuguese text.

    Detects references to Baralho Cigano cards through:
    - Numeric patterns (e.g., "carta 3", "numero 7")
    - Card name mentions
    - Keyword matches
    - Theme aliases (semantic mappings for related concepts)
    """

    CARD_NUMBER_PATTERN = re.compile(
        r"\b(carta|numero|num\s?|card|n)\s*(\d+)\b", re.IGNORECASE
    )

    # Theme aliases: maps common terms to card IDs based on thematic association
    THEME_ALIASES: dict[str, list[int]] = {
        "amor": [6, 27],
        "casamento": [11],
        "casar": [11],
        "casada": [11],
        "casado": [11],
        "uniao": [6],
        "união": [6],
        "caminho": [3, 11],
    }

    def __init__(self) -> None:
        """Initialize the card mapper with cards data."""
        self._cards: list[dict[str, Any]] = self._load_cards()
        self._name_lookup: dict[str, int] = self._build_name_lookup()
        self._keyword_lookup: dict[str, list[int]] = self._build_keyword_lookup()
        self._theme_lookup: dict[str, list[int]] = self._build_theme_lookup()

    def _load_cards(self) -> list[dict[str, Any]]:
        """Load cards data from JSON file.

        Returns:
            List of card dictionaries.
        """
        cards_path = Path(__file__).parent / "data" / "cards.json"
        with open(cards_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_name_lookup(self) -> dict[str, int]:
        """Build a lookup map from card name words to card IDs.

        Returns:
            Dictionary mapping lowercase name words to card IDs.
        """
        lookup: dict[str, int] = {}
        for card in self._cards:
            name = card["name"].lower()
            # Add full name
            lookup[name] = card["id"]
            # Add individual words from name
            words = name.split()
            for word in words:
                if word not in lookup:
                    lookup[word] = card["id"]
        return lookup

    def _build_keyword_lookup(self) -> dict[str, list[int]]:
        """Build a lookup map from keywords to card IDs.

        Returns:
            Dictionary mapping lowercase keywords to lists of card IDs.
        """
        lookup: dict[str, list[int]] = {}
        for card in self._cards:
            for keyword in card["keywords"]:
                key = keyword.lower()
                if key not in lookup:
                    lookup[key] = []
                lookup[key].append(card["id"])
        return lookup

    def _build_theme_lookup(self) -> dict[str, list[int]]:
        """Build theme lookup from THEME_ALIASES.

        Returns:
            Dictionary mapping lowercase theme aliases to card IDs.
        """
        lookup: dict[str, list[int]] = {}
        for key, card_ids in self.THEME_ALIASES.items():
            lookup[key.lower()] = card_ids
        return lookup

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching.

        Args:
            text: Input text to normalize.

        Returns:
            Normalized lowercase text with special chars removed.
        """
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_card_numbers(self, text: str) -> list[int]:
        """Extract card numbers from text patterns like "carta 3".

        Args:
            text: Input text to search.

        Returns:
            List of extracted card IDs.
        """
        found_ids: set[int] = set()
        normalized = self._normalize_text(text)

        for match in self.CARD_NUMBER_PATTERN.finditer(normalized):
            card_num = int(match.group(2))
            # Validate card number is in valid range (1-36)
            if 1 <= card_num <= 36:
                found_ids.add(card_num)

        return list(found_ids)

    def _find_by_name(self, text: str) -> list[int]:
        """Find card IDs by matching card names in text.

        Args:
            text: Input text to search.

        Returns:
            List of matching card IDs.
        """
        found_ids: set[int] = set()
        normalized = self._normalize_text(text)
        words = normalized.split()

        # Check full text segments against names
        for card in self._cards:
            name_lower = card["name"].lower()
            if name_lower in normalized:
                found_ids.add(card["id"])

        # Check individual words against name lookup
        for word in words:
            if word in self._name_lookup:
                found_ids.add(self._name_lookup[word])

        return list(found_ids)

    def _find_by_keywords(self, text: str) -> list[int]:
        """Find card IDs by matching keywords in text.

        Args:
            text: Input text to search.

        Returns:
            List of matching card IDs.
        """
        found_ids: set[int] = set()
        normalized = self._normalize_text(text)
        words = set(normalized.split())

        # Check each word against keyword lookup
        for word in words:
            if word in self._keyword_lookup:
                for card_id in self._keyword_lookup[word]:
                    found_ids.add(card_id)

        return list(found_ids)

    def _find_by_theme(self, text: str) -> list[int]:
        """Find card IDs by matching theme aliases in text.

        Args:
            text: Input text to search.

        Returns:
            List of matching card IDs.
        """
        found_ids: set[int] = set()
        normalized = self._normalize_text(text)
        words = set(normalized.split())

        # Check each word against theme lookup
        for word in words:
            if word in self._theme_lookup:
                for card_id in self._theme_lookup[word]:
                    found_ids.add(card_id)

        return list(found_ids)

    def find_cards(self, text: str) -> list[dict[str, Any]]:
        """Find all card references in text.

        Args:
            text: Input text to analyze for card references.

        Returns:
            List of card dictionaries that were referenced in the text.
        """
        if not text or not isinstance(text, str):
            return []

        # Reject negative card references before normalization strips the minus
        if re.search(r"(carta|numero|num|card|n)\s*-\s*\d+", text, re.IGNORECASE):
            return []

        # Collect all found card IDs
        all_ids: set[int] = set()

        # Try each matching strategy
        for card_id in self._extract_card_numbers(text):
            all_ids.add(card_id)

        for card_id in self._find_by_name(text):
            all_ids.add(card_id)

        for card_id in self._find_by_keywords(text):
            all_ids.add(card_id)

        for card_id in self._find_by_theme(text):
            all_ids.add(card_id)

        # Build result list in ID order
        result: list[dict[str, Any]] = []
        for card in self._cards:
            if card["id"] in all_ids:
                result.append(card)

        return result
