# coding: utf-8
"""Data structures for session analysis in Clareza."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CardAnalysis:
    """Analysis result for a single card.

    Attributes:
        card_id: The numeric ID of the card (1-36).
        name: The name of the card.
        keywords: List of keywords associated with the card.
        meaning: The meaning of the card.
        direction: Card direction ('upright' or 'reversed').
        relevance: Relevance score to the question (0.0 to 1.0).
        themes: List of themes associated with this card.
    """

    card_id: int
    name: str
    keywords: list[str]
    meaning: str
    direction: str = "upright"
    relevance: float = 0.5
    themes: list[str] = field(default_factory=list)

    def is_reversed(self) -> bool:
        """Check if the card is in reversed position.

        Returns:
            True if the card is reversed, False otherwise.
        """
        return self.direction.lower() == "reversed"


@dataclass
class SessionAnalysis:
    """Complete analysis of a reading session.

    Attributes:
        cards: List of analyzed cards in the session.
        themes: Aggregated themes from all cards in the session.
        primary_question: The main question asked by the user.
        session_summary: Optional summary of the session.
    """

    cards: list[CardAnalysis]
    themes: list[str] = field(default_factory=list)
    primary_question: str = ""
    session_summary: Optional[str] = None

    def get_card_count(self) -> int:
        """Get the number of cards in the session.

        Returns:
            The number of cards.
        """
        return len(self.cards)

    def get_dominant_theme(self) -> Optional[str]:
        """Find the most frequent theme across all cards.

        Returns:
            The most common theme, or None if no cards.
        """
        if not self.themes:
            return None
        theme_counts: dict[str, int] = {}
        for theme in self.themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        return max(theme_counts, key=theme_counts.get)

    def get_relevant_cards(self, threshold: float = 0.5) -> list[CardAnalysis]:
        """Get cards with relevance above a threshold.

        Args:
            threshold: Minimum relevance score (0.0 to 1.0).

        Returns:
            List of cards meeting the relevance threshold.
        """
        return [card for card in self.cards if card.relevance >= threshold]
