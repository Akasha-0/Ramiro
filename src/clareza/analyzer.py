# coding: utf-8
"""Main analyzer module integrating all Clareza components."""

from typing import Any

from clareza.card_mapper import CardMapper
from clareza.emotion_classifier import EmotionClassifier
from clareza.tokenizer import PortugueseTokenizer


class TextAnalyzer:
    """Main analyzer for Clareza Baralho Cigano text analysis.

    Integrates tokenizer, card mapper, and emotion classifier to provide
    comprehensive analysis of user text input.

    Features:
    - Text normalization and tokenization
    - Card reference detection (by name, keyword, theme)
    - Emotion classification with confidence scoring
    - Combined analysis result
    """

    def __init__(self) -> None:
        """Initialize the analyzer with all components."""
        self._tokenizer = PortugueseTokenizer()
        self._card_mapper = CardMapper()
        self._emotion_classifier = EmotionClassifier()

    def analyze(self, text: str) -> dict[str, Any]:
        """Analyze input text for card references and emotional state.

        Args:
            text: Input text to analyze.

        Returns:
            Dictionary containing:
            - card_ids: List of detected card IDs
            - cards: List of card dictionaries found in text
            - emotion: Dominant emotion category
            - emotion_confidence: Confidence score for emotion classification
            - tokens: List of tokenized words from normalized text
            - normalized_text: Normalized version of input text
        """
        if not text or not text.strip():
            return self._empty_result()

        # Tokenize and normalize text
        normalized_text = self._tokenizer.normalize(text)
        tokens = self._tokenizer.tokenize(text)

        # Find card references
        cards = self._card_mapper.find_cards(text)
        card_ids = [card["id"] for card in cards]

        # Classify emotion
        emotion_result = self._emotion_classifier.classify_with_confidence(text)
        emotion = emotion_result["emotion"]
        emotion_confidence = emotion_result["confidence"]

        return {
            "card_ids": card_ids,
            "cards": cards,
            "emotion": emotion,
            "emotion_confidence": emotion_confidence,
            "tokens": tokens,
            "normalized_text": normalized_text,
        }

    def _empty_result(self) -> dict[str, Any]:
        """Return empty result for invalid input.

        Returns:
            Dictionary with empty/default values.
        """
        return {
            "card_ids": [],
            "cards": [],
            "emotion": "uncertain",
            "emotion_confidence": 0.0,
            "tokens": [],
            "normalized_text": "",
        }

    def find_cards(self, text: str) -> list[dict[str, Any]]:
        """Find card references in text.

        Args:
            text: Input text to search for card references.

        Returns:
            List of card dictionaries referenced in the text.
        """
        return self._card_mapper.find_cards(text)

    def classify_emotion(self, text: str) -> dict[str, Any]:
        """Classify emotional state of input text.

        Args:
            text: Input text to analyze for emotional content.

        Returns:
            Dictionary with emotion classification and confidence scores.
        """
        return self._emotion_classifier.classify_with_confidence(text)

    def tokenize(self, text: str) -> list[str]:
        """Tokenize input text.

        Args:
            text: Input text to tokenize.

        Returns:
            List of word tokens from normalized text.
        """
        return self._tokenizer.tokenize(text)

    def normalize(self, text: str) -> str:
        """Normalize input text.

        Args:
            text: Input text to normalize.

        Returns:
            Normalized text string.
        """
        return self._tokenizer.normalize(text)
