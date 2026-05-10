"""Gerador de sumários para arcos de reflexão — Sistema de Clareza Simbólico-Estratégica.

Módulo que executa análise multi-sessão em arcos de reflexão:
- theme_frequency: análise de frequência de temas
- card_frequency: análise de frequência de cartas
- pattern_detection: detecta padrões recorrentes entre sessões

Recebe lista de SessionRecord (types.py) e retorna ArcSummary (types.py).
"""

import logging
from collections import Counter
from typing import Optional

from src.types import ArcSummary, SessionRecord

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------

_TOP_N = 3  # Número de top items a retornar


# ----------------------------------------------------------------------
# Gerador de sumários
# ----------------------------------------------------------------------


class ArcSummaryGenerator:
    """Gerador de sumários para arcos de reflexão.

    Executa análise multi-sessão para identificar:
    - Temas predominantes (por frequência)
    - Cartas mais recorrentes (por frequência)
    - Padrões e insights entre sessões

    Attributes:
        top_n: Número de top items a incluir no sumário (default 3).
    """

    def __init__(self, top_n: int = _TOP_N) -> None:
        """Inicializa o gerador de sumários.

        Args:
            top_n: Número de top items a retornar (temas e cartas).
        """
        self.top_n = top_n
        logger.debug("ArcSummaryGenerator inicializado, top_n=%d", top_n)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generate(self, sessions: list[SessionRecord]) -> ArcSummary:
        """Gera sumário completo a partir de uma lista de sessões.

        Args:
            sessions: Lista de SessionRecord representando todas as sessões do arco.

        Returns:
            ArcSummary com análise multi-sessão.
        """
        logger.info("Gerando sumário para %d sessões", len(sessions))

        if not sessions:
            logger.debug("Nenhuma sessão para processar")
            return ArcSummary(
                arc_name="",
                total_sessions=0,
                date_range=None,
                top_themes=[],
                top_cards=[],
                session_ids=[],
            )

        # Extrair nome do arco da primeira sessão (se disponível)
        arc_name = sessions[0].arc_name or ""

        # Análise de temas e cartas
        theme_data = self._analyze_themes(sessions)
        card_data = self._analyze_cards(sessions)

        # Calcular range de datas
        date_range = self._calculate_date_range(sessions)

        # Coletar IDs das sessões
        session_ids = [s.session_id for s in sessions]

        summary = ArcSummary(
            arc_name=arc_name,
            total_sessions=len(sessions),
            date_range=date_range,
            top_themes=theme_data["top_themes"],
            top_cards=card_data["top_cards"],
            session_ids=session_ids,
        )

        logger.info(
            "Sumário gerado: arc=%r, sessions=%d, themes=%s, cards=%s",
            arc_name,
            summary.total_sessions,
            summary.top_themes,
            summary.top_cards,
        )

        return summary

    # ------------------------------------------------------------------
    # Análise de temas
    # ------------------------------------------------------------------

    def _analyze_themes(self, sessions: list[SessionRecord]) -> dict:
        """Analisa frequência de temas através de todas as sessões.

        Args:
            sessions: Lista de sessões a analisar.

        Returns:
            Dicionário com:
                - top_themes: lista dos N temas mais frequentes
                - theme_counts: dict com contagem por tema
                - total_themes: total de temas únicos
        """
        if not sessions:
            return {
                "top_themes": [],
                "theme_counts": {},
                "total_themes": 0,
            }

        # Contar temas
        theme_counts: Counter = Counter()
        for session in sessions:
            for theme in session.themes:
                theme_counts[theme] += 1

        # Obter top N
        top_themes = [theme for theme, _ in theme_counts.most_common(self.top_n)]

        logger.debug("Análise de temas: top=%s, unique=%d", top_themes, len(theme_counts))

        return {
            "top_themes": top_themes,
            "theme_counts": dict(theme_counts),
            "total_themes": len(theme_counts),
        }

    # ------------------------------------------------------------------
    # Análise de cartas
    # ------------------------------------------------------------------

    def _analyze_cards(self, sessions: list[SessionRecord]) -> dict:
        """Analisa frequência de cartas através de todas as sessões.

        Args:
            sessions: Lista de sessões a analisar.

        Returns:
            Dicionário com:
                - top_cards: lista das N cartas mais frequentes
                - card_counts: dict com contagem por carta
                - total_cards: total de cartas únicas
        """
        if not sessions:
            return {
                "top_cards": [],
                "card_counts": {},
                "total_cards": 0,
            }

        # Contar cartas
        card_counts: Counter = Counter()
        for session in sessions:
            for card in session.cards:
                card_counts[card] += 1

        # Obter top N
        top_cards = [card for card, _ in card_counts.most_common(self.top_n)]

        logger.debug("Análise de cartas: top=%s, unique=%d", top_cards, len(card_counts))

        return {
            "top_cards": top_cards,
            "card_counts": dict(card_counts),
            "total_cards": len(card_counts),
        }

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def _calculate_date_range(
        self, sessions: list[SessionRecord]
    ) -> Optional[tuple]:
        """Calcula o range de datas das sessões.

        Args:
            sessions: Lista de sessões.

        Returns:
            Tupla (início, fim) ou None se não houver sessões válidas.
        """
        if not sessions:
            return None

        timestamps = [s.timestamp for s in sessions if s.timestamp]
        if not timestamps:
            return None

        return (min(timestamps), max(timestamps))

    def get_session_summary(self, session: SessionRecord) -> dict:
        """Gera sumário resumido de uma sessão individual.

        Args:
            session: Sessão a resumir.

        Returns:
            Dicionário com informações resumidas da sessão.
        """
        return {
            "session_id": session.session_id,
            "timestamp": session.timestamp.isoformat() if session.timestamp else None,
            "themes": session.themes,
            "cards": session.cards,
            "has_risks": len(session.risks) > 0,
            "risk_count": len(session.risks),
            "decision_count": len(session.decisions),
        }

    def format_themes_summary(self, sessions: list[SessionRecord]) -> str:
        """Formata análise de temas como string legível.

        Args:
            sessions: Lista de sessões.

        Returns:
            String formatada com análise de temas.
        """
        data = self._analyze_themes(sessions)

        if not data["top_themes"]:
            return "Nenhum tema detectado nas sessões."

        lines = ["### Temas Predominantes\n"]
        for i, theme in enumerate(data["top_themes"], 1):
            count = data["theme_counts"].get(theme, 0)
            lines.append(f"{i}. **{theme}** — {count} ocorrência(s)")

        return "\n".join(lines)

    def format_cards_summary(self, sessions: list[SessionRecord]) -> str:
        """Formata análise de cartas como string legível.

        Args:
            sessions: Lista de sessões.

        Returns:
            String formatada com análise de cartas.
        """
        data = self._analyze_cards(sessions)

        if not data["top_cards"]:
            return "Nenhuma carta detectada nas sessões."

        lines = ["### Cartas Mais Recorrentes\n"]
        for i, card in enumerate(data["top_cards"], 1):
            count = data["card_counts"].get(card, 0)
            lines.append(f"{i}. **{card}** — {count} ocorrência(s)")

        return "\n".join(lines)