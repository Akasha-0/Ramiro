"""Gerador de relatórios Markdown — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por transformar o resultado da análise (AnalysisResult)
em um relatório estruturado em Markdown com 5 seções fixas:
1. Diagnóstico
2. Interpretação Simbólica
3. Riscos Identificados
4. Caminhos de Decisão
5. Plano Prático

Recebe AnalysisResult (types.py) e retorna string com relatório em Markdown.
"""

import logging
from datetime import datetime
from typing import Optional

from src.types import AnalysisResult

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Template de relatório com 5 seções fixas
# ----------------------------------------------------------------------

REPORT_TEMPLATE = """# Relatório de Análise — {timestamp}

## Diagnóstico
{diagnosis}

## Interpretação Simbólica
{symbolic_interpretation}

## Riscos Identificados
{risks}

## Caminhos de Decisão
{decisions}

## Plano Prático
{practical_plan}

---
*Relatório gerado por Sistema de Clareza Simbólico-Estratégica v0.0.1 — use como ferramenta de reflexão, não como previsão determinista.*
"""


# ----------------------------------------------------------------------
# Gerador de relatórios
# ----------------------------------------------------------------------


class ReportGenerator:
    """Gerador de relatórios Markdown estruturados.

    Transforma o resultado da análise em um relatório legível
    com 5 seções obrigatórias.

    Attributes:
        include_timestamp: Se True, inclui timestamp no relatório (default True).
    """

    def __init__(self, include_timestamp: bool = True) -> None:
        self.include_timestamp = include_timestamp
        logger.debug("ReportGenerator inicializado, timestamp=%s", include_timestamp)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generate(
        self,
        analysis: AnalysisResult,
        disclaimer: Optional[str] = None,
    ) -> str:
        """Gera relatório Markdown a partir do resultado da análise.

        Args:
            analysis: AnalysisResult com diagnóstico, temas, riscos, decisões e plano.
            disclaimer: Texto adicional a ser inserido antes do rodapé (opcional).

        Returns:
            String com relatório completo em Markdown.
        """
        logger.info("Gerando relatório para análise com %d temas", len(analysis.themes))

        # Montar campos do template
        timestamp = self._get_timestamp()
        diagnosis = self._format_diagnosis(analysis)
        symbolic_interp = self._format_symbolic_interpretation(analysis)
        risks = self._format_risks(analysis)
        decisions = self._format_decisions(analysis)
        practical_plan = self._format_practical_plan(analysis)

        # Preencher template
        report = REPORT_TEMPLATE.format(
            timestamp=timestamp,
            diagnosis=diagnosis,
            symbolic_interpretation=symbolic_interp,
            risks=risks,
            decisions=decisions,
            practical_plan=practical_plan,
        )

        # Inserir disclaimer adicional se fornecido
        if disclaimer:
            report = report.rstrip() + "\n\n" + disclaimer + "\n"

        logger.info("Relatório gerado com %d caracteres", len(report))
        return report

    # ------------------------------------------------------------------
    # Formatadores por seção
    # ------------------------------------------------------------------

    def _get_timestamp(self) -> str:
        """Retorna timestamp formatado para o relatório."""
        if self.include_timestamp:
            return datetime.now().strftime("%d/%m/%Y às %H:%M")
        return ""

    def _format_diagnosis(self, analysis: AnalysisResult) -> str:
        """Formata a seção de Diagnóstico.

        Args:
            analysis: Resultado da análise.

        Returns:
            String formatada com o diagnóstico.
        """
        return analysis.diagnosis or "*Diagnóstico não disponível.*"

    def _format_symbolic_interpretation(self, analysis: AnalysisResult) -> str:
        """Formata a seção de Interpretação Simbólica.

        Args:
            analysis: Resultado da análise.

        Returns:
            String formatada com as interpretações simbólicas.
        """
        lines: list[str] = []

        # Mapeamentos simbólicos (keywords → símbolos)
        if analysis.symbolic_mappings:
            lines.append("### Mapeamentos Identificados\n")
            for keyword, symbol_name in analysis.symbolic_mappings.items():
                prefix = keyword.split(":")[0]  # "kw:" ou "card:"
                key = keyword.split(":", 1)[-1]
                prefix_label = "Keyword" if prefix == "kw" else "Carta"
                lines.append(f"- **{prefix_label}**: {key} → *{symbol_name}*")
            lines.append("")

        # Interpretações das cartas (para tiragens spread)
        if analysis.card_interpretations:
            lines.append("### Interpretação das Cartas\n")
            for interp in analysis.card_interpretations:
                lines.append(interp)
                lines.append("")
            lines.append("")

        # Temas detectados
        if analysis.themes:
            lines.append("### Temas Predominantes\n")
            for theme in analysis.themes:
                lines.append(f"- *{theme}*")
            lines.append("")

        # Fallback se nada foi gerado
        if not lines:
            return "*Nenhuma interpretação simbólica disponível — forneça mais contexto para análise.*"

        return "\n".join(lines).strip()

    def _format_risks(self, analysis: AnalysisResult) -> str:
        """Formata a seção de Riscos Identificados.

        Args:
            analysis: Resultado da análise.

        Returns:
            String formatada com os riscos.
        """
        if not analysis.risks:
            return "*Nenhum risco específico identificado — a análise não encontrou temas de atenção.*"

        lines: list[str] = []
        for risk in analysis.risks:
            lines.append(f"- {risk}")
        return "\n".join(lines)

    def _format_decisions(self, analysis: AnalysisResult) -> str:
        """Formata a seção de Caminhos de Decisão.

        Args:
            analysis: Resultado da análise.

        Returns:
            String formatada com os caminhos de decisão.
        """
        if not analysis.decisions:
            return "*Nenhum caminho de decisão específico identificado — a análise não encontrou temas de escolha.*"

        lines: list[str] = []
        for i, decision in enumerate(analysis.decisions, start=1):
            lines.append(f"{i}. {decision}")
        return "\n".join(lines)

    def _format_practical_plan(self, analysis: AnalysisResult) -> str:
        """Formata a seção de Plano Prático.

        Args:
            analysis: Resultado da análise.

        Returns:
            String formatada com o plano prático.
        """
        if not analysis.practical_plan:
            return "*Plano prático não disponível — a análise não gerou recomendações.*"

        return analysis.practical_plan

    # ------------------------------------------------------------------
    # Utilitários de formatação
    # ------------------------------------------------------------------

    @staticmethod
    def format_list(items: list[str], bullet: str = "-") -> str:
        """Formata uma lista de itens como Markdown.

        Args:
            items: Lista de strings a formatar.
            bullet: Caractere ou string de marcação (default "-").

        Returns:
            String formatada com cada item em sua própria linha.
        """
        if not items:
            return "*Nenhum item disponível.*"
        return "\n".join(f"{bullet} {item}" for item in items)

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