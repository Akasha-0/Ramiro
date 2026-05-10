# coding: utf-8
"""Diagnóstico section generator for Clareza reflection reports."""

from clareza.analysis import SessionAnalysis


def generate_diagnostico(analysis: SessionAnalysis) -> str:
    """Generate the Diagnóstico section of a reflection report.

    The Diagnóstico section provides an overview of the session including
    detected cards, their mapped themes, and the primary question asked.

    Args:
        analysis: SessionAnalysis object containing cards, themes, and question.

    Returns:
        A formatted Markdown string for the Diagnóstico section.
    """
    lines = []

    # Section heading
    lines.append("# Diagnóstico")
    lines.append("")

    # Primary question
    if analysis.primary_question:
        lines.append(f"**Questão Principal:** {analysis.primary_question}")
        lines.append("")

    # Card count overview
    card_count = analysis.get_card_count()
    lines.append(f"**Análise de {card_count} carta{'s' if card_count > 1 else ''}:**")
    lines.append("")

    # List each card with its details
    for i, card in enumerate(analysis.cards, start=1):
        direction_indicator = " (Invertida)" if card.is_reversed() else ""
        lines.append(f"{i}. **{card.name}**{direction_indicator}")
        lines.append(f"   - Significado: {card.meaning}")
        if card.themes:
            lines.append(f"   - Temas: {', '.join(card.themes)}")
        lines.append("")

    # Theme summary
    if analysis.themes:
        # Count theme occurrences
        theme_counts: dict[str, int] = {}
        for theme in analysis.themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        # Sort by frequency
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        dominant_theme = analysis.get_dominant_theme()

        lines.append("**Resumo dos Temas:**")
        for theme, count in sorted_themes:
            marker = " ← tema dominante" if theme == dominant_theme else ""
            lines.append(f"- {theme}: {count} ocorrência{'s' if count > 1 else ''}{marker}")

        lines.append("")

    # Session summary if available
    if analysis.session_summary:
        lines.append(f"**Síntese:** {analysis.session_summary}")
        lines.append("")

    return "\n".join(lines)