# coding: utf-8
"""Report generator module for Clareza reflection reports."""

import json
from pathlib import Path
from typing import Optional

from clareza.analysis import CardAnalysis, SessionAnalysis
from clareza.themes import get_themes_for_card
from clareza.sections.diagnostico import generate_diagnostico
from clareza.sections.interpretacao import generate_interpretacao
from clareza.sections.riscos import generate_riscos
from clareza.sections.decisoes import generate_decisoes
from clareza.sections.plano import generate_plano


def get_cards_data() -> list[dict]:
    """Load cards data from the JSON file.

    Returns:
        List of card dictionaries from cards.json.
    """
    cards_path = Path(__file__).parent / "data" / "cards.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_cards(
    card_ids: list[int],
    primary_question: str = "",
) -> SessionAnalysis:
    """Analyze a list of cards and build a SessionAnalysis object.

    Args:
        card_ids: List of card IDs to analyze.
        primary_question: The main question asked by the user.

    Returns:
        SessionAnalysis object with analyzed cards and themes.
    """
    cards_data = get_cards_data()

    analyzed_cards: list[CardAnalysis] = []
    all_themes: list[str] = []

    for card_id in card_ids:
        # Find the card in the data
        card_data = next(
            (c for c in cards_data if c["id"] == card_id),
            None,
        )
        if card_data is None:
            continue

        # Determine direction based on card ID (odd=upright, even=reversed)
        # This is a simple heuristic; in real usage, the CLI might accept direction
        direction = "upright" if card_id % 2 == 1 else "reversed"

        # Get themes for this card using the card ID
        card_themes = get_themes_for_card(card_data["id"])

        # Calculate relevance (placeholder - could be enhanced with NLP)
        relevance = 0.7 if card_themes else 0.5

        # Create CardAnalysis object
        card_analysis = CardAnalysis(
            card_id=card_data["id"],
            name=card_data["name"],
            keywords=card_data.get("keywords", []),
            meaning=card_data["meaning"],
            direction=direction,
            relevance=relevance,
            themes=card_themes,
        )

        analyzed_cards.append(card_analysis)
        all_themes.extend(card_themes)

    return SessionAnalysis(
        cards=analyzed_cards,
        themes=all_themes,
        primary_question=primary_question,
    )


def generate_report(
    card_ids: list[int],
    primary_question: str = "",
) -> str:
    """Generate a complete five-section reflection report.

    Assembles all five sections of the Clareza reflection report:
    1. Diagnóstico - Analysis of detected cards, themes, and primary question
    2. Interpretação Simbólica - Deep symbolic interpretation of cards
    3. Riscos - Identification of cognitive biases and emotional traps
    4. Decisões - Structured options and trade-offs
    5. Plano Prático - Concrete actionable steps with timeline

    Args:
        card_ids: List of card IDs to include in the report.
        primary_question: The main question asked by the user.

    Returns:
        A complete Markdown report with all five sections.
    """
    # Analyze the cards
    analysis = analyze_cards(card_ids, primary_question)

    # Validate that we have cards to analyze
    if not analysis.cards:
        raise ValueError("Nenhuma carta válida fornecida para análise.")

    # Build the report sections
    sections: list[str] = []

    # Section 1: Diagnóstico
    diagnostico = generate_diagnostico(analysis)
    sections.append(diagnostico)

    # Section 2: Interpretação Simbólica
    interpretacao = generate_interpretacao(analysis)
    sections.append(interpretacao)

    # Section 3: Riscos
    riscos = generate_riscos(analysis)
    sections.append(riscos)

    # Section 4: Decisões
    decisoes = generate_decisoes(analysis)
    sections.append(decisoes)

    # Section 5: Plano Prático
    plano = generate_plano(analysis)
    sections.append(plano)

    # Join all sections
    return "\n".join(sections)


def save_report(
    card_ids: list[int],
    primary_question: str = "",
    output_path: Optional[Path] = None,
) -> str:
    """Generate and optionally save a report to a file.

    Args:
        card_ids: List of card IDs to include in the report.
        primary_question: The main question asked by the user.
        output_path: Optional path to save the report. If None, returns content.

    Returns:
        The generated report content.
    """
    report_content = generate_report(card_ids, primary_question)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

    return report_content
