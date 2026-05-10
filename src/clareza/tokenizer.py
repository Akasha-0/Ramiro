# coding: utf-8
"""Tokenizer module for Portuguese text normalization."""

import re
from typing import Any


class PortugueseTokenizer:
    """Tokenizer for Portuguese text with normalization.

    Normalizes text by:
    - Converting to lowercase
    - Removing special characters (parentheses, brackets, etc.)
    - Normalizing whitespace
    """

    def __init__(self) -> None:
        """Initialize the tokenizer."""
        self._special_chars_pattern = re.compile(r"[^\w\s]")
        self._whitespace_pattern = re.compile(r"\s+")

    def normalize(self, text: str) -> str:
        """Normalize Portuguese text for analysis.

        Args:
            text: Input text to normalize.

        Returns:
            Normalized text with special characters removed,
            converted to lowercase, and whitespace normalized.
        """
        if not text:
            return ""

        text = text.lower()
        text = self._special_chars_pattern.sub(" ", text)
        text = self._whitespace_pattern.sub(" ", text)
        text = text.strip()

        return text

    def tokenize(self, text: str) -> list[str]:
        """Tokenize normalized text into words.

        Args:
            text: Input text to tokenize.

        Returns:
            List of word tokens from the normalized text.
        """
        normalized = self.normalize(text)
        return normalized.split()
