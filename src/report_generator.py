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

import json
import logging
from datetime import datetime
from typing import Optional

from src.types import AnalysisResult, CrossCardPattern

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

## Padrões Cruzados
{cross_card_patterns}

## Plano Prático
{practical_plan}

---
*Relatório gerado por Sistema de Clareza Simbólico-Estratégica v0.0.1 — use como ferramenta de reflexão, não como previsão determinista.*
"""

# ----------------------------------------------------------------------
# Template compacto — resumo das 5 seções
# ----------------------------------------------------------------------

COMPACT_TEMPLATE = """# Análise — {timestamp}

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
        output_format: str = "default",
    ) -> str:
        """Gera relatório em Markdown (ou outro formato) a partir do resultado da análise.

        Args:
            analysis: AnalysisResult com diagnóstico, temas, riscos, decisões e plano.
            disclaimer: Texto adicional a ser inserido antes do rodapé (opcional).
            output_format: Formato do relatório — "default" (completo), "compact"
                (resumido), ou "json" (estruturado). Default: "default".

        Returns:
            String com relatório no formato solicitado.

        Raises:
            ValueError: Se output_format não for um dos valores suportados.
        """
        logger.info(
            "Gerando relatório para análise com %d temas (formato=%s)",
            len(analysis.themes),
            output_format,
        )

        # Validar formato
        valid_formats = {"default", "compact", "json"}
        if output_format not in valid_formats:
            logger.warning("Formato desconhecido '%s', usando 'default'", output_format)
            output_format = "default"

        # Montar campos do template
        timestamp = self._get_timestamp()
        diagnosis = self._format_diagnosis(analysis)
        symbolic_interp = self._format_symbolic_interpretation(analysis)
        risks = self._format_risks(analysis)
        decisions = self._format_decisions(analysis)
        cross_card_patterns = self._format_cross_card_patterns(analysis)
        practical_plan = self._format_practical_plan(analysis)

        # Selecionar template ou formato conforme solicitado
        if output_format == "json":
            report = self._generate_json_output(
                timestamp, diagnosis, symbolic_interp, risks, decisions, practical_plan, disclaimer
            )
        elif output_format == "compact":
            report = self._generate_compact_output(
                timestamp, diagnosis, symbolic_interp, risks, decisions, practical_plan, disclaimer
            )
        else:
            report = self._generate_default_output(
                timestamp, diagnosis, symbolic_interp, risks, decisions, practical_plan, disclaimer
            )

        logger.info("Relatório gerado com %d caracteres", len(report))
        return report

    def _generate_default_output(
        self,
        timestamp: str,
        diagnosis: str,
        symbolic_interp: str,
        risks: str,
        decisions: str,
        practical_plan: str,
        disclaimer: Optional[str],
    ) -> str:
        """Gera relatório no formato padrão (completo)."""
        report = REPORT_TEMPLATE.format(
            timestamp=timestamp,
            diagnosis=diagnosis,
            symbolic_interpretation=symbolic_interp,
            risks=risks,
            decisions=decisions,
            cross_card_patterns=cross_card_patterns,
            practical_plan=practical_plan,
        )
        if disclaimer:
            report = report.rstrip() + "\n\n" + disclaimer + "\n"
        return report

    def _generate_compact_output(
        self,
        timestamp: str,
        diagnosis: str,
        symbolic_interp: str,
        risks: str,
        decisions: str,
        practical_plan: str,
        disclaimer: Optional[str],
    ) -> str:
        """Gera relatório no formato compacto."""
        report = COMPACT_TEMPLATE.format(
            timestamp=timestamp,
            diagnosis=diagnosis,
            symbolic_interpretation=symbolic_interp,
            risks=risks,
            decisions=decisions,
            practical_plan=practical_plan,
        )
        if disclaimer:
            report = report.rstrip() + "\n\n" + disclaimer + "\n"
        return report

    def _generate_json_output(
        self,
        timestamp: str,
        diagnosis: str,
        symbolic_interp: str,
        risks: str,
        decisions: str,
        practical_plan: str,
        disclaimer: Optional[str],
    ) -> str:
        """Gera relatório em formato JSON."""
        report_data: dict[str, object] = {
            "timestamp": timestamp,
            "diagnosis": diagnosis,
            "symbolic_interpretation": symbolic_interp,
            "risks": risks,
            "decisions": decisions,
            "practical_plan": practical_plan,
        }
        if disclaimer:
            report_data["disclaimer"] = disclaimer
        return json.dumps(report_data, ensure_ascii=False, indent=2)

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

    def _format_cross_card_patterns(self, analysis: AnalysisResult) -> str:
        """Formata a seção de Padrões Cruzados.

        Args:
            analysis: Resultado da análise.

        Returns:
            String formatada com os padrões detectados entre múltiplas cartas.
        """
        if not analysis.cross_card_patterns:
            return "*Nenhum padrão cruzado identificado — as cartas não apresentam correlações significativas.*"

        lines: list[str] = []
        for pattern in analysis.cross_card_patterns:
            pattern_type_label = pattern.pattern_type.replace("_", " ").title()
            lines.append(f"### {pattern_type_label}\n")
            card_ids_str = ", ".join(str(cid) for cid in pattern.card_ids)
            lines.append(f"**Cartas**: {card_ids_str}")
            if pattern.strength:
                lines.append(f"**Intensidade**: {pattern.strength}")
            lines.append(f"\n{pattern.interpretation}\n")
            lines.append("")

        return "\n".join(lines).strip()

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