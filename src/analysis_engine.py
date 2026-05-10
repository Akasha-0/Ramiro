"""Motor de análise simbólico-estratégica — Sistema de Clareza.

Módulo central que executa a análise sobre o input estruturado:
- symbol_mapping: mapeia keywords/cartas ao catálogo simbólico
- theme_detection: detecta temas predominantes
- risk_identification: identifica riscos e cuidados necessários
- decision_mapping: gera caminhos de decisão possíveis

Recebe StructuredInput (types.py) e retorna AnalysisResult (types.py).
"""

import logging
from typing import Optional

from src.symbols import (
    CiganoSymbol,
    get_all_symbols,
    get_symbol_by_name,
    match_keyword,
)
from src.types import AnalysisResult, CardPosition, CrossCardPattern, StructuredInput

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Temas possíveis (unidos dos definidos em symbols.py)
# ----------------------------------------------------------------------

_THEMES = [
    "trabalho",
    "relação",
    "saúde",
    "espiritual",
    "dinheiro",
    "viagem",
    "família",
]


# ----------------------------------------------------------------------
# Temas de risco (palavras que sinalizam atenção especial)
# ----------------------------------------------------------------------

_RISK_TRIGGERS: list[tuple[list[str], str]] = [
    (["perigo", "ameaça", "ataque", "violência", "agressão", "medo", "assédio"], "risco_pessoal"),
    (["traição", "engano", "mentira", "manipulação", "falsa"], "risco_relacional"),
    (["perda", "morte", "luto", "fim", "encerramento"], "risco_emeracional"),
    (["doença", "dor", "sofrimento", "exaustão", "crise"], "risco_saúde"),
    (["financeiro", "dívida", "falência", "dinheiro", "pobreza"], "risco_financeiro"),
    (["bloqueio", "obstáculo", "paralisia", "imobilidade"], "risco_bloqueio"),
]

# ----------------------------------------------------------------------
# Contexto de decisão (palavras que indicam necessidade de escolha)
# ----------------------------------------------------------------------

_DECISION_TRIGGERS: list[tuple[list[str], str]] = [
    (["escolher", "decidir", "encruzilhada", "alternativa", "opção", "caminho"], "escolha_pendente"),
    (["mudar", "transformar", "renovar", "reinício", "novo"], "mudança_posterior"),
    (["início", "começar", "nascimento", "chegada"], "início_pendente"),
    (["fim", "terminar", "encerrar", "fechar", "sair"], "encerramento_pendente"),
    (["compromisso", "união", "casamento", "aliança", "vínculo"], "compromisso_pendente"),
    (["separação", "ruptura", "corte", "divisão"], "separação_pendente"),
]


# ----------------------------------------------------------------------
# Mapeamento simbólico para keywords do input
# ----------------------------------------------------------------------


def _map_keyword_to_symbol(keyword: str) -> list[CiganoSymbol]:
    """Mapeia uma keyword a símbolos do Baralho Cigano.

    Args:
        keyword: Palavra-chave a buscar no índice simbólico.

    Returns:
        Lista de CiganoSymbol correspondentes (pode ser vazia).
    """
    if not keyword or len(keyword) < 2:
        return []

    # Busca no índice de palavras-chave
    symbols = match_keyword(keyword)
    if symbols:
        logger.debug("Keyword %r → %d símbolos encontrados", keyword, len(symbols))
        return symbols

    # Tentativa fuzzy: buscar por nome aproximado
    name_match = get_symbol_by_name(keyword)
    if name_match:
        return [name_match]

    return []


# ----------------------------------------------------------------------
# Interpretação contextual por posição na tiragem
# ----------------------------------------------------------------------


def _get_position_context_text(
    position: int, context: Optional[str], symbol: CiganoSymbol
) -> Optional[str]:
    """Gera texto contextual para uma posição específica na tiragem.

    Args:
        position: Posição da carta (1-based).
        context: Contexto posicional (ex: "passado", "presente", "futuro").
        symbol: Símbolo da carta para adaptação contextual.

    Returns:
        String com interpretação contextual ou None se não aplicável.
    """
    if not context:
        return None

    normalized = context.lower().strip()
    interpretations: dict[str, str] = {
        "passado": "Esta carta representa o passado — uma situação que já aconteceu e "
        "influencia o presente. A energia de {name} neste momento indica "
        "que {past_hint}.",
        "presente": "Esta carta representa o momento atual — a situação que está "
        "acontecendo agora. A energia de {name} neste ponto indica "
        "que {present_hint}.",
        "futuro": "Esta carta representa o futuro — uma possibilidade que está "
        "se desenhando. A energia de {name} aponta para "
        "que {future_hint}.",
        "influência": "Esta carta representa uma influência externa — algo que "
        "afeta a situação de fora. A energia de {name} sugere "
        "que {influence_hint}.",
        "base": "Esta carta representa a base ou fundamento — o alicerce "
        "da situação. A energia de {name} indica "
        "que {base_hint}.",
        "ação": "Esta carta representa a ação necessária — o que deve ser "
        "feito. A energia de {name} aponta para "
        "que {action_hint}.",
        "resultado": "Esta carta representa o resultado provável — o desfecho "
        "mais provável. A energia de {name} indica "
        "que {result_hint}.",
    }

    if normalized not in interpretations:
        return None

    # Dicas contextuais baseadas no símbolo
    past_hints = {
        "espiritual": "um ciclo antigo está encerrando e influenciando o presente.",
        "trabalho": "uma decisão profissional passada molda a situação atual.",
        "relação": "um relacionamento anterior deixa marcas na situação presente.",
        "família": "assuntos familiares do passado afetam o momento atual.",
        "saúde": "uma condição passada influencia o bem-estar presente.",
        "dinheiro": "decisões financeiras passadas impactam a situação atual.",
        "viagem": "uma jornada anterior trouxe mudanças que afetam agora.",
    }

    present_hints = {
        "espiritual": "transformação interior está em curso neste momento.",
        "trabalho": "oportunidade ou desafio profissional se apresenta agora.",
        "relação": "dinâmica relacional importante está em jogo agora.",
        "família": "assuntos domésticos requerem atenção neste momento.",
        "saúde": "cuidado com o bem-estar físico e emocional é necessário.",
        "dinheiro": "decisão financeira importante está no momento presente.",
        "viagem": "uma mudança de cenário pode trazer clareza agora.",
    }

    future_hints = {
        "espiritual": "mudança profunda está se desenhando no horizonte.",
        "trabalho": "nova oportunidade profissional está por vir.",
        "relação": "desenvolvimento significativo no campo relacional está próximo.",
        "família": "evento familiar importante está por acontecer.",
        "saúde": "cuidado preventivo trará benefícios futuros.",
        "dinheiro": "prospéridade está se desenhando no caminho.",
        "viagem": "jornada transformadora está se aproximando.",
    }

    influence_hints = {
        "espiritual": "energia externa está afetando sua situação de forma sutil.",
        "trabalho": "influência externa está moldando o ambiente profissional.",
        "relação": "terceira pessoa ou fator externo afeta a dinâmica relacional.",
        "família": "influência familiar externa está em jogo.",
        "saúde": "fatores externos podem estar afetando seu bem-estar.",
        "dinheiro": "influência externa afeta sua situação financeira.",
        "viagem": "fator externo pode desencadear uma mudança importante.",
    }

    base_hints = {
        "espiritual": "suas bases espirituais são fortes e sustenta você.",
        "trabalho": "fundamento profissional é sólido, use-o como base.",
        "relação": "relacionamento baseia-se em pilares fortes.",
        "família": "raízes familiares oferecem estabilidade importante.",
        "saúde": "constituição básica oferece抵抗力.",
        "dinheiro": "base financeira é a foundation atual.",
        "viagem": "experiências passadas são a base para decisões.",
    }

    action_hints = {
        "espiritual": "reflexão e autoconhecimento são as ações recomendadas.",
        "trabalho": "comunicação clara e objetiva é necessária agora.",
        "relação": "diálogo aberto e honesto é a ação recomendada.",
        "família": "cuidado e atenção ao ambiente doméstico são necessários.",
        "saúde": "busque cuidado preventivo e equilíbrio.",
        "dinheiro": "avaliação cuidadosa antes de decisões financeiras.",
        "viagem": "considere expandir horizontes e explorar novas possibilidades.",
    }

    result_hints = {
        "espiritual": "crescimento espiritual e clareza são prováveis.",
        "trabalho": "sucesso profissional e reconhecimento são prováveis.",
        "relação": "aprofundamento ou transformação relacional é provável.",
        "família": "fortalecimento dos vínculos familiares é provável.",
        "saúde": "melhoria do bem-estar geral é provável.",
        "dinheiro": "estabilidade ou crescimento financeiro é provável.",
        "viagem": "experiência transformadora e novos aprendizados são prováveis.",
    }

    hint_maps = {
        "passado": past_hints,
        "presente": present_hints,
        "futuro": future_hints,
        "influência": influence_hints,
        "base": base_hints,
        "ação": action_hints,
        "resultado": result_hints,
    }

    hints = hint_maps.get(normalized, {})
    hint = hints.get(symbol.theme, f"a energia de {symbol.name} é significativa neste contexto.")

    template = interpretations[normalized]
    return template.format(
        name=symbol.name,
        past_hint=hints.get("espiritual", ""),
        present_hint=hints.get("espiritual", ""),
        future_hint=hints.get("espiritual", ""),
        influence_hint=hints.get("espiritual", ""),
        base_hint=hints.get("espiritual", ""),
        action_hint=hints.get("espiritual", ""),
        result_hint=hints.get("espiritual", ""),
    ) + f" {hint}"


# ----------------------------------------------------------------------
# Geração de interpretações para cartas da tiragem
# ----------------------------------------------------------------------


def _interpret_card_position(
    card: CardPosition, all_symbols: list[CiganoSymbol]
) -> str:
    """Gera interpretação contextualizada para uma carta na tiragem.

    Args:
        card: CardPosition com posição e nome da carta.
        all_symbols: Lista completa de símbolos (para busca por nome).

    Returns:
        String com interpretação contextualizada da carta.
    """
    symbol = get_symbol_by_name(card.card_name)
    if symbol is None:
        # Tentar busca por palavra-chave no nome
        matches = match_keyword(card.card_name)
        if matches:
            symbol = matches[0]

    if symbol is None:
        logger.warning("Carta não encontrada no catálogo: %r", card.card_name)
        return f"Carta '{card.card_name}' — mapeamento simbólico não encontrado."

    lines = [
        f"**{card.position}. {symbol.name}**",
        "",
        f"_{symbol.interpretation}_",
        "",
    ]

    # Adicionar contexto posicional se disponível
    if card.position_context:
        context_interpretation = _get_position_context_text(
            card.position, card.position_context, symbol
        )
        if context_interpretation:
            lines.append(f"> 📍 {context_interpretation}")
            lines.append("")

    if symbol.advice:
        lines.append(f"> 💡 {symbol.advice}")

    if symbol.reversed_meaning:
        lines.append("")
        lines.append(f"⚠️ *Sentido invertido: {symbol.reversed_meaning}*")

    return "\n".join(lines)


# ----------------------------------------------------------------------
# Detecção de temas predominantes
# ----------------------------------------------------------------------


def _detect_themes(
    symbols: list[CiganoSymbol], raw_content: str
) -> list[str]:
    """Detecta os temas predominantes a partir dos símbolos e conteúdo.

    Args:
        symbols: Lista de símbolos encontrados no input.
        raw_content: Conteúdo bruto para análise complementar.

    Returns:
        Lista ordenada de temas predominantes (por frequência).
    """
    if not symbols:
        return []

    # Contagem por tema
    from collections import Counter

    theme_counts = Counter(s.theme for s in symbols)
    top_themes = [t for t, _ in theme_counts.most_common()]

    logger.debug("Temas detectados: %s", top_themes)
    return top_themes


# ----------------------------------------------------------------------
# Identificação de riscos
# ----------------------------------------------------------------------


def _identify_risks(
    symbols: list[CiganoSymbol],
    raw_content: str,
    themes: list[str],
) -> list[str]:
    """Identifica riscos e cuidados necessários.

    Args:
        symbols: Lista de símbolos encontrados.
        raw_content: Conteúdo bruto para análise de triggers.
        themes: Temas predominantes detectados.

    Returns:
        Lista de riscos identificados como strings descritivas.
    """
    risks: list[str] = []
    seen_categories: set[str] = set()

    # Verificar símbolos com keywords de risco
    risk_keywords = {
        "perigo": ["lobo", "serpente", "cobra"],
        "bloqueio": ["forca", "nuvens"],
        "perda": ["caixão", "morte"],
        "sofrimento": ["cruz", "cruz de são andré"],
    }

    for symbol in symbols:
        for category, trigger_cards in risk_keywords.items():
            if symbol.name.lower() in trigger_cards:
                if category not in seen_categories:
                    seen_categories.add(category)
                    risks.append(_RISK_DESCRIPTIONS.get(category, f"Risco em {category}"))

    # Verificar triggers de risco no conteúdo
    content_lower = raw_content.lower()
    for trigger_words, category in _RISK_TRIGGERS:
        for word in trigger_words:
            if len(word) >= 3 and word in content_lower:
                if category not in seen_categories:
                    seen_categories.add(category)
                    risks.append(_RISK_DESCRIPTIONS.get(category, f"Risco: {category}"))
                break

    logger.debug("Riscos identificados: %s", risks)
    return risks


_RISK_DESCRIPTIONS: dict[str, str] = {
    "risco_pessoal": "⚠️ Risco pessoal detectado —有必要留意人身安全和界限。",
    "risco_relacional": "⚠️ Risco relacional detectado — relaciones podem envolver engano ou manipulação.",
    "risco_emeracional": "⚠️ Risco emocional detectado — momento propício para processar perdas e encerrar ciclos.",
    "risco_saúde": "⚠️ Risco à saúde detectado — atenção ao corpo e à mente é necessária.",
    "risco_financeiro": "⚠️ Risco financeiro detectado — decisões económicas requerem cautela.",
    "risco_bloqueio": "⚠️ Risco de bloqueio detectado — pode haver obstáculo que impede progresso.",
}


# ----------------------------------------------------------------------
# Mapeamento de decisões
# ----------------------------------------------------------------------


def _map_decisions(
    symbols: list[CiganoSymbol],
    raw_content: str,
    themes: list[str],
) -> list[str]:
    """Gera caminhos de decisão possíveis a partir dos símbolos.

    Args:
        symbols: Lista de símbolos encontrados.
        raw_content: Conteúdo bruto para análise de triggers.
        themes: Temas predominantes detectados.

    Returns:
        Lista de caminhos de decisão como strings descritivas.
    """
    decisions: list[str] = []
    seen_categories: set[str] = set()

    # Mapa de símbolos para tipos de decisão
    decision_map: dict[str, str] = {
        "cruz de são andré": "🔀 Encruzilhada: duas direções disponíveis — avalie prós e contras antes de escolher.",
        "cruz": "⏳ Momento de provação: a decisão pode esperar; busque apoio primeiro.",
        "ancora": "🔒 Momento de consolidação: não é hora de mudar — ancore-se no que já tem.",
        "cegonha": "🌱 Novo começo disponível: prepare-se para receber algo novo.",
        "morte": "🔄 Transformação iminente: permita que o velho termine para o novo nascer.",
        "florista": "🌸 Oportunidade de cultivo: ações pacientes agora trarão resultados futuros.",
        "mercado": "💼 Momento propício para negócios: condições favoráveis para negociação.",
        "anel": "💍 Compromisso pendente: esta decisão terá consequências duradouras.",
        "flecha": "🎯 Direção clara: defina seu objetivo com precisão antes de agir.",
        "casa": "🏠 Ação doméstica: fortaleça suas bases antes de expandir.",
        "cigano": "🌍 Perspectiva externa: considere o ponto de vista de alguém diferente.",
        "coruja": "🔍 Investigação necessária: busque mais informação antes de decidir.",
    }

    for symbol in symbols:
        symbol_key = symbol.name.lower()
        if symbol_key in decision_map:
            decisions.append(decision_map[symbol_key])

    # Verificar triggers de decisão no conteúdo
    content_lower = raw_content.lower()
    for trigger_words, category in _DECISION_TRIGGERS:
        for word in trigger_words:
            if len(word) >= 3 and word in content_lower:
                if category not in seen_categories:
                    seen_categories.add(category)
                    decisions.append(_DECISION_DESCRIPTIONS.get(category, f"Decisão pendente: {category}"))
                break

    # Se nenhum decisão específica encontrada mas há símbolos, generic fallback
    if not decisions and symbols:
        decisions.append(
            "📋 Múltiplos símbolos detectados — uma análise mais aprofundada das relações entre as cartas trará mais clareza."
        )

    logger.debug("Decisões mapeadas: %s", decisions)
    return decisions


_DECISION_DESCRIPTIONS: dict[str, str] = {
    "escolha_pendente": "🔀 Momento de escolha: avalie suas opções antes de agir.",
    "mudança_posterior": "🔄 Transformação identificada: prepare-se para uma mudança significativa.",
    "início_pendente": "🌱 Novo começo detectado: este é um momento propício para iniciar algo.",
    "encerramento_pendente": "🏁 Ciclo se encerrando: permita que o fim ocorra naturalmente.",
    "compromisso_pendente": "💍 Compromisso detectado: avalie as consequências de longo prazo.",
    "separação_pendente": "✂️ Separação necessária: às vezes é preciso cortar para avançar.",
}


# ----------------------------------------------------------------------
# Geração do plano prático
# ----------------------------------------------------------------------


def _generate_practical_plan(
    symbols: list[CiganoSymbol],
    themes: list[str],
    risks: list[str],
) -> str:
    """Gera um plano prático de ação com base na análise.

    Args:
        symbols: Lista de símbolos predominantes.
        themes: Temas predominantes.
        risks: Riscos identificados.

    Returns:
        String com plano prático estruturado em markdown.
    """
    lines: list[str] = ["### Plano de Ação Sugerido\n"]

    if not symbols:
        lines.append("- Aprofundar a análise com mais contexto para gerar recomendações.")
        return "\n".join(lines)

    # Primeiro passo: baseado no símbolo mais relevante (primeiro da lista)
    if symbols:
        top_symbol = symbols[0]
        lines.append(f"1. **Foco principal ({top_symbol.name})**: {top_symbol.advice}")
        lines.append("")

    # Segundo passo: baseado no tema predominante
    if themes:
        theme_advice = _THEME_ADVICES.get(themes[0], "")
        if theme_advice:
            lines.append(f"2. **Atenção ao tema {themes[0]}**: {theme_advice}")
            lines.append("")

    # Terceiro passo: cuidados específicos
    if risks:
        lines.append("3. **Cuidados necessários**:")
        for risk in risks[:3]:  # Limitar a 3 riscos principais
            # Remove emoji e formatação para texto corrido
            risk_text = risk.split("—", 1)[-1].strip() if "—" in risk else risk
            lines.append(f"   - {risk_text}")
        lines.append("")

    # Quarto passo: próximos passos
    lines.append("4. **Próximos passos**:")

    # Gerar passos com base nos símbolos restantes
    for symbol in symbols[1:4]:  # até 3 símbolos seguintes
        step = _symbol_to_action(symbol)
        if step:
            lines.append(f"   - {step}")

    if len(symbols) <= 1:
        lines.append("   - Aguarde mais informações para detalhamento.")

    return "\n".join(lines)


_THEME_ADVICES: dict[str, str] = {
    "trabalho": "Dê atenção a decisões profissionais e à comunicação com colegas e superiores.",
    "relação": "Invista em qualidade nos relacionamentos e comunicação clara com pessoas próximas.",
    "saúde": "Priorize o cuidado com o corpo e a mente — pequenos gestos.preventivos fazem diferença.",
    "espiritual": "Reserve tempo para reflexão e autoconhecimento — a resposta vem de dentro.",
    "dinheiro": "Avalie com cautela decisões financeiras — proteja seus recursos.",
    "viagem": "Considere mudanças de ambiente ou perspectiva — sair do comum traz insights.",
    "família": "Fortaleça vínculos com pessoas próximas e cuide do seu ambiente doméstico.",
}


def _symbol_to_action(symbol: CiganoSymbol) -> str:
    """Converte um símbolo em uma ação prática sugerida.

    Args:
        symbol: Símbolo a converter.

    Returns:
        String com ação prática ou string vazia.
    """
    action_map: dict[str, str] = {
        "cigano": "Converse com alguém de perspectiva diferente.",
        "trevo": "Mantenha-se alerta a oportunidades inesperadas.",
        "navio": "Considere uma mudança de cenário.",
        "casa": "Cuide do seu ambiente eBase.",
        "árvore": "Invista em crescimento sustentável.",
        "nuvens": "Aguarde clareza antes de decidir.",
        "cobra": "Avalie quem está ao seu redor com cuidado.",
        "caixão": "Permita que ciclos se encerrem.",
        "buquê": "Celebre conquistas, pequenas ou grandes.",
        "forca": "Mude sua perspectiva sobre a situação.",
        "serpente": "Busque conhecimento profundo.",
        "morte": "Permita que transformações ocorram.",
        "cegonha": "Prepare-se para receber algo novo.",
        "cão": "Valorize seus aliados leais.",
        "lobo": "Identifique ameaças e aja com firmeza.",
        "cabana": "Busque acolhimento e simplicidade.",
        "estrela": "Mantenha esperança e clareza.",
        "coruja": "Observe mais, fale menos.",
        "lua": "Confie na sua intuição.",
        "machado": "Avalie o que precisa ser cortado.",
        "facho": "Use sua energia para iluminar.",
        "cruz": "Peça apoio se precisar.",
        "cruz de são andré": "Escolha com consciência — ambas direções têm peso.",
        "urso": "Busque proteção e cuidado.",
        "estrelas": "Explore diferentes possibilidades.",
        "mercado": "Negocie com vantagem.",
        "beijo": "Exprima afeto e busque reconciliação.",
        "livro": "Busque conhecimento e informação.",
        "carta": "Fique atento a mensagens importantes.",
        "florista": "Cultive com paciência e cuidado.",
        "anel": "Avalie compromissos com seriedade.",
        "pompom": "Preste atenção a intermediários.",
        "peixe": "Siga sua intuição para prosperidade.",
        "âncora": "Consolide o que já tem.",
        "flecha": "Defina sua direção com precisão.",
        "cafezinho": "Reserve tempo para convívio social.",
    }

    return action_map.get(symbol.name.lower(), f"Considere o tema {symbol.name} em sua análise.")


# ----------------------------------------------------------------------
# Detecção de padrões entre cartas (cross-card patterns)
# ----------------------------------------------------------------------


def _detect_cross_card_patterns(
    cards: list[CardPosition],
) -> list[CrossCardPattern]:
    """Detecta padrões significativos entre múltiplas cartas na tiragem.

    Args:
        cards: Lista de posições de cartas na tiragem.

    Returns:
        Lista de CrossCardPattern detectados.
    """
    if not cards or len(cards) < 2:
        return []

    patterns: list[CrossCardPattern] = []

    # 1. Detectar repetições numéricas (mesma carta aparece em múltiplas posições)
    numeric_repeat_patterns = _detect_numeric_repeats(cards)
    patterns.extend(numeric_repeat_patterns)

    # 2. Detectar sequências numéricas (cartas em ordem consecutiva)
    sequence_patterns = _detect_numeric_sequences(cards)
    patterns.extend(sequence_patterns)

    # 3. Detectar clusters temáticos (cartas do mesmo tema)
    theme_clusters = _detect_theme_clusters(cards)
    patterns.extend(theme_clusters)

    # 4. Detectar desequilíbrios elementais (distribuição de temas)
    elemental_imbalances = _detect_elemental_imbalances(cards)
    patterns.extend(elemental_imbalances)

    logger.debug("Padrões cruzados detectados: %d", len(patterns))
    return patterns


def _detect_numeric_repeats(cards: list[CardPosition]) -> list[CrossCardPattern]:
    """Detecta quando a mesma carta aparece múltiplas vezes.

    Args:
        cards: Lista de posições de cartas.

    Returns:
        Lista de padrões de repetição encontrados.
    """
    from collections import Counter

    if len(cards) < 2:
        return []

    card_names = [c.card_name.lower() for c in cards]
    name_counts = Counter(card_names)

    patterns: list[CrossCardPattern] = []

    for name, count in name_counts.items():
        if count >= 2:
            positions = [c.position for c in cards if c.card_name.lower() == name]

            interpretation = (
                f"A carta '{name.title()}' aparece {count} vezes na tiragem "
                f"(posições {', '.join(map(str, positions))}). "
                f"Este reforço indica que seu significado está sendo amplificado "
                f"significativamente. A energia de '{name.title()}' é dominante "
                f"neste momento — preste muita atenção a esta mensagem."
            )

            strength = "forte" if count >= 3 else "moderado"

            patterns.append(CrossCardPattern(
                pattern_type="numeric_repeat",
                card_ids=positions,
                interpretation=interpretation,
                strength=strength,
            ))

    return patterns


def _detect_numeric_sequences(cards: list[CardPosition]) -> list[CrossCardPattern]:
    """Detecta sequências numéricas (cartas em posições consecutivas).

    Args:
        cards: Lista de posições de cartas.

    Returns:
        Lista de padrões de sequência encontrados.
    """
    if len(cards) < 2:
        return []

    # Ordenar por posição
    sorted_cards = sorted(cards, key=lambda c: c.position)
    positions = [c.position for c in sorted_cards]

    # Verificar sequências de pelo menos 3 posições consecutivas
    sequences: list[list[int]] = []
    current_seq: list[int] = [positions[0]]

    for i in range(1, len(positions)):
        if positions[i] == current_seq[-1] + 1:
            current_seq.append(positions[i])
        else:
            if len(current_seq) >= 3:
                sequences.append(current_seq)
            current_seq = [positions[i]]

    # Verificar última sequência
    if len(current_seq) >= 3:
        sequences.append(current_seq)

    patterns: list[CrossCardPattern] = []

    for seq in sequences:
        card_names = [c.card_name for c in sorted_cards if c.position in seq]

        interpretation = (
            f"Posições consecutivas ({', '.join(map(str, seq))}) revelam "
            f"um fluxo: {' → '.join(card_names)}. "
            f"Este encadeamento sugere uma progressão natural da situação, "
            f"onde cada carta contribui para o desenvolvimento da próxima. "
            f"A sequência indica que os eventos estão se desenrolando de "
            f"forma fluida econnected."
        )

        patterns.append(CrossCardPattern(
            pattern_type="numeric_sequence",
            card_ids=seq,
            interpretation=interpretation,
            strength="moderado",
        ))

    return patterns


def _detect_theme_clusters(cards: list[CardPosition]) -> list[CrossCardPattern]:
    """Detecta quando múltiplas cartas compartilham o mesmo tema.

    Args:
        cards: Lista de posições de cartas.

    Returns:
        Lista de padrões de cluster temático encontrados.
    """
    if len(cards) < 3:
        return []

    from collections import Counter

    # Mapear cartas para símbolos e seus temas
    card_themes: dict[int, str] = {}
    for card in cards:
        symbol = get_symbol_by_name(card.card_name)
        if symbol:
            card_themes[card.position] = symbol.theme

    if len(card_themes) < 3:
        return []

    # Agrupar por tema
    theme_positions: dict[str, list[int]] = {}
    for position, theme in card_themes.items():
        if theme not in theme_positions:
            theme_positions[theme] = []
        theme_positions[theme].append(position)

    patterns: list[CrossCardPattern] = []

    for theme, positions in theme_positions.items():
        if len(positions) >= 2:
            theme_names = {
                "trabalho": "Trabalho e carreira",
                "relação": "Relacionamentos",
                "saúde": "Saúde e vitalidade",
                "espiritual": "Espiritualidade",
                "dinheiro": "Finanças",
                "viagem": "Viagem e mudanças",
                "família": "Família e lar",
            }

            theme_display = theme_names.get(theme, theme.title())

            interpretation = (
                f"Cluster de '{theme_display}' detectado nas posições "
                f"{', '.join(map(str, sorted(positions)))}. "
                f"Múltiplas cartas neste tema indicam que esta área da vida "
                f"requer atenção especial. A concentração de energia em "
                f"'{theme_display}' sugere que a situação está sendo moldada "
                f"por fatores relacionados a este domínio."
            )

            strength = "forte" if len(positions) >= 3 else "moderado"

            patterns.append(CrossCardPattern(
                pattern_type="theme_cluster",
                card_ids=sorted(positions),
                interpretation=interpretation,
                strength=strength,
            ))

    return patterns


def _detect_elemental_imbalances(cards: list[CardPosition]) -> list[CrossCardPattern]:
    """Detecta desequilíbrios na distribuição de elementos/temas.

    Args:
        cards: Lista de posições de cartas.

    Returns:
        Lista de padrões de desequilíbrio encontrados.
    """
    if len(cards) < 4:
        return []

    from collections import Counter

    # Mapear para temas
    themes: list[str] = []
    for card in cards:
        symbol = get_symbol_by_name(card.card_name)
        if symbol:
            themes.append(symbol.theme)

    if len(themes) < 4:
        return []

    theme_counts = Counter(themes)

    # Verificar se há dominância clara (> 50% de um único tema)
    total = len(themes)
    patterns: list[CrossCardPattern] = []

    for theme, count in theme_counts.items():
        percentage = (count / total) * 100
        if percentage >= 60:
            dominant_positions = [
                c.position for c in cards
                if get_symbol_by_name(c.card_name)
                and get_symbol_by_name(c.card_name).theme == theme
            ]

            theme_names = {
                "trabalho": "trabalho/carrreira",
                "relação": "relacionamentos",
                "saúde": "saúde",
                "espiritual": "espiritualidade",
                "dinheiro": "finanças",
                "viagem": "viagem/mudanças",
                "família": "família/lar",
            }

            theme_display = theme_names.get(theme, theme)

            interpretation = (
                f"Desequilíbrio detectado: {percentage:.0f}% das cartas "
                f"({count}/{total}) pertencem ao tema '{theme_display}'. "
                f"Isto indica que a energia está fortemente concentrada "
                f"nesta área. Embora revele sobre o que você deve focar, "
                f"também sugere cuidado para não negligenciar outros "
                f"aspectos da vida. Equilibre seu foco com atenção aos "
                f"detalhes que não aparecem na tiragem."
            )

            patterns.append(CrossCardPattern(
                pattern_type="elemental_imbalance",
                card_ids=sorted(dominant_positions),
                interpretation=interpretation,
                strength="moderado",
            ))

    return patterns


# ----------------------------------------------------------------------
# Motor principal de análise
# ----------------------------------------------------------------------


class AnalysisEngine:
    """Motor de análise simbólico-estratégica.

    Recebe StructuredInput e produz AnalysisResult com:
    - Mapeamento simbólico (keywords → símbolos)
    - Detecção de temas predominantes
    - Identificação de riscos
    - Mapeamento de caminhos de decisão
    - Geração de plano prático

    Attributes:
        include_reversed: Se True, inclui sentido invertido na interpretação.
    """

    def __init__(self, include_reversed: bool = True) -> None:
        self.include_reversed = include_reversed
        logger.debug("AnalysisEngine inicializado, reversed=%s", include_reversed)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def analyze(self, input_data: StructuredInput) -> AnalysisResult:
        """Executa análise completo sobre o input estruturado.

        Args:
            input_data: StructuredInput com dados do usuário (keywords ou cartas).

        Returns:
            AnalysisResult com análise completa.
        """
        logger.info(
            "Iniciando análise: format=%r, keywords=%s, cards=%d",
            input_data.format,
            input_data.keywords,
            len(input_data.cards) if input_data.cards else 0,
        )

        # Fase 1: Mapeamento simbólico
        mapped_symbols, symbolic_mappings = self._map_symbols(input_data)

        # Fase 2: Interpretação de cartas (se tiragem)
        card_interpretations = self._interpret_cards(input_data)

        # Fase 3: Diagnóstico central
        diagnosis = self._generate_diagnosis(mapped_symbols, input_data)

        # Fase 4: Detecção de temas
        themes = _detect_themes(mapped_symbols, input_data.raw_content)

        # Fase 5: Identificação de riscos
        risks = _identify_risks(mapped_symbols, input_data.raw_content, themes)

        # Fase 6: Mapeamento de decisões
        decisions = _map_decisions(mapped_symbols, input_data.raw_content, themes)

        # Fase 7: Geração do plano prático
        practical_plan = _generate_practical_plan(mapped_symbols, themes, risks)

        # Fase 8: Detecção de padrões cruzados (apenas para tiragens)
        cross_card_patterns = _detect_cross_card_patterns(input_data.cards or [])

        result = AnalysisResult(
            diagnosis=diagnosis,
            themes=themes,
            risks=risks,
            decisions=decisions,
            practical_plan=practical_plan,
            card_interpretations=card_interpretations,
            symbolic_mappings=symbolic_mappings,
            cross_card_patterns=cross_card_patterns,
        )

        logger.info(
            "Análise concluída: temas=%s, riscos=%d, decisões=%d, padrões=%d",
            themes,
            len(risks),
            len(decisions),
            len(cross_card_patterns),
        )

        return result

    # ------------------------------------------------------------------
    # Fases internas
    # ------------------------------------------------------------------

    def _map_symbols(
        self, input_data: StructuredInput
    ) -> tuple[list[CiganoSymbol], dict[str, str]]:
        """Mapeia keywords e nomes de cartas para símbolos do catálogo.

        Args:
            input_data: Input estruturado.

        Returns:
            Tupla (lista de símbolos mapeados, dicionário de mapeamentos).
        """
        symbols: list[CiganoSymbol] = []
        mappings: dict[str, str] = {}

        # Processar keywords (text ou symbols format)
        if input_data.keywords:
            for kw in input_data.keywords:
                matched = _map_keyword_to_symbol(kw)
                for sym in matched:
                    if sym not in symbols:
                        symbols.append(sym)
                    # Registrar mapeamento
                    key = f"kw:{kw}"
                    if key not in mappings:
                        mappings[key] = sym.name

        # Processar cartas (spread format)
        if input_data.cards:
            for card in input_data.cards:
                sym = get_symbol_by_name(card.card_name)
                if sym is None:
                    # Fallback: busca por keyword
                    matched = match_keyword(card.card_name)
                    if matched:
                        sym = matched[0]

                if sym and sym not in symbols:
                    symbols.append(sym)
                # Registrar mapeamento
                key = f"card:{card.card_name}"
                if key not in mappings:
                    mappings[key] = sym.name if sym else "(não encontrado)"

        logger.debug("Símbolos mapeados: %d", len(symbols))
        return symbols, mappings

    def _interpret_cards(self, input_data: StructuredInput) -> Optional[list[str]]:
        """Gera interpretações para cartas da tiragem (spread format).

        Args:
            input_data: Input estruturado com cartas.

        Returns:
            Lista de interpretações ou None se não houver cartas.
        """
        if not input_data.cards:
            return None

        all_symbols = get_all_symbols()
        interpretations: list[str] = []

        for card in input_data.cards:
            interp = _interpret_card_position(card, all_symbols)
            interpretations.append(interp)

        return interpretations

    def _generate_diagnosis(
        self, symbols: list[CiganoSymbol], input_data: StructuredInput
    ) -> str:
        """Gera o diagnóstico central da situação.

        Args:
            symbols: Lista de símbolos mapeados.
            input_data: Input original para contexto.

        Returns:
            String com diagnóstico central.
        """
        if not symbols:
            return (
                "Não foi possível identificar símbolos a partir do input fornecido. "
                "Tente fornecer keywords mais específicas ou nomes de cartas válidos."
            )

        # Diagnóstico baseado no símbolo mais relevante
        top = symbols[0]
        lines = [
            f"**Simbologia central: {top.name}**",
            "",
            top.interpretation,
        ]

        # Adicionar tema predominante
        if top.theme:
            lines.append("")
            lines.append(f"Área de destaque: *{top.theme}*")

        # Adicionar nuance se houver mais símbolos
        if len(symbols) > 1:
            lines.append("")
            secondary = symbols[1]
            lines.append(
                f"**Nuance secundária**: A presença de *{secondary.name}* adiciona "
                f"a perspectiva de {secondary.theme} — {secondary.interpretation[:100]}..."
            )

        return "\n".join(lines)