# coding: utf-8
"""Riscos section generator for Clareza reflection reports."""

from clareza.analysis import SessionAnalysis


def generate_riscos(analysis: SessionAnalysis) -> str:
    """Generate the Riscos section of a reflection report.

    The Riscos section identifies potential cognitive biases, emotional
    traps, and pitfalls relevant to the user's situation based on the
    detected cards and themes.

    Args:
        analysis: SessionAnalysis object containing cards, themes, and question.

    Returns:
        A formatted Markdown string for the Riscos section.
    """
    lines = []

    # Section heading
    lines.append("# Riscos e Armadilhas Cognitivas")
    lines.append("")

    # Introduction
    lines.append("Esta seção alerta para vieses cognitivos e armadilhas emocionais que podem distorcer sua percepção da situação. Reconhecê-los é o primeiro passo para evitá-los.")
    lines.append("")

    # Risk categories based on themes
    risks: list[dict] = []

    # Define theme-based risk mappings
    theme_risks: dict[str, dict] = {
        "incerteza": {
            "title": "Viés de Intolerância à Incerteza",
            "description": "A necessidade de respostas imediatas pode levar a decisões precipitadas.",
            "recommendation": "Pratique a tolerância à ambiguidade. Nem sempre uma carta fornece todas as respostas.",
        },
        "medo": {
            "title": "Viés de Confirmação do Medo",
            "description": "Você pode tender a interpretar sinais de forma negativa, reforçando a narrativa de medo.",
            "recommendation": "Questione: \"Esta interpretação é baseada em evidências ou em ansiedade?\"",
        },
        "esperanca": {
            "title": "Viés Otimista Exagerado",
            "description": "A esperança pode cegar para sinais de alerta importantes.",
            "recommendation": "Equilibre a esperança com uma análise realista dos fatos.",
        },
        "relacionamento": {
            "title": "Viés de Projeção Emocional",
            "description": "Você pode interpretar as cartas através do filtro de seus próprios desejos e medos.",
            "recommendation": "Tente manter objetividade ao analisar situações relacionais.",
        },
        "decisao": {
            "title": "Paralisia por Análise",
            "description": "Analisar demais pode levar à incapacidade de agir.",
            "recommendation": "Defina um prazo para sua decisão e respeite-o.",
        },
        "trabalho": {
            "title": "Viés de Confirmação Profissional",
            "description": "Você pode buscar apenas informações que confirmem suas crenças sobre sua carreira.",
            "recommendation": "Considere perspectivas que desafiem suas suposições.",
        },
        "financeiro": {
            "title": "Viés de Aversão à Perda",
            "description": "O medo de perder dinheiro pode levar a decisões subótimas.",
            "recommendation": "Avalie oportunidades com base em ganhos potenciais, não apenas em perdas evitadas.",
        },
        "saude": {
            "title": "Catastrofização",
            "description": "Preocupações com saúde podem ser amplificadas pelo viés de disponibilidade.",
            "recommendation": "Busque informações médicas profissionais, não apenas autoconhecimento.",
        },
    }

    # Collect risks based on detected themes
    detected_themes = set(analysis.themes) if analysis.themes else set()

    for theme in detected_themes:
        theme_lower = theme.lower()
        for risk_theme, risk_info in theme_risks.items():
            if risk_theme in theme_lower or theme_lower in risk_theme:
                # Avoid duplicates
                if not any(r["title"] == risk_info["title"] for r in risks):
                    risks.append(risk_info)

    # Add card-specific risks
    for card in analysis.cards:
        # Check for reversed cards that may indicate blind spots
        if card.is_reversed():
            theme_ref = card.themes[0] if card.themes else "este tema"
            risks.append({
                "title": f"Zona Cega: {card.name}",
                "description": f"Esta carta aparece invertida, indicando que você pode estar ignorando um aspecto importante relacionado a {theme_ref}.",
                "recommendation": "Reflita sobre o que você pode estar evitando reconhecer sobre si mesmo(a).",
            })

    # Add generic risks if none specific found
    if not risks:
        risks.append({
            "title": "Viés de Acomodação",
            "description": "Você pode ter resistência a mudanças que são necessárias.",
            "recommendation": "Questione suas suposições sobre o que é 'normal' ou 'esperado'.",
        })
        risks.append({
            "title": "Viés de Ancoragem",
            "description": "Suas primeiras impressões podem estar excessivamente influenciando suas conclusões.",
            "recommendation": "Revise suas conclusões iniciais com uma mente aberta.",
        })

    # Display each risk
    lines.append("## Armadilhas Identificadas")
    lines.append("")
    for i, risk in enumerate(risks[:5], start=1):  # Limit to 5 risks
        lines.append(f"### {i}. {risk['title']}")
        lines.append("")
        lines.append(f"**O que é:** {risk['description']}")
        lines.append("")
        lines.append(f"**Como evitar:** {risk['recommendation']}")
        lines.append("")

    # Warning about self-fulfilling prophecy
    lines.append("---")
    lines.append("")
    lines.append("## Aviso Importante")
    lines.append("")
    lines.append("⚠️  Lembre-se: cartas do Baralho Cigano são ferramentas de reflexão, não previsões determinísticas. Seu pensamento e suas ações influenciam ativamente os resultados. Não permita que o medo de um resultado negativo se torne o próprio resultado.")
    lines.append("")
    lines.append("Use estas reflexões como guia para pensamento consciente, não como destino fixo.")
    lines.append("")

    return "\n".join(lines)