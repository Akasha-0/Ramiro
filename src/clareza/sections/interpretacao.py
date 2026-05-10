# coding: utf-8
"""Interpretação Simbólica section generator for Clareza reflection reports."""

from clareza.analysis import SessionAnalysis


def generate_interpretacao(analysis: SessionAnalysis) -> str:
    """Generate the Interpretação Simbólica section of a reflection report.

    The Interpretação Simbólica section provides deep symbolic analysis
    of each card, referencing card names, meanings, keywords, and
    tying them to the user's primary question.

    Args:
        analysis: SessionAnalysis object containing cards, themes, and question.

    Returns:
        A formatted Markdown string for the Interpretação Simbólica section.
    """
    lines = []

    # Section heading
    lines.append("# Interpretação Simbólica")
    lines.append("")

    # Context about the analysis
    if analysis.primary_question:
        lines.append(f"**Análise simbólico-reflexiva à questão:** \"{analysis.primary_question}\"")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Analyze each card with symbolic depth
    for i, card in enumerate(analysis.cards, start=1):
        direction_indicator = " (Invertida)" if card.is_reversed() else ""
        reversed_context = " A energia está bloqueada ou expressa de forma oposta." if card.is_reversed() else ""

        lines.append(f"## {i}. {card.name}{direction_indicator}")
        lines.append("")

        # Card meaning with contextual framing
        lines.append(f"**Significado central:** {card.meaning}")
        lines.append("")

        # Symbolic interpretation
        lines.append("**Análise simbólica:**")
        # Build a contextual interpretation based on card properties
        if card.keywords:
            keyword_list = ", ".join(card.keywords[:5])  # Limit to top 5 keywords
            lines.append(f"Os símbolos centrais desta carta incluem: {keyword_list}.{reversed_context}")
        else:
            lines.append(f"Esta carta fala sobre: {card.meaning}.{reversed_context}")
        lines.append("")

        # Thematic connection
        if card.themes:
            theme_list = ", ".join(card.themes)
            lines.append(f"**Conexão temática:** Este symbolismoconnecta-se com os temas de {theme_list}.")
            lines.append("")

        # Question relevance
        if analysis.primary_question:
            lines.append(f"**Relevância para sua questão:** A energia de {card.name} traz um elemento de reflexão sobre \"{analysis.primary_question}\", sugerindo que este symbolismopode indicar uma direção ou influência em seu caminho atual.")
            lines.append("")

        # Separator between cards (except for the last one)
        if i < len(analysis.cards):
            lines.append("---")
            lines.append("")

    # Synthesis paragraph
    lines.append("---")
    lines.append("")

    # Build synthesis based on card themes
    if analysis.themes:
        dominant = analysis.get_dominant_theme()
        theme_set = list(set(analysis.themes))
        theme_context = ", ".join(theme_set[:4])  # Top 4 themes
        lines.append(f"**Síntese interpretativa:** As cartas revelam um padrão simbólico centrado em {theme_context}. ")
        if dominant:
            lines.append(f"O tema dominante — {dominant} — oferece a chave principal para comprender sua situação atual.{reversed_context}")
        lines.append("")
        if analysis.primary_question:
            lines.append("Esta interpretação convida você a refletir sobre como estas symbolismoses manifestam-se em sua vida atual e quais ações ou perspectivas podem emergir desta leitura.")
        lines.append("")

    return "\n".join(lines)