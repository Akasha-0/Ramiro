"""Detector de padrões cruzados entre cartas — Sistema de Clareza.

Módulo que analisa relações entre múltiplas cartas em uma tiragem:
- detect_numeric_repeats: detecta cartas com números repetidos (ex: 8 e 32)
- detect_numeric_sequences: detecta sequências numéricas (ex: 1, 2, 3)
- detect_theme_clusters: detecta agrupamentos temáticos (ex: múltiplas cartas de trabalho)
- detect_elemental_imbalance: detecta desequilíbrios elementais
- detect_conflicts: detecta conflitos entre cartas com temas opostos
- detect_all_patterns: função principal que executa todas as detecções

Recebe lista de CardPosition (types.py) e retorna lista de CrossCardPattern (types.py).
"""

import logging
from collections import Counter
from typing import Optional

from clareza.symbols import CiganoSymbol, get_symbol_by_name
from clareza.types import CardPosition, CrossCardPattern

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Mapeamento de elementos para temas (para análise de desequilíbrio)
# ----------------------------------------------------------------------

_ELEMENT_MAP: dict[str, str] = {
    "trabalho": "ar",
    "relação": "água",
    "saúde": "terra",
    "espiritual": "éter",
    "dinheiro": "terra",
    "viagem": "ar",
    "família": "água",
}

_ELEMENT_TRIGGERS: dict[str, list[str]] = {
    "água": ["relação", "família", "espiritual"],
    "terra": ["saúde", "dinheiro", "família"],
    "ar": ["trabalho", "viagem", "espiritual"],
    "éter": ["espiritual", "trabalho"],
}

# ----------------------------------------------------------------------
# Pares de temas conflitantes
# ----------------------------------------------------------------------

_CONFLICT_PAIRS: list[tuple[str, str]] = [
    ("trabalho", "família"),
    ("relação", "trabalho"),
    ("saúde", "trabalho"),
    ("dinheiro", "espiritual"),
    ("viagem", "família"),
]

# ----------------------------------------------------------------------
# Funções de detecção de padrões
# ----------------------------------------------------------------------


def _symbol_from_card(card: CardPosition) -> Optional[CiganoSymbol]:
    """Resolve um CardPosition para seu CiganoSymbol correspondente.

    Args:
        card: CardPosition com nome da carta.

    Returns:
        CiganoSymbol correspondente ou None se não encontrado.
    """
    symbol = get_symbol_by_name(card.card_name)
    if symbol is None:
        logger.debug("Símbolo não encontrado para carta: %r", card.card_name)
    return symbol


def _get_last_digit(num: int) -> int:
    """Retorna o último dígito de um número.

    Args:
        num: Número inteiro.

    Returns:
        Último dígito (0-9).
    """
    return abs(num) % 10


def detect_numeric_repeats(cards: list[CardPosition]) -> list[CrossCardPattern]:
    """Detecta cartas com dígitos numéricos repetidos.

    Explica a relevância: quando múltiplas cartas compartilham o último
    dígito, há uma ressonância energética — a energia desse número ressoa
    em diferentes aspectos da situação.

    Args:
        cards: Lista de cartas na tiragem.

    Returns:
        Lista de CrossCardPattern com padrões numéricos repetidos.
    """
    if not cards:
        return []

    patterns: list[CrossCardPattern] = []

    # Coletar símbolos válidos
    symbols_with_ids: list[tuple[int, CiganoSymbol]] = []
    for card in cards:
        symbol = _symbol_from_card(card)
        if symbol:
            symbols_with_ids.append((symbol.id, symbol))

    if len(symbols_with_ids) < 2:
        return []

    # Agrupar por último dígito
    digit_groups: dict[int, list[CiganoSymbol]] = {}
    for symbol_id, symbol in symbols_with_ids:
        digit = _get_last_digit(symbol_id)
        if digit not in digit_groups:
            digit_groups[digit] = []
        digit_groups[digit].append(symbol)

    # Gerar padrões para dígitos com 2+ cartas
    for digit, group_symbols in digit_groups.items():
        if len(group_symbols) >= 2:
            card_ids = [s.id for s in group_symbols]
            names = [s.name for s in group_symbols]

            interpretation = (
                f"Ressonância numérica no dígito {digit}: as cartas {', '.join(names)} "
                f"compartilham a energia deste número. "
                f"Este padrão indica que o tema do dígito {digit} está presente "
                f"em múltiplas áreas da sua situação. "
                f"Preste atenção especial a questões relacionadas ao número {digit}."
            )

            patterns.append(
                CrossCardPattern(
                    pattern_type="numeric_repeat",
                    card_ids=card_ids,
                    interpretation=interpretation,
                    strength="moderate" if len(group_symbols) == 2 else "strong",
                )
            )

    logger.debug("Padrões numéricos repetidos detectados: %d", len(patterns))
    return patterns


def detect_numeric_sequences(cards: list[CardPosition]) -> list[CrossCardPattern]:
    """Detecta sequências numéricas consecutivas entre cartas.

    Explica a relevância: sequências indicam uma progressão natural —
    a energia das cartas está em movimento, cada carta alimentando
    a próxima. É um sinal de jornada ou processo em andamento.

    Args:
        cards: Lista de cartas na tiragem.

    Returns:
        Lista de CrossCardPattern com sequências numéricas.
    """
    if not cards:
        return []

    patterns: list[CrossCardPattern] = []

    # Coletar IDs válidos
    symbol_ids: list[int] = []
    for card in cards:
        symbol = _symbol_from_card(card)
        if symbol:
            symbol_ids.append(symbol.id)

    if len(symbol_ids) < 2:
        return []

    # Ordenar IDs
    sorted_ids = sorted(set(symbol_ids))

    # Encontrar sequências consecutivas
    sequences: list[list[int]] = []
    current_sequence: list[int] = [sorted_ids[0]]

    for i in range(1, len(sorted_ids)):
        if sorted_ids[i] == sorted_ids[i - 1] + 1:
            current_sequence.append(sorted_ids[i])
        else:
            if len(current_sequence) >= 2:
                sequences.append(current_sequence)
            current_sequence = [sorted_ids[i]]

    # Não esquecer a última sequência
    if len(current_sequence) >= 2:
        sequences.append(current_sequence)

    # Gerar padrões para cada sequência
    for seq in sequences:
        symbols = [get_symbol_by_name(_get_symbol_name_by_id(sid)) for sid in seq]
        names = [s.name for s in symbols if s]
        card_ids = seq

        seq_str = " → ".join(str(sid) for sid in seq)
        names_str = ", ".join(names) if names else "desconhecidas"

        interpretation = (
            f"Sequência numérica {seq_str}: as cartas {names_str} formam uma "
            f"progressão consecutive. "
            f"Este padrão indica que a energia está fluindo naturalmente entre estas cartas. "
            f"É um sinal de jornada em andamento — cada etapa leva naturalmente à próxima. "
            f"Permita que o processo se desenvolva sem forçar interrupções."
        )

        patterns.append(
            CrossCardPattern(
                pattern_type="numeric_sequence",
                card_ids=card_ids,
                interpretation=interpretation,
                strength="strong" if len(seq) >= 3 else "moderate",
            )
        )

    logger.debug("Sequências numéricas detectadas: %d", len(patterns))
    return patterns


def _get_symbol_name_by_id(symbol_id: int) -> str:
    """Retorna o nome do símbolo pelo ID (busca simples)."""
    from clareza.symbols import get_all_symbols

    for s in get_all_symbols():
        if s.id == symbol_id:
            return s.name
    return str(symbol_id)


def detect_theme_clusters(cards: list[CardPosition]) -> list[CrossCardPattern]:
    """Detecta agrupamentos temáticos entre cartas.

    Explica a relevância: quando múltiplas cartas pertencem ao mesmo tema,
    há uma concentração energética nessa área. O tema está intensified —
    seja como oportunidade ou como área que requer atenção.

    Args:
        cards: Lista de cartas na tiragem.

    Returns:
        Lista de CrossCardPattern com agrupamentos temáticos.
    """
    if not cards:
        return []

    patterns: list[CrossCardPattern] = []

    # Coletar símbolos
    symbols: list[CiganoSymbol] = []
    for card in cards:
        symbol = _symbol_from_card(card)
        if symbol:
            symbols.append(symbol)

    if len(symbols) < 2:
        return []

    # Agrupar por tema
    theme_groups: dict[str, list[CiganoSymbol]] = {}
    for symbol in symbols:
        if symbol.theme not in theme_groups:
            theme_groups[symbol.theme] = []
        theme_groups[symbol.theme].append(symbol)

    # Gerar padrões para temas com 2+ cartas
    for theme, group_symbols in theme_groups.items():
        if len(group_symbols) >= 2:
            card_ids = [s.id for s in group_symbols]
            names = [s.name for s in group_symbols]

            interpretation = (
                f"Agrupamento temático em **{theme}**: as cartas {', '.join(names)} "
                f"compartilham este tema. "
                f"Este padrão indica uma concentração de energia no tema {theme}. "
                f"A situação atual está fortemente influenciada por questões de {theme}. "
                f"É recomendável dar atenção especial a esta área da sua vida."
            )

            patterns.append(
                CrossCardPattern(
                    pattern_type="theme_cluster",
                    card_ids=card_ids,
                    interpretation=interpretation,
                    strength="moderate" if len(group_symbols) == 2 else "strong",
                )
            )

    logger.debug("Agrupamentos temáticos detectados: %d", len(patterns))
    return patterns


def detect_elemental_imbalance(cards: list[CardPosition]) -> Optional[CrossCardPattern]:
    """Detecta desequilíbrios elementais na tiragem.

    Explica a relevância: o Baralho Cigano reflete equilíbrio elemental.
    Cada tema corresponde a um elemento (água, terra, ar, éter). Muitos
    cartões de um elemento sem outros indica uma energia unilateral —
    há falta de contrapeso. Isso pode significar que a situação está
    sendo vivida de forma muito intensa ou muito restrita.

    Args:
        cards: Lista de cartas na tiragem.

    Returns:
        CrossCardPattern com análise de desequilíbrio ou None se balanceado.
    """
    if not cards:
        return None

    # Coletar elementos
    elements: list[str] = []
    for card in cards:
        symbol = _symbol_from_card(card)
        if symbol:
            element = _ELEMENT_MAP.get(symbol.theme, "éter")
            elements.append(element)

    if not elements:
        return None

    # Contar frequência
    element_counts = Counter(elements)
    total = len(elements)

    # Calcular desequilíbrio
    # Se um elemento tem mais de 50% ou há ausência completa de algum elemento
    dominant_threshold = 0.5
    is_dominant = any(count / total > dominant_threshold for count in element_counts.values())

    # Verificar ausência (elemento com 0 quando outros têm 3+)
    has_absence = False
    all_elements = {"água", "terra", "ar", "éter"}
    present_elements = set(elements)
    missing_elements = all_elements - present_elements

    if len(present_elements) >= 3:
        for missing in missing_elements:
            if element_counts[missing] == 0:
                has_absence = True
                break

    if not is_dominant and not has_absence:
        logger.debug("Tiragem elementalmente balanceada")
        return None

    # Gerar interpretação do desequilíbrio
    dominant_element = max(element_counts, key=element_counts.get)
    dominant_count = element_counts[dominant_element]
    dominant_pct = (dominant_count / total) * 100

    card_ids = []
    for card in cards:
        symbol = _symbol_from_card(card)
        if symbol:
            card_ids.append(symbol.id)

    if is_dominant:
        interpretation = (
            f"Desequilíbrio elemental: {dominant_pct:.0f}% das cartas são de "
            f"elemento **{dominant_element}** ({', '.join(_ELEMENT_TRIGGERS[dominant_element])}). "
            f"Este padrão indica que a energia está muito concentrada neste elemento. "
            f"Uma energia tão intensa de {dominant_element} pode significar que a situação "
            f"está sendo vivida de forma muito intensa ou que falta contrapeso. "
            f"Considere buscar equilíbrio incorporando energias de outros elementos."
        )
    else:
        missing_list = ", ".join(missing_elements)
        interpretation = (
            f"Desequilíbrio elemental: elementos {missing_list} estão ausentes. "
            f"O dominante é **{dominant_element}** ({dominant_pct:.0f}%). "
            f"Este padrão indica que a energia está unilateral. "
            f"Falta a perspectiva dos elementos ausentes. "
            f"Para restaurar equilíbrio, considere buscar experiências que tragam "
            f"as energias que estão faltando na sua vida."
        )

    logger.debug("Desequilíbrio elemental detectado: %s", dominant_element)

    return CrossCardPattern(
        pattern_type="elemental_imbalance",
        card_ids=card_ids,
        interpretation=interpretation,
        strength="strong" if is_dominant else "moderate",
    )


def detect_conflicts(cards: list[CardPosition]) -> list[CrossCardPattern]:
    """Detecta conflitos entre cartas com temas opostos.

    Explica a relevância: quando cartas de temas conflitantes aparecem juntas,
    há uma tensão interna na situação. Isso não é necessariamente ruim —
    pode indicar uma escolha pendente ou uma área onde há conflito de prioridades.

    Args:
        cards: Lista de cartas na tiragem.

    Returns:
        Lista de CrossCardPattern com conflitos detectados.
    """
    if not cards:
        return []

    patterns: list[CrossCardPattern] = []

    # Coletar símbolos e seus temas
    symbols: list[CiganoSymbol] = []
    for card in cards:
        symbol = _symbol_from_card(card)
        if symbol:
            symbols.append(symbol)

    if len(symbols) < 2:
        return []

    # Coletar temas únicos presentes
    present_themes = set(s.theme for s in symbols)

    # Verificar cada par de temas conflitantes
    conflict_pairs_found: list[tuple[str, str, list[CiganoSymbol], list[CiganoSymbol]]] = []

    for theme_a, theme_b in _CONFLICT_PAIRS:
        if theme_a in present_themes and theme_b in present_themes:
            symbols_a = [s for s in symbols if s.theme == theme_a]
            symbols_b = [s for s in symbols if s.theme == theme_b]

            if symbols_a and symbols_b:
                conflict_pairs_found.append((theme_a, theme_b, symbols_a, symbols_b))

    # Gerar padrões para cada conflito
    for theme_a, theme_b, group_a, group_b in conflict_pairs_found:
        all_conflicting = group_a + group_b
        card_ids = [s.id for s in all_conflicting]
        names_a = [s.name for s in group_a]
        names_b = [s.name for s in group_b]

        interpretation = (
            f"Tensão entre **{theme_a}** e **{theme_b}**: "
            f"cartas {', '.join(names_a)} ({theme_a}) vs "
            f"{', '.join(names_b)} ({theme_b}). "
            f"Este padrão indica um conflito de prioridades ou uma escolha pendente. "
            f"A situação atual envolve tensões entre estas duas áreas da vida. "
            f"É necessário encontrar equilíbrio ou fazer uma escolha consciente "
            f"sobre qual área priorizar neste momento."
        )

        patterns.append(
            CrossCardPattern(
                pattern_type="conflict",
                card_ids=card_ids,
                interpretation=interpretation,
                strength="moderate",
            )
        )

    logger.debug("Conflitos detectados: %d", len(patterns))
    return patterns


# ----------------------------------------------------------------------
# Função principal
# ----------------------------------------------------------------------


def detect_all_patterns(cards: list[CardPosition]) -> list[CrossCardPattern]:
    """Detecta todos os padrões cruzados entre cartas na tiragem.

    Executa todas as detecções de padrão e retorna uma lista combinada
    ordenada por tipo de padrão.

    Args:
        cards: Lista de cartas na tiragem.

    Returns:
        Lista de CrossCardPattern com todos os padrões detectados.
        Retorna lista vazia se não houver padrões ou cartas insuficientes.
    """
    logger.info("Iniciando detecção de padrões para %d cartas", len(cards))

    if not cards or len(cards) < 2:
        logger.debug("Cartas insuficientes para análise de padrões")
        return []

    all_patterns: list[CrossCardPattern] = []

    # Executar todas as detecções
    all_patterns.extend(detect_numeric_repeats(cards))
    all_patterns.extend(detect_numeric_sequences(cards))
    all_patterns.extend(detect_theme_clusters(cards))

    elemental = detect_elemental_imbalance(cards)
    if elemental:
        all_patterns.append(elemental)

    all_patterns.extend(detect_conflicts(cards))

    logger.info(
        "Padrões detectados: total=%d (repetidos=%d, sequências=%d, "
        "temas=%d, elementar=%s, conflitos=%d)",
        len(all_patterns),
        len(detect_numeric_repeats(cards)),
        len(detect_numeric_sequences(cards)),
        len(detect_theme_clusters(cards)),
        "sim" if elemental else "não",
        len(detect_conflicts(cards)),
    )

    return all_patterns
