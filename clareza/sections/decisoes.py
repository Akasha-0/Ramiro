# coding: utf-8
"""Decisões section generator for Clareza reflection reports."""

from clareza.analysis import SessionAnalysis


def generate_decisoes(analysis: SessionAnalysis) -> str:
    """Generate the Decisões section of a reflection report.

    The Decisões section presents structured options and trade-offs
    for the decisions at hand based on the detected cards and themes.

    Args:
        analysis: SessionAnalysis object containing cards, themes, and question.

    Returns:
        A formatted Markdown string for the Decisões section.
    """
    lines = []

    # Section heading
    lines.append("# Decisões e Opções")
    lines.append("")

    # Introduction
    lines.append("Esta seção apresenta caminhos possíveis baseados na leitura das cartas. Cada opção inclui seus prós e contras para ajudá-lo(a) a tomar uma decisão fundamentada.")
    lines.append("")

    # Define decision pathways based on themes and cards
    options: list[dict] = []

    # Theme-based decision options
    theme_options: dict[str, list[dict]] = {
        "incerteza": [
            {
                "title": "Aguardar mais informações",
                "description": "Decidir não agir imediatamente e buscar mais contexto antes de tomar uma decisão.",
                "pros": ["Permite tempo para analisar melhor a situação", "Reduz risco de decisões precipitadas"],
                "contras": ["Pode resultar em oportunidade perdida", "Incerteza prolongada pode causar ansiedade"],
            },
            {
                "title": "Agir com base no que se sabe",
                "description": "Tomar a decisão com as informações disponíveis agora, aceitando alguma incerteza.",
                "pros": ["Permite avançar sem esperar indefinidamente", "Demonstra iniciativa e coragem"],
                "contras": ["Maior risco de erro por falta de informação", "Pode gerar arrependimento se a informação mudar"],
            },
        ],
        "medo": [
            {
                "title": "Enfrentar diretamente o medo",
                "description": "Agir apesar do medo, confrontando a fonte de ansiedade.",
                "pros": ["Supera o medo ao enfrentá-lo", "Gera crescimento pessoal e autoconfiança"],
                "contras": ["Risco de fracasso e reforco do medo", "Pode ser emocionalmente desafiador"],
            },
            {
                "title": "Reconhecer e respeitar o medo",
                "description": "Usar o medo como sinal de cautela, não como paralisia.",
                "pros": ["Evita decisões impulsivas por medo", "Permite ação considerada"],
                "contras": ["Pode ser usado como desculpa para inação", "Medo irracional não sera superado"],
            },
        ],
        "esperanca": [
            {
                "title": "Seguir com otimismo calculado",
                "description": "Avançar com esperança, mas mantendo perspectiva realista.",
                "pros": ["Mantém motivação e energia positiva", "Permite ação enquanto gerencia expectativas"],
                "contras": ["Pode ignorar sinais de alerta", "Expectativas muito altas podem gerar decepção"],
            },
        ],
        "relacionamento": [
            {
                "title": "Buscar diálogo aberto",
                "description": "Iniciar conversa honesta com a outra parte sobre a situação.",
                "pros": ["Clarifica mal-entendidos", "Fortalece a relação se bem executado"],
                "contras": ["Requer vulnerabilidade", "Conversa pode ser desconfortável"],
            },
            {
                "title": "Dar espaço e tempo",
                "description": "Recuar momentaneamente para permitir reflexão e clareza.",
                "pros": ["Evita conflitos no calor do momento", "Permite perspectiva mais calma"],
                "contras": ["Pode ser interpretado como desinteresse", "Problema pode escalar se não abordado"],
            },
        ],
        "decisao": [
            {
                "title": "Decidir rapidamente com base em princípios",
                "description": "Estabelecer critérios claros e tomar decisão no prazo definido.",
                "pros": ["Evita paralisia por análise", "Demonstra clareza de valores"],
                "contras": ["Pode ignorar detalhes importantes", "Decisão pode ser revertida se apressada"],
            },
            {
                "title": "Coletar mais dados antes de decidir",
                "description": "Ampliar a análise com mais informações e perspectivas.",
                "pros": ["Decisão mais bem informada", "Maior confiança na escolha"],
                "contras": ["Risco de procrastinação", "Informações adicionais podem causar mais dúvidas"],
            },
        ],
        "trabalho": [
            {
                "title": "Priorizar estabilidade",
                "description": "Escolher a opção mais segura e previsível profissionalmente.",
                "pros": ["Menor risco financeiro", "Rotina estabelecida"],
                "contras": ["Pode limitar crescimento", "Estagnação profissional"],
            },
            {
                "title": "Buscar nova oportunidade",
                "description": "Investigar e perseguir opções que representem mudança ou progresso.",
                "pros": ["Potencial de crescimento", "Renovação de energia e motivação"],
                "contras": ["Maior insegurança", "Risco de insucesso"],
            },
        ],
        "financeiro": [
            {
                "title": "Conservar recursos",
                "description": "Priorizar economia e segurança financeira.",
                "pros": ["Proteção contra imprevistos", "Menor estresse financeiro"],
                "contras": ["Perda de oportunidades de investimento", "Inflação pode erodir valor"],
            },
            {
                "title": "Investir no crescimento",
                "description": "Destinar recursos para oportunidades que podem gerar retorno.",
                "pros": ["Potencial de ganhos significativos", "Crescimento patrimonial"],
                "contras": ["Risco de perda", "Requer monitoramento ativo"],
            },
        ],
        "saude": [
            {
                "title": "Buscar orientação profissional",
                "description": "Consultar especialistas e profissionais de saúde.",
                "pros": ["Orientação baseada em evidências", "Plano de ação estruturado"],
                "contras": ["Pode ser lento e custoso", "Dependência de terceiros"],
            },
            {
                "title": "Iniciar mudanças por conta própria",
                "description": "Implementar melhorias na saúde de forma autônoma.",
                "pros": ["Imediato e acessível", "Controle sobre o processo"],
                "contras": ["Falta de expertise", "Risco de abordagem inadequada"],
            },
        ],
    }

    # Collect options based on detected themes
    detected_themes = set(analysis.themes) if analysis.themes else set()
    added_titles = set()

    for theme in detected_themes:
        theme_lower = theme.lower()
        for option_theme, theme_option_list in theme_options.items():
            if option_theme in theme_lower or theme_lower in option_theme:
                for option in theme_option_list:
                    if option["title"] not in added_titles:
                        options.append(option)
                        added_titles.add(option["title"])

    # Add card-specific options based on card presence
    for card in analysis.cards:
        if card.is_reversed():
            # For reversed cards, suggest caution or different approach
            if "cautela" not in added_titles:
                options.append({
                    "title": "Abordar com cautela",
                    "description": f"A carta {card.name} aparece invertida, sugerindo que você deve abordar esta situação com mais cuidado e consideração.",
                    "pros": ["Evita erros por impulsividade", "Permite reflexão profunda"],
                    "contras": ["Pode atrasar ação necessária", "Incerteza prolongada"],
                })
                added_titles.add("cautela")
        else:
            # For upright cards, suggest confident action
            if "agir com confiança" not in added_titles:
                options.append({
                    "title": "Agir com confiança",
                    "description": "A energia positiva das cartas sugere que é momento de avançar com determinação.",
                    "pros": ["Capture momento favoravel", "Demonstra iniciativa"],
                    "contras": ["Risco se a leitura for interpretada incorretamente", "Pode parecer apressado para outros"],
                })
                added_titles.add("agir com confiança")

    # Add generic options if none specific found
    if not options:
        options.append({
            "title": "Considerar múltiplas perspectivas",
            "description": "Antes de decidir, examine a situação de diferentes ângulos e considere pontos de vista diversos.",
            "pros": ["Decisão mais equilibrada", "Menos surpresas"],
            "contras": ["Pode delaying o processo", "Confusão por excesso de informações"],
        })
        options.append({
            "title": "Estabelecer prazo para decisão",
            "description": "Definir um limite claro para quando a decisão deve ser tomada.",
            "pros": ["Evita procrastinação", "Cria senso de urgência saudável"],
            "contras": ["Decisão pode ser apressada", "Estresse no prazo"],
        })

    # Display each option
    lines.append("## Caminhos Possíveis")
    lines.append("")
    for i, option in enumerate(options[:4], start=1):  # Limit to 4 options
        lines.append(f"### {i}. {option['title']}")
        lines.append("")
        lines.append(f"{option['description']}")
        lines.append("")
        lines.append("**Prós:**")
        for pro in option["pros"]:
            lines.append(f"- {pro}")
        lines.append("")
        lines.append("**Contras:**")
        for contra in option["contras"]:
            lines.append(f"- {contra}")
        lines.append("")

    # Decision framework
    lines.append("---")
    lines.append("")
    lines.append("## Framework para sua Decisão")
    lines.append("")
    lines.append("Para escolher o melhor caminho, considere:")
    lines.append("")
    lines.append("1. **Alinhamento com seus valores:** Esta opção respeita o que é mais importante para você?")
    lines.append("2. **Consequências de longo prazo:** Como esta decisão afetará sua vida nos próximos meses ou anos?")
    lines.append("3. **Reversibilidade:** Você pode reverter esta decisão se necessário?")
    lines.append("4. **Informação disponível:** Você tem dados suficientes para tomar esta decisão agora?")
    lines.append("")

    # Warning about decision making
    lines.append("---")
    lines.append("")
    lines.append("## Aviso")
    lines.append("")
    lines.append("⚠️  As cartas oferecem reflexão, não determinismo. Você tem agency sobre suas escolhas. Use estas opções como ponto de partida para sua reflexão, não como veredicto final. Sua intuição, experiência e contexto pessoal são fatores essenciais que nenhuma leitura pode substituir.")
    lines.append("")
    lines.append("A melhor decisão é aquela que você pode defender com razões claras e que se alinha com seus objetivos de longo prazo.")
    lines.append("")

    return "\n".join(lines)