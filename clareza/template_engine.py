"""Template Engine — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por renderizar relatórios a partir de templates
configuráveis (ReportTemplate) usando dados da análise (AnalysisResult).

Suporta seções ordenadas, habilitação/desabilitação de seções,
placeholders customizados e renderização flexível.

Patterns from:
    src/report_generator.py (ReportGenerator pattern)
    src/types.py (AnalysisResult, ReportTemplate, TemplateSection)
"""

import logging
import re
from typing import Optional

from clareza.types import AnalysisResult, ReportTemplate, TemplateSection

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Compilação de templates
# ----------------------------------------------------------------------


def _compile_template(content_template: str) -> re.Pattern:
    """Compila template de conteúdo em padrão regex para substituição.

    Args:
        content_template: String de template com placeholders {field}.

    Returns:
        Padrão regex para encontrar todos os placeholders.

    Raises:
        re.error: Se o padrão for inválido (desvia de caracteres especiais).
    """
    # Escape special regex chars in template, then replace \{...\} with actual placeholder
    escaped = re.escape(content_template)
    escaped = escaped.replace(r"\{", "{").replace(r"\}", "}")
    pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>.+?)", escaped)
    return re.compile(pattern)


def _substitute_template(
    content_template: str,
    substitutions: dict[str, str],
) -> str:
    """Substitui placeholders em um template de conteúdo.

    Args:
        content_template: Template com placeholders {field}.
        substitutions: Dicionário de campo → valor.

    Returns:
        String com placeholders substituídos.
    """
    result = content_template
    for field, value in substitutions.items():
        placeholder = "{" + field + "}"
        result = result.replace(placeholder, value)
    return result


# ----------------------------------------------------------------------
# Preparadores de contexto
# ----------------------------------------------------------------------


def _prepare_diagnosis_context(analysis: AnalysisResult) -> str:
    """Prepara contexto para campo diagnosis.

    Args:
        analysis: Resultado da análise.

    Returns:
        String formatada com o diagnóstico.
    """
    return analysis.diagnosis or ""


def _prepare_symbolic_interpretation_context(analysis: AnalysisResult) -> str:
    """Prepara contexto para campo symbolic_interpretation.

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

    return "\n".join(lines).strip()


def _prepare_risks_context(analysis: AnalysisResult) -> str:
    """Prepara contexto para campo risks.

    Args:
        analysis: Resultado da análise.

    Returns:
        String formatada com os riscos.
    """
    if not analysis.risks:
        return ""

    lines: list[str] = []
    for risk in analysis.risks:
        lines.append(f"- {risk}")
    return "\n".join(lines)


def _prepare_decisions_context(analysis: AnalysisResult) -> str:
    """Prepara contexto para campo decisions.

    Args:
        analysis: Resultado da análise.

    Returns:
        String formatada com os caminhos de decisão.
    """
    if not analysis.decisions:
        return ""

    lines: list[str] = []
    for i, decision in enumerate(analysis.decisions, start=1):
        lines.append(f"{i}. {decision}")
    return "\n".join(lines)


def _prepare_cross_card_patterns_context(analysis: AnalysisResult) -> str:
    """Prepara contexto para campo cross_card_patterns.

    Args:
        analysis: Resultado da análise.

    Returns:
        String formatada com os padrões detectados entre múltiplas cartas.
    """
    if not analysis.cross_card_patterns:
        return ""

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


def _prepare_practical_plan_context(analysis: AnalysisResult) -> str:
    """Prepara contexto para campo practical_plan.

    Args:
        analysis: Resultado da análise.

    Returns:
        String formatada com o plano prático.
    """
    return analysis.practical_plan or ""


# Mapeamento de campos known → preparadores
_CONTEXT_PREPARERS: dict[str, callable] = {
    "diagnosis": _prepare_diagnosis_context,
    "symbolic_interpretation": _prepare_symbolic_interpretation_context,
    "risks": _prepare_risks_context,
    "decisions": _prepare_decisions_context,
    "cross_card_patterns": _prepare_cross_card_patterns_context,
    "practical_plan": _prepare_practical_plan_context,
}


def _build_context(analysis: AnalysisResult) -> dict[str, str]:
    """Constrói dicionário de contexto a partir de AnalysisResult.

    Args:
        analysis: Resultado da análise.

    Returns:
        Dicionário com todos os campos disponíveis para substituição.
    """
    context: dict[str, str] = {}
    for field, preparer in _CONTEXT_PREPARERS.items():
        try:
            context[field] = preparer(analysis)
        except Exception as e:
            logger.warning("Erro ao preparar contexto '%s': %s", field, e)
            context[field] = ""
    return context


# ----------------------------------------------------------------------
# Renderizadores de seção
# ----------------------------------------------------------------------


def _extract_template_fields(content_template: str) -> list[str]:
    """Extrai lista de campos referencedos em um content_template.

    Args:
        content_template: Template com placeholders {field}.

    Returns:
        Lista de nomes de campo encontrados.
    """
    return re.findall(r"\{([^}]+)\}", content_template)


def _render_section(
    section: TemplateSection,
    context: dict[str, str],
) -> Optional[str]:
    """Renderiza uma seção individual do template.

    Args:
        section: Seção do template a renderizar.
        context: Dicionário com valores de substituição.

    Returns:
        String renderizada ou None se a seção não deve ser exibida.
    """
    # Verificar se seção está habilitada
    if not section.enabled:
        logger.debug("Seção '%s' desabilitada, pulando", section.id)
        return None

    # Verificar campos obrigatórios
    required_fields = _extract_template_fields(section.content_template)
    missing_fields = [f for f in required_fields if f not in context]
    if missing_fields:
        logger.warning(
            "Seção '%s': campos desconhecidos %s (disponíveis: %s)",
            section.id,
            missing_fields,
            list(context.keys()),
        )

    # Substituir placeholders
    rendered_content = _substitute_template(section.content_template, context)

    # Verificar se conteúdo está vazio
    if not rendered_content.strip():
        if section.placeholder:
            return section.placeholder
        if section.required:
            raise ValueError(f"Seção required '{section.id}' está vazia")
        logger.debug("Seção '%s' vazia sem placeholder, ocultando", section.id)
        return None

    return rendered_content


# ----------------------------------------------------------------------
# Template Engine
# ----------------------------------------------------------------------


class TemplateEngine:
    """Motor de renderização de relatórios configuráveis.

    Transforma um ReportTemplate em relatório Markdown usando dados
    de AnalysisResult. Suporta seções ordenadas, habilitação,
    placeholders e renderização flexível.

    Attributes:
        default_template: Template usado quando nenhum é fornecido.
    """

    def __init__(self, default_template: Optional[ReportTemplate] = None) -> None:
        self.default_template = default_template
        logger.debug("TemplateEngine inicializado")

    def render(
        self,
        analysis: AnalysisResult,
        template: Optional[ReportTemplate] = None,
        timestamp: Optional[str] = None,
        disclaimer: Optional[str] = None,
    ) -> str:
        """Renderiza relatório a partir de template e dados de análise.

        Args:
            analysis: Resultado da análise com dados para o relatório.
            template: Template a usar (default: built-in).
            timestamp: Timestamp para incluir no relatório (opcional).
            disclaimer: Disclaimer adicional a adicionar (opcional).

        Returns:
            String com relatório renderizado em Markdown.

        Raises:
            ValueError: Se template for inválido ou seção required vazia.
        """
        template = template or self.default_template
        if template is None:
            raise ValueError("Nenhum template disponível e nenhum default_template configurado")

        logger.info(
            "Renderizando relatório com template '%s' (%d seções)",
            template.template_id,
            len(template.sections),
        )

        # Construir contexto a partir de análise
        context = _build_context(analysis)

        # Adicionar timestamp se presente
        if timestamp:
            context["timestamp"] = timestamp

        # Renderizar seções
        rendered_sections: list[tuple[int, str, str]] = []  # (order, title, content)
        for section in template.sections:
            try:
                rendered = _render_section(section, context)
                if rendered is not None:
                    rendered_sections.append((section.order, section.title, rendered))
            except ValueError:
                # Seção required vazia - propagar erro
                raise
            except Exception as e:
                logger.warning("Erro ao renderizar seção '%s': %s", section.id, e)
                if section.required:
                    raise ValueError(f"Seção required '{section.id}' falhou: {e}")

        # Ordenar por ordem
        rendered_sections.sort(key=lambda x: x[0])

        # Montar relatório
        lines: list[str] = []

        # Cabeçalho com timestamp
        if timestamp:
            lines.append(f"# Relatório de Análise — {timestamp}")
            lines.append("")

        # Seções renderizadas
        for order, title, content in rendered_sections:
            lines.append(f"## {title}")
            lines.append("")
            lines.append(content)
            lines.append("")

        # Disclaimer
        if disclaimer:
            lines.append(disclaimer)
            lines.append("")

        # Rodapé padrão
        footer = (
            "---\n"
            "*Relatório gerado por Sistema de Clareza Simbólico-Estratégica "
            "v0.0.1 — use como ferramenta de reflexão, não como previsão determinista.*"
        )
        lines.append(footer)

        result = "\n".join(lines)
        logger.info("Relatório renderizado com %d caracteres", len(result))
        return result

    def render_section(
        self,
        section: TemplateSection,
        analysis: AnalysisResult,
    ) -> Optional[str]:
        """Renderiza uma seção individual.

        Útil para preview ou teste de seções específicas.

        Args:
            section: Seção do template a renderizar.
            analysis: Resultado da análise.

        Returns:
            String renderizada ou None se seção desabilitada/vazia.
        """
        if not section.enabled:
            return None

        context = _build_context(analysis)
        return _render_section(section, context)

    def get_available_fields(self) -> list[str]:
        """Retorna lista de campos disponíveis para templates.

        Returns:
            Lista de nomes de campo que podem ser usados em content_template.
        """
        return list(_CONTEXT_PREPARERS.keys())

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    @staticmethod
    def extract_fields(template_str: str) -> list[str]:
        """Extrai campos de um template string.

        Args:
            template_str: String de template com {field}.

        Returns:
            Lista de nomes de campo encontrados.
        """
        return _extract_template_fields(template_str)

    @staticmethod
    def substitute(template_str: str, **kwargs: str) -> str:
        """Substitui campos em um template string.

        Args:
            template_str: String de template com {field}.
            **kwargs: Valores para cada campo.

        Returns:
            String com campos substituídos.
        """
        return _substitute_template(template_str, kwargs)