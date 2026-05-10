# coding: utf-8
"""Main analyzer module integrating all Clareza components."""

import re
from typing import Any

from clareza.card_mapper import CardMapper
from clareza.emotion_classifier import EmotionClassifier
from clareza.tokenizer import PortugueseTokenizer


class IntentDetector:
    """Detector for identifying user intent and primary questions.

    Extracts the primary question from user input and classifies intent type.
    """

    # Question patterns for Portuguese
    QUESTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
        ("career", re.compile(r"\b(devo|deveria|posso|consigo|vou|devo\s+mudar|vou\s+mudar|mudar\s+emprego|emprego|trabalho|carreira|profissao|profissão)\b", re.IGNORECASE)),
        ("relationship", re.compile(r"\b(amo|amo|amor|relacao|relação|namorado|namorada|marido|esposa|parceiro|parceira|sinto\s+falta|saudade|jealous|ciumes|traido|traída|terminei)\b", re.IGNORECASE)),
        ("health", re.compile(r"\b(saude|saúde|doente|doença|dor|medicamento|medico|médico|hospital|tratamento|ansiedade|depressao|depressão)\b", re.IGNORECASE)),
        ("finance", re.compile(r"\b(dinheiro|dinheiro|financeiro|investimento|poupar|economia|divida|dívida|debito|débito|conta|fatura|salario|salário)\b", re.IGNORECASE)),
        ("future", re.compile(r"\b(futuro|amanha|amanhã|decisao|decisão|escolha|planejar|planeamento|planejamento|incerto|inseguro)\b", re.IGNORECASE)),
        ("question_word", re.compile(r"\b(o\s+que|que|quem|onde|quando|por\s+que|como|qual|quais|se\s+devo|se\s+deveria|se\s+posso)\b", re.IGNORECASE)),
    ]

    def detect_intent(self, text: str) -> dict[str, Any]:
        """Detect intent and extract primary question from text.

        Args:
            text: Input text to analyze.

        Returns:
            Dictionary containing:
            - intent: The primary intent category
            - primary_question: The main question in the text
            - has_question: Whether text contains a question
        """
        if not text or not text.strip():
            return {
                "intent": "unknown",
                "primary_question": "",
                "has_question": False,
            }

        has_question = self._has_question(text)
        primary_question = self._extract_primary_question(text)
        intent = self._classify_intent(text, primary_question)

        return {
            "intent": intent,
            "primary_question": primary_question,
            "has_question": has_question,
        }

    def _has_question(self, text: str) -> bool:
        """Check if text contains a question.

        Args:
            text: Input text to check.

        Returns:
            True if text contains a question.
        """
        # Check for question mark
        if "?" in text:
            return True

        # Check for question words
        question_words = r"\b(devo|deveria|posso|posso|o\s+que|que|quem|onde|quando|por\s+que|como|qual|quais)\b"
        return bool(re.search(question_words, text, re.IGNORECASE))

    def _extract_primary_question(self, text: str) -> str:
        """Extract the primary question from text.

        Args:
            text: Input text to extract question from.

        Returns:
            The primary question string, or empty string if no question found.
        """
        # Find the first sentence ending with "?" or containing question words
        sentences = re.split(r"[.!?]", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if sentence ends with "?" or starts with question word
            if sentence.endswith("?"):
                return sentence.strip()

            question_starters = r"^(devo|deveria|posso|consigo|o\s+que|que|quem|onde|quando|por\s+que|como|qual|quais|se\s+devo|se\s+deveria)\s"
            if re.match(question_starters, sentence, re.IGNORECASE):
                return sentence.strip()

        return ""

    def _classify_intent(self, text: str, primary_question: str) -> str:
        """Classify the intent category of the text.

        Args:
            text: Input text to classify.
            primary_question: The primary question extracted.

        Returns:
            The intent category string.
        """
        text_to_check = f"{text} {primary_question}".lower()

        for intent, pattern in self.QUESTION_PATTERNS:
            if pattern.search(text_to_check):
                return intent

        return "general"


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
        self._intent_detector = IntentDetector()

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
            - intent: Detected intent category
            - primary_question: The primary question in the text
            - has_question: Whether the text contains a question
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

        # Detect intent
        intent_result = self._intent_detector.detect_intent(text)
        intent = intent_result["intent"]
        primary_question = intent_result["primary_question"]
        has_question = intent_result["has_question"]

        return {
            "card_ids": card_ids,
            "cards": cards,
            "emotion": emotion,
            "emotion_confidence": emotion_confidence,
            "tokens": tokens,
            "normalized_text": normalized_text,
            "intent": intent,
            "primary_question": primary_question,
            "has_question": has_question,
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
            "intent": "unknown",
            "primary_question": "",
            "has_question": False,
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
