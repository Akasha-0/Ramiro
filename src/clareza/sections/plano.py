# coding: utf-8
"""Plano Prático section generator for Clareza reflection reports."""

from clareza.analysis import SessionAnalysis


def generate_plano(analysis: SessionAnalysis) -> str:
    """Generate the Plano Prático section of a reflection report.

    The Plano Prático section provides concrete, actionable next steps
    with a suggested timeline based on the detected cards and themes.

    Args:
        analysis: SessionAnalysis object containing cards, themes, and question.

    Returns:
        A formatted Markdown string for the Plano Prático section.
    """
    lines = []

    # Section heading
    lines.append("# Plano Prático")
    lines.append("")

    # Introduction
    lines.append("Esta seção apresenta passos concretos e acionáveis que você pode aplicar a partir de hoje. Cada ação é fundamentada na leitura das cartas e conectada aos temas identificados.")
    lines.append("")

    # Define action steps based on themes and cards
    actions: list[dict] = []

    # Theme-based action mappings
    theme_actions: dict[str, list[dict]] = {
        "incerteza": [
            {
                "title": "Definir um prazo para a decisão",
                "description": "Estabeleça uma data limite clara para resolver a incerteza. Escreva-a em um local visível.",
                "timeline": "Esta semana",
                "rationale": "As cartas indicam incerteza, e um prazo cria estrutura para a ação.",
            },
            {
                "title": "Listar todas as variáveis desconhecidas",
                "description": "Identifique em um papel tudo que você não sabe e que está impedindo sua decisão. Depois, marque o que pode ser descoberto.",
                "timeline": "Próximos 2 dias",
                "rationale": "Tornar o desconhecido visível reduz sua capacidade de paralisar.",
            },
            {
                "title": "Buscar uma segunda opinião",
                "description": "Consulte alguém de confiança que possa oferecer perspectiva externa sobre sua situação.",
                "timeline": "Esta semana",
                "rationale": "Perspectivas externas frequentemente iluminam aspectos não considerados.",
            },
        ],
        "medo": [
            {
                "title": "Identificar o medo específico",
                "description": "Nomeie exatamente do que você tem medo. Escreva-o em uma frase completa.",
                "timeline": "Hoje",
                "rationale": "Medos vagos são mais poderosos que medos nomeados.",
            },
            {
                "title": "Calcular o pior cenário realista",
                "description": "Analise honestamente: se o pior acontecer, você sobreviveria? Quais seriam as consequências reais?",
                "timeline": "Esta semana",
                "rationale": "Frequentemente, o pior cenário é menos devastador do que imaginamos.",
            },
            {
                "title": "Dar um passo pequeno em direção ao medo",
                "description": "Identifique a menor ação que você pode fazer hoje que avance na direção temida. Faça-a.",
                "timeline": "Hoje",
                "rationale": "Ações pequenas acumulam-se e reduzem a intensidade do medo.",
            },
        ],
        "esperanca": [
            {
                "title": "Documentar suas expectativas",
                "description": "Escreva claramente o que você espera que aconteça e por quê. Seja específico.",
                "timeline": "Esta semana",
                "rationale": "Expectativas claras previnem decepções por mal-entendidos.",
            },
            {
                "title": "Criar um plano B",
                "description": "Desenvolva uma alternativa caso a esperança inicial não se materialize.",
                "timeline": "Próximos 7 dias",
                "rationale": "Ter um plano alternativo mantém você ativo, não passivo.",
            },
            {
                "title": "Celebrar o processo, não apenas o resultado",
                "description": "Identifique pequenos marcos de progresso e reconheça-os ao longo do caminho.",
                "timeline": " ongoing",
                "rationale": "Esperança equilibrada encontra alegria no percurso.",
            },
        ],
        "relacionamento": [
            {
                "title": "Iniciar uma conversa honesta",
                "description": "Programe um momento para dialogar abertamente sobre a situação, sem acusações.",
                "timeline": "Esta semana",
                "rationale": "Comunicação clara é a base de relacionamentos saudáveis.",
            },
            {
                "title": "Praticar escuta ativa",
                "description": "Na próxima conversa importante, foque em entender antes de ser entendido. Repita o que ouviu.",
                "timeline": "Próximas conversas",
                "rationale": "Escuta genuína constrói confiança e reduz mal-entendidos.",
            },
            {
                "title": "Estabelecer limites saudáveis",
                "description": "Defina claramente o que você pode e não pode aceitar.Communique isso com clareza.",
                "timeline": "Esta semana",
                "rationale": "Limites claros protegem a relação e o bem-estar individual.",
            },
        ],
        "decisao": [
            {
                "title": "Priorizar os critérios de decisão",
                "description": "Liste seus critérios em ordem de importância. Use-os como filtro para todas as opções.",
                "timeline": "Hoje",
                "rationale": "Critérios claros simplificam decisões complexas.",
            },
            {
                "title": "Definir um ponto de decisão final",
                "description": "Estabeleça quando você deve tomar a decisão, independentemente de ter todas as informações.",
                "timeline": "Definir hoje",
                "rationale": "Um prazo previne a paralisia por análise.",
            },
            {
                "title": "Testar a decisão com um experimento",
                "description": "Antes de se comprometer totalmente, faça um teste em pequena escala.",
                "timeline": "Próximas 2 semanas",
                "rationale": "Experimentação reduz riscos e fornece dados reais.",
            },
        ],
        "trabalho": [
            {
                "title": "Mapear suas opções profissionais",
                "description": "Liste todas as possibilidades concretas disponíveis para você agora, incluindo as que parecem improváveis.",
                "timeline": "Esta semana",
                "rationale": "Opções invisíveis não podem ser escolhidas.",
            },
            {
                "title": "Atualizar seu perfil profissional",
                "description": "Dedique tempo para melhorar sua presença profissional online ou offline.",
                "timeline": "Próximos 7 dias",
                "rationale": "Preparação ativa aumenta as oportunidades.",
            },
            {
                "title": "Solicitar feedback construtivo",
                "description": "Peça a alguém de confiança que avalie seus pontos fortes e áreas de melhoria no trabalho.",
                "timeline": "Esta semana",
                "rationale": "Feedback externo revela pontos cegos.",
            },
        ],
        "financeiro": [
            {
                "title": "Documentar sua situação financeira atual",
                "description": "Liste todas as receitas, despesas, ativos e passivos de forma organizada.",
                "timeline": "Hoje",
                "rationale": "Você não pode melhorar o que não mede.",
            },
            {
                "title": "Definir um objetivo financeiro claro",
                "description": "Estabeleça uma meta específica: quanto, para quê, em quanto tempo.",
                "timeline": "Esta semana",
                "rationale": "Metas claras direcionam ações financeiras.",
            },
            {
                "title": "Criar um plano de ação financeira",
                "description": "Desenvolva passos concretos para atingir seu objetivo, mesmo que pequenos.",
                "timeline": "Próximos 7 dias",
                "rationale": "Planos estruturados transformam intenções em resultados.",
            },
        ],
        "saude": [
            {
                "title": "Agendar uma avaliação profissional",
                "description": "Se há preocupações com saúde, marque uma consulta com o profissional adequado.",
                "timeline": "Esta semana",
                "rationale": "Orientação profissional é insubstituível para questões de saúde.",
            },
            {
                "title": "Estabelecer uma rotina de autocuidado",
                "description": "Identifique uma atividade que promova seu bem-estar e incorpore-a em sua rotina diária.",
                "timeline": "Hoje",
                "rationale": "Cuidados preventivos são mais eficazes que correções tardias.",
            },
            {
                "title": "Monitorar sinais importantes",
                "description": "Observe e anote quaisquer mudanças ou sintomas que possam ser relevantes.",
                "timeline": " ongoing",
                "rationale": "Documentação ajuda profissionais de saúde a fazer diagnósticos precisos.",
            },
        ],
    }

    # Collect actions based on detected themes
    detected_themes = set(analysis.themes) if analysis.themes else set()
    added_titles = set()

    for theme in detected_themes:
        theme_lower = theme.lower()
        for action_theme, theme_action_list in theme_actions.items():
            if action_theme in theme_lower or theme_lower in action_theme:
                for action in theme_action_list:
                    if action["title"] not in added_titles:
                        actions.append(action)
                        added_titles.add(action["title"])

    # Add card-specific actions
    for card in analysis.cards:
        if card.is_reversed():
            # For reversed cards, suggest reflection actions
            if "refletir sobre a energia bloqueada" not in added_titles:
                actions.append({
                    "title": f"Refletir sobre a energia de {card.name}",
                    "description": f"A carta {card.name} aparece invertida. Reserve um tempo para contemplar o que pode estar bloqueado ou expresso de forma oposta em sua situação.",
                    "timeline": "Esta semana",
                    "rationale": "Cartas invertidas indicam áreas que necessitam de atenção interior.",
                })
                added_titles.add("refletir sobre a energia bloqueada")
        else:
            # For upright cards, suggest forward action
            if "agir com base na energia positiva" not in added_titles:
                actions.append({
                    "title": "Avançar com a energia atual",
                    "description": "A leitura indica uma fase favorável para ação. Identifique uma área onde você pode fazer progresso hoje.",
                    "timeline": "Hoje",
                    "rationale": "Momentos favoráveis devem ser aproveitados com atenção.",
                })
                added_titles.add("agir com a energia positiva")

    # Add generic actions if none specific found
    if not actions:
        actions.append({
            "title": "Revisar suas conclusões",
            "description": "Releia esta análise em alguns dias e verifique se suas perspectivas mudaram.",
            "timeline": "Próximos 7 dias",
            "rationale": "Reflexão periódica aprofunda o autoconhecimento.",
        })
        actions.append({
            "title": "Documentar seus insights",
            "description": "Anote as principais lições desta leitura em um diário ou arquivo pessoal.",
            "timeline": "Hoje",
            "rationale": "Registrar insights evita que se percam com o tempo.",
        })
        actions.append({
            "title": "Agendar um follow-up",
            "description": "Programe um momento no futuro para revisitar esta análise e verificar seu progresso.",
            "timeline": "Próximas 2 semanas",
            "rationale": "Acompanhamento cria accountability pessoal.",
        })

    # Display each action with timeline
    lines.append("## Passos de Ação")
    lines.append("")
    for i, action in enumerate(actions[:6], start=1):  # Limit to 6 actions
        lines.append(f"### {i}. {action['title']}")
        lines.append("")
        lines.append(f"{action['description']}")
        lines.append("")
        lines.append(f"**Prazo:** {action['timeline']}")
        lines.append(f"**Fundamento:** {action['rationale']}")
        lines.append("")

    # Timeline overview
    lines.append("---")
    lines.append("")
    lines.append("## Visão Geral do Timeline")
    lines.append("")

    # Categorize actions by timeline
    today_actions = [a for a in actions if "hoje" in a["timeline"].lower()]
    week_actions = [a for a in actions if "semana" in a["timeline"].lower()]
    ongoing_actions = [a for a in actions if "ongoing" in a["timeline"].lower()]

    if today_actions:
        lines.append("### Ações para Hoje")
        for action in today_actions:
            lines.append(f"- [{action['title']}](#{action['title'].lower().replace(' ', '-')})")
        lines.append("")

    if week_actions:
        lines.append("### Ações para Esta Semana")
        for action in week_actions:
            lines.append(f"- [{action['title']}](#{action['title'].lower().replace(' ', '-')})")
        lines.append("")

    if ongoing_actions:
        lines.append("### Ações Contínuas")
        for action in ongoing_actions:
            lines.append(f"- [{action['title']}](#{action['title'].lower().replace(' ', '-')})")
        lines.append("")

    # Commitment section
    lines.append("---")
    lines.append("")
    lines.append("## Compromisso de Ação")
    lines.append("")
    lines.append("Para transformar reflexão em resultados, escolha **duas ações** desta lista para priorizar esta semana:")
    lines.append("")
    lines.append("- [ ] Ação prioritária 1: ________________")
    lines.append("- [ ] Ação prioritária 2: ________________")
    lines.append("")
    lines.append("Registre aqui seu compromisso:")
    lines.append("")
    lines.append("_" * 40)
    lines.append("")

    # Closing reminder
    lines.append("---")
    lines.append("")
    lines.append("## Lembrete Final")
    lines.append("")
    lines.append("⚠️  Plano é caminho, não destino. Permaneça flexível e ajuste conforme necessário. O Baralho Cigano oferece reflexão; a ação é sua responsabilidade. Cada pequeno passo na direção certa é progresso válido.")
    lines.append("")
    lines.append("O melhor momento para começar é agora. Sua próxima ação está ao seu alcance.")

    return "\n".join(lines)
