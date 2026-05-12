# coding: utf-8
"""Emotion classifier module for detecting emotional states in text."""

from typing import Any

try:
    from unidecode import unidecode
except ImportError:
    import unicodedata
    def unidecode(text):
        # Fallback: normalize to NFKD, strip non-ASCII
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


class EmotionClassifier:
    """Classifier for detecting emotional states in Portuguese text.

    Classifies text into four emotion categories:
    - conflicted: Conflicting feelings, indecision, doubt
    - hopeful: Optimism, positive expectations, future-looking
    - fearful: Anxiety, worry, concern about the future
    - uncertain: Lack of clarity, confusion, ambiguity

    Uses keyword-based classification with confidence scoring.
    """

    # Emotion keywords mapped to emotional categories
    EMOTION_KEYWORDS: dict[str, list[str]] = {
        "conflicted": [
            "confuso", "conflito", "indeciso", "contraditorio", "duvida", "dvida",
            "hesitante", "pressionado", "pressionada", "dilema", "embaraçado",
            "desconfiado", "inseguro", "conflituoso", "tenso", "nervoso",
            "ambivalente", "irresoluto", "incert", "hesitar", "tropeçar",
        ],
        "hopeful": [
            "esperanca", "esperança", "espero", "otimista", "confiante",
            "positivo", "melhor", "acredito", "acredito que",
            "motivado", "motivada", "inspirado",
            "inspirada", "feliz", "alegre", "entusiamo", "entusiasmo",
            "promissor", "promissora", "vai dar certo", "vai funcionar",
            "conseguirei", "positivo", "progresso",
        ],
        "fearful": [
            "medo", "assustado", "assustada", "ansioso", "ansiosa", "preocupado",
            "preocupada", "nervoso", "nervosa", "inseguro", "insegura",
            "pavor", "terror", "horror", "temor", "receio", "susto",
            "afraid", "worried", "scared", "nervous", "anxious",
            "phobia", "paranoid", "panico", "pânico", "stress", "estress",
            "ruim", "pior", "falhar", "falhar", "fracasso", "perder",
            "negativo", "ruim", "difícil", "dificil", "impossível",
        ],
        "uncertain": [
            "nao sei", "não sei", "talvez", "provavelmente",
            "nao tenho certeza", "não tenho certeza", "perdido",
            "sem resposta", "nao entendo", "não entendo", "nao compreendo",
            "não compreendo", "incerto", "incerta", "questiono", "questiona",
            "desconhecido", "nao familiar", "não familiar",
            "misterio", "mistério", "imprevisto", "nao sei o que fazer",
        ],
    }

    def __init__(self) -> None:
        """Initialize the emotion classifier."""
        self._keyword_scores: dict[str, dict[str, float]] = self._build_keyword_scores()

    def _build_keyword_scores(self) -> dict[str, dict[str, float]]:
        """Build keyword scores for each emotion category.

        Returns:
            Dictionary mapping emotions to keyword scores.
        """
        scores: dict[str, dict[str, float]] = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            scores[emotion] = {}
            for keyword in keywords:
                # Shorter keywords get slightly higher weight
                weight = 1.0 / (1 + len(keyword) * 0.05)
                scores[emotion][keyword] = weight
        return scores

    def _normalize_text(self, text: str) -> str:
        """Normalize text for emotion analysis.

        Args:
            text: Input text to normalize.

        Returns:
            Normalized lowercase text with accents stripped for keyword matching.
        """
        import re
        text = text.lower()
        # Strip accents so "dúvida" matches "duvida"
        text = unidecode(text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _score_emotion(self, text: str, emotion: str) -> float:
        """Calculate emotion score for a given category.

        Args:
            text: Input text to analyze.
            emotion: Emotion category to score.

        Returns:
            Score indicating how strongly this emotion is present.
        """
        normalized = self._normalize_text(text)
        keywords = self._keyword_scores.get(emotion, {})

        total_score = 0.0
        for keyword, weight in keywords.items():
            if keyword in normalized:
                total_score += weight

        return total_score

    def classify(self, text: str) -> str:
        """Classify the emotional state of the input text.

        Args:
            text: Input text to analyze for emotional content.

        Returns:
            The dominant emotion category: conflicted, hopeful,
            fearful, or uncertain.
        """
        if not text or not text.strip():
            return "uncertain"

        # Calculate scores for each emotion
        scores: dict[str, float] = {}
        for emotion in self.EMOTION_KEYWORDS.keys():
            scores[emotion] = self._score_emotion(text, emotion)

        # Find the emotion with highest score
        if max(scores.values()) > 0:
            dominant = max(scores, key=scores.get)  # type: ignore
            return dominant

        return "uncertain"

    def classify_with_confidence(self, text: str) -> dict[str, Any]:
        """Classify emotion with confidence scores.

        Args:
            text: Input text to analyze for emotional content.

        Returns:
            Dictionary with emotion classification and confidence scores.
        """
        if not text or not text.strip():
            return {
                "emotion": "uncertain",
                "confidence": 0.0,
                "scores": {},
            }

        # Calculate scores for each emotion
        scores: dict[str, float] = {}
        for emotion in self.EMOTION_KEYWORDS.keys():
            scores[emotion] = self._score_emotion(text, emotion)

        # Calculate total and confidence
        total_score = sum(scores.values())
        if total_score > 0:
            confidence = max(scores.values()) / total_score
            dominant = max(scores, key=scores.get)  # type: ignore
        else:
            confidence = 0.0
            dominant = "uncertain"

        return {
            "emotion": dominant,
            "confidence": round(confidence, 2),
            "scores": {k: round(v, 3) for k, v in scores.items()},
        }