"""Gerador de relatórios Markdown para arcos de reflexão.

Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por transformar o resultado da análise multi-sessão
(ArcSummary) em um relatório estruturado em Markdown com seções fixas:
1. Resumo do Arco
2. Métricas
3. Temas Predominantes
4. Cartas Mais Recorrentes
5. Período de Reflexão

Recebe ArcSummary (types.py) e retorna string com relatório em Markdown.
"""

import logging
from datetime import datetime
from typing import Optional

from src.types import ArcSummary

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Template de relatório de arco com seções fixas
# ----------------------------------------------------------------------

ARC_REPORT_TEMPLATE = """# Relatório de Arco de Reflexão — {arc_name}

## Resumo do Arco
{arc_summary}

## Métricas
{metrics}

## Temas Predominantes
{top_themes}

## Cartas Mais Recorrentes
{top_cards}

## Período de Reflexão
{date_range}

---
*Relatório gerado por Sistema de Clareza Simbólico-Estratégica v0.0.1 — use como ferramenta de reflexão, não como previsão determinista.*
"""


# ----------------------------------------------------------------------
# Gerador de relatórios de arco
# ----------------------------------------------------------------------


class ArcReportGenerator:
    """Gerador de relatórios Markdown para arcos de reflexão.

    Transforma o resultado da análise multi-sessão (ArcSummary)
    em um relatório legível com seções obrigatórias.

    Attributes:
        include_timestamp: Se True, inclui timestamp no relatório (default True).
    """

    def __init__(self, include_timestamp: bool = True) -> None:
        self.include_timestamp = include_timestamp
        logger.debug("ArcReportGenerator inicializado, timestamp=%s", include_timestamp)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generate(
        self,
        summary: ArcSummary,
        disclaimer: Optional[str] = None,
    ) -> str:
        """Gera relatório Markdown a partir do sumário do arco.

        Args:
            summary: ArcSummary com métricas, temas e cartas do arco.
            disclaimer: Texto adicional a ser inserido antes do rodapé (opcional).

        Returns:
            String com relatório completo em Markdown.
        """
        logger.info(
            "Gerando relatório de arco %r com %d sessões",
            summary.arc_name,
            summary.total_sessions,
        )

        # Montar campos do template
        arc_summary = self._format_arc_summary(summary)
        metrics = self._format_metrics(summary)
        top_themes = self._format_top_themes(summary)
        top_cards = self._format_top_cards(summary)
        date_range = self._format_date_range(summary)

        # Preencher template
        report = ARC_REPORT_TEMPLATE.format(
            arc_name=summary.arc_name or "Arco sem nome",
            arc_summary=arc_summary,
            metrics=metrics,
            top_themes=top_themes,
            top_cards=top_cards,
            date_range=date_range,
        )

        # Inserir disclaimer adicional se fornecido
        if disclaimer:
            report = report.rstrip() + "\n\n" + disclaimer + "\n"

        logger.info("Relatório de arco gerado com %d caracteres", len(report))
        return report

    def generate_summary_report(self, summary: ArcSummary) -> str:
        """Gera versão resumida do relatório de arco.

        Args:
            summary: ArcSummary com métricas do arco.

        Returns:
            String com relatório resumido em Markdown.
        """
        return self.generate(summary)

    # ------------------------------------------------------------------
    # Formatadores por seção
    # ------------------------------------------------------------------

    def _format_arc_summary(self, summary: ArcSummary) -> str:
        """Formata a seção de Resumo do Arco.

        Args:
            summary: Sumário do arco.

        Returns:
            String formatada com o resumo.
        """
        if not summary.arc_name:
            return "*Arco sem nome definido.*"

        lines = [
            f"Este arco de reflexão, **{summary.arc_name}**, "
            f"contém {summary.total_sessions} sessão(ões) de análise.",
        ]

        if summary.date_range:
            start, end = summary.date_range
            start_str = start.strftime("%d/%m/%Y")
            end_str = end.strftime("%d/%m/%Y")
            lines.append(
                f"O período de acompanhamento vai de {start_str} a {end_str}."
            )

        if summary.top_themes:
            themes_str = ", ".join(f"*{t}*" for t in summary.top_themes[:3])
            lines.append(f"Temas predominantes: {themes_str}.")

        if summary.top_cards:
            cards_str = ", ".join(f"*{c}*" for c in summary.top_cards[:3])
            lines.append(f"Cartas mais recorrentes: {cards_str}.")

        return "\n".join(lines)

    def _format_metrics(self, summary: ArcSummary) -> str:
        """Formata a seção de Métricas.

        Args:
            summary: Sumário do arco.

        Returns:
            String formatada com as métricas.
        """
        lines = [
            f"- **Total de sessões**: {summary.total_sessions}",
            f"- **Temas únicos detectados**: {len(set(t for s in [summary] for t in summary.top_themes)) or len(summary.top_themes)}",
            f"- **Cartas únicas usadas**: {len(set(c for s in [summary] for c in summary.top_cards)) or len(summary.top_cards)}",
            f"- **IDs de sessão registrados**: {len(summary.session_ids)}",
        ]
        return "\n".join(lines)

    def _format_top_themes(self, summary: ArcSummary) -> str:
        """Formata a seção de Temas Predominantes.

        Args:
            summary: Sumário do arco.

        Returns:
            String formatada com os temas.
        """
        if not summary.top_themes:
            return "*Nenhum tema predominante identificado nas sessões.*"

        lines = []
        for i, theme in enumerate(summary.top_themes[:3], start=1):
            lines.append(f"{i}. **{theme}**")
        return "\n".join(lines)

    def _format_top_cards(self, summary: ArcSummary) -> str:
        """Formata a seção de Cartas Mais Recorrentes.

        Args:
            summary: Sumário do arco.

        Returns:
            String formatada com as cartas.
        """
        if not summary.top_cards:
            return "*Nenhuma carta recorrente identificada nas sessões.*"

        lines = []
        for i, card in enumerate(summary.top_cards[:3], start=1):
            lines.append(f"{i}. **{card}**")
        return "\n".join(lines)

    def _format_date_range(self, summary: ArcSummary) -> str:
        """Formata a seção de Período de Reflexão.

        Args:
            summary: Sumário do arco.

        Returns:
            String formatada com o período.
        """
        if not summary.date_range:
            return "*Período não disponível — nenhuma sessão com timestamp registrado.*"

        start, end = summary.date_range
        start_str = start.strftime("%d/%m/%Y às %H:%M")
        end_str = end.strftime("%d/%m/%Y às %H:%M")

        return f"""- **Início**: {start_str}
- **Fim**: {end_str}
- **Duração**: {(end - start).days} dia(s)"""

    # ------------------------------------------------------------------
    # Utilitários de formatação
    # ------------------------------------------------------------------

    @staticmethod
    def bold(text: str) -> str:
        """Aplica negrito Markdown a um texto.

        Args:
            text: Texto a formatar.

        Returns:
            Texto envolvido em **bold**.
        """
        return f"**{text}**"

    @staticmethod
    def italic(text: str) -> str:
        """Aplica itálico Markdown a um texto.

        Args:
            text: Texto a formatar.

        Returns:
            Texto envolvido em _itálico_.
        """
        return f"_{text}_"