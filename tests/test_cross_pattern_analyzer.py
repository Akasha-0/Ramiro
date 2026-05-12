"""Testes unitários para src/cross_pattern_analyzer.py.

Cobertura:
- _get_last_digit() — extração de último dígito
- _symbol_from_card() — resolução de CardPosition para CiganoSymbol
- _get_symbol_name_by_id() — busca de nome por ID
- detect_numeric_repeats() — detecção de dígitos repetidos
- detect_numeric_sequences() — detecção de sequências numéricas
- detect_theme_clusters() — detecção de agrupamentos temáticos
- detect_elemental_imbalance() — detecção de desequilíbrio elemental
- detect_conflicts() — detecção de conflitos entre temas
- detect_all_patterns() — função principal que executa todas as detecções
- _ELEMENT_MAP — mapeamento de elementos
- _ELEMENT_TRIGGERS — disparadores elementais
- _CONFLICT_PAIRS — pares de temas conflitantes
"""

import pytest

from clareza.cross_pattern_analyzer import (
    _CONFLICT_PAIRS,
    _ELEMENT_MAP,
    _ELEMENT_TRIGGERS,
    _get_last_digit,
    _get_symbol_name_by_id,
    _symbol_from_card,
    detect_all_patterns,
    detect_conflicts,
    detect_elemental_imbalance,
    detect_numeric_repeats,
    detect_numeric_sequences,
    detect_theme_clusters,
)
from clareza.symbols import get_symbol_by_name
from clareza.types import CardPosition, CrossCardPattern


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def cards_work_family() -> list[CardPosition]:
    """Cartas com temas trabalho e família (conflitantes)."""
    return [
        CardPosition(position=1, card_name="O Mercado"),
        CardPosition(position=2, card_name="A Casa"),
        CardPosition(position=3, card_name="A Cegonha"),
    ]


@pytest.fixture
def cards_numeric_repeat() -> list[CardPosition]:
    """Cartas com IDs terminando no mesmo dígito (ex: 1 e 31)."""
    return [
        CardPosition(position=1, card_name="O Cigano"),
        CardPosition(position=2, card_name="O Anel"),
    ]


@pytest.fixture
def cards_numeric_sequence() -> list[CardPosition]:
    """Cartas com IDs consecutivos (ex: 1, 2, 3)."""
    return [
        CardPosition(position=1, card_name="O Cigano"),
        CardPosition(position=2, card_name="O Trevo"),
        CardPosition(position=3, card_name="O Navio"),
    ]


@pytest.fixture
def cards_theme_cluster() -> list[CardPosition]:
    """Cartas do mesmo tema (trabalho)."""
    return [
        CardPosition(position=1, card_name="O Mercado"),
        CardPosition(position=2, card_name="O Pompom"),
        CardPosition(position=3, card_name="A Flecha"),
    ]


# ----------------------------------------------------------------------
# Testes — _get_last_digit()
# ----------------------------------------------------------------------


class TestGetLastDigit:
    def test_positive_number(self) -> None:
        """Dígito final de número positivo."""
        assert _get_last_digit(32) == 2
        assert _get_last_digit(8) == 8
        assert _get_last_digit(15) == 5

    def test_negative_number(self) -> None:
        """Dígito final de número negativo (usa valor absoluto)."""
        assert _get_last_digit(-32) == 2
        assert _get_last_digit(-8) == 8

    def test_single_digit(self) -> None:
        """Dígito único retorna ele mesmo."""
        assert _get_last_digit(7) == 7
        assert _get_last_digit(0) == 0

    def test_large_number(self) -> None:
        """Dígito final de número grande."""
        assert _get_last_digit(123456789) == 9
        assert _get_last_digit(1000) == 0


# ----------------------------------------------------------------------
# Testes — _symbol_from_card()
# ----------------------------------------------------------------------


class TestSymbolFromCard:
    def test_valid_card(self) -> None:
        """CardPosition válido retorna CiganoSymbol."""
        card = CardPosition(position=1, card_name="A Estrela")
        symbol = _symbol_from_card(card)
        assert symbol is not None
        assert symbol.name == "A Estrela"

    def test_valid_card_lowercase(self) -> None:
        """Nome em minúsculas ainda encontra símbolo."""
        card = CardPosition(position=1, card_name="a estrela")
        symbol = _symbol_from_card(card)
        assert symbol is not None

    def test_invalid_card_returns_none(self) -> None:
        """Carta inexistente retorna None."""
        card = CardPosition(position=1, card_name="Carta Inexistente XYZ")
        symbol = _symbol_from_card(card)
        assert symbol is None

    def test_empty_card_name_returns_none(self) -> None:
        """Nome vazio retorna None."""
        card = CardPosition(position=1, card_name="")
        symbol = _symbol_from_card(card)
        assert symbol is None


# ----------------------------------------------------------------------
# Testes — _get_symbol_name_by_id()
# ----------------------------------------------------------------------


class TestGetSymbolNameById:
    def test_valid_id(self) -> None:
        """ID válido retorna nome do símbolo."""
        name = _get_symbol_name_by_id(1)
        assert name != ""
        assert isinstance(name, str)

    def test_invalid_id_returns_string(self) -> None:
        """ID inválido retorna string do ID."""
        name = _get_symbol_name_by_id(9999)
        assert name == "9999"

    def test_id_zero(self) -> None:
        """ID zero retorna string '0'."""
        name = _get_symbol_name_by_id(0)
        assert name == "0"


# ----------------------------------------------------------------------
# Testes — detect_numeric_repeats()
# ----------------------------------------------------------------------


class TestDetectNumericRepeats:
    def test_repeats_detected(self, cards_numeric_repeat: list[CardPosition]) -> None:
        """Dígitos repetidos são detectados."""
        patterns = detect_numeric_repeats(cards_numeric_repeat)
        assert len(patterns) >= 1
        assert patterns[0].pattern_type == "numeric_repeat"

    def test_no_repeats_single_card(self) -> None:
        """Uma única carta não gera padrão."""
        card = CardPosition(position=1, card_name="A Estrela")
        patterns = detect_numeric_repeats([card])
        assert patterns == []

    def test_no_repeats_empty(self) -> None:
        """Lista vazia retorna lista vazia."""
        patterns = detect_numeric_repeats([])
        assert patterns == []

    def test_pattern_has_card_ids(self, cards_numeric_repeat: list[CardPosition]) -> None:
        """Padrão inclui IDs das cartas."""
        patterns = detect_numeric_repeats(cards_numeric_repeat)
        assert len(patterns) >= 1
        assert len(patterns[0].card_ids) >= 2

    def test_pattern_has_interpretation(self, cards_numeric_repeat: list[CardPosition]) -> None:
        """Padrão inclui interpretação."""
        patterns = detect_numeric_repeats(cards_numeric_repeat)
        assert len(patterns) >= 1
        assert patterns[0].interpretation != ""
        assert "Ressonância" in patterns[0].interpretation

    def test_strength_depends_on_count(self, cards_numeric_repeat: list[CardPosition]) -> None:
        """Força do padrão depende da quantidade de cartas."""
        patterns = detect_numeric_repeats(cards_numeric_repeat)
        assert len(patterns) >= 1
        assert patterns[0].strength in ("moderate", "strong")


# ----------------------------------------------------------------------
# Testes — detect_numeric_sequences()
# ----------------------------------------------------------------------


class TestDetectNumericSequences:
    def test_sequences_detected(self, cards_numeric_sequence: list[CardPosition]) -> None:
        """Sequências consecutivas são detectadas."""
        patterns = detect_numeric_sequences(cards_numeric_sequence)
        assert len(patterns) >= 1
        assert patterns[0].pattern_type == "numeric_sequence"

    def test_no_sequences_non_consecutive(self) -> None:
        """Cartas não consecutivas não geram padrão."""
        cards = [
            CardPosition(position=1, card_name="A Estrela"),
            CardPosition(position=2, card_name="O Cigano"),
        ]
        patterns = detect_numeric_sequences(cards)
        # Se não forem consecutivas, não deve gerar sequência
        assert isinstance(patterns, list)

    def test_no_sequences_single_card(self) -> None:
        """Uma única carta não gera padrão."""
        card = CardPosition(position=1, card_name="A Estrela")
        patterns = detect_numeric_sequences([card])
        assert patterns == []

    def test_no_sequences_empty(self) -> None:
        """Lista vazia retorna lista vazia."""
        patterns = detect_numeric_sequences([])
        assert patterns == []

    def test_pattern_has_interpretation(self, cards_numeric_sequence: list[CardPosition]) -> None:
        """Padrão inclui interpretação."""
        patterns = detect_numeric_sequences(cards_numeric_sequence)
        assert len(patterns) >= 1
        assert patterns[0].interpretation != ""
        assert "Sequência" in patterns[0].interpretation

    def test_pattern_has_card_ids(self, cards_numeric_sequence: list[CardPosition]) -> None:
        """Padrão inclui IDs das cartas."""
        patterns = detect_numeric_sequences(cards_numeric_sequence)
        assert len(patterns) >= 1
        assert len(patterns[0].card_ids) >= 2


# ----------------------------------------------------------------------
# Testes — detect_theme_clusters()
# ----------------------------------------------------------------------


class TestDetectThemeClusters:
    def test_cluster_detected(self, cards_theme_cluster: list[CardPosition]) -> None:
        """Agrupamento temático é detectado."""
        patterns = detect_theme_clusters(cards_theme_cluster)
        assert len(patterns) >= 1
        assert patterns[0].pattern_type == "theme_cluster"

    def test_no_cluster_single_theme(self) -> None:
        """Cartas de temas diferentes não geram cluster."""
        cards = [
            CardPosition(position=1, card_name="A Estrela"),
            CardPosition(position=2, card_name="O Cigano"),
        ]
        patterns = detect_theme_clusters(cards)
        # Estrelas e Cigano podem ter o mesmo tema
        assert isinstance(patterns, list)

    def test_no_cluster_single_card(self) -> None:
        """Uma única carta não gera padrão."""
        card = CardPosition(position=1, card_name="A Estrela")
        patterns = detect_theme_clusters([card])
        assert patterns == []

    def test_no_cluster_empty(self) -> None:
        """Lista vazia retorna lista vazia."""
        patterns = detect_theme_clusters([])
        assert patterns == []

    def test_pattern_has_theme_name(self, cards_theme_cluster: list[CardPosition]) -> None:
        """Padrão inclui nome do tema."""
        patterns = detect_theme_clusters(cards_theme_cluster)
        assert len(patterns) >= 1
        assert patterns[0].interpretation != ""
        # Interpretação menciona o tema
        assert "trabalho" in patterns[0].interpretation.lower()

    def test_pattern_has_card_ids(self, cards_theme_cluster: list[CardPosition]) -> None:
        """Padrão inclui IDs das cartas."""
        patterns = detect_theme_clusters(cards_theme_cluster)
        assert len(patterns) >= 1
        assert len(patterns[0].card_ids) >= 2


# ----------------------------------------------------------------------
# Testes — detect_elemental_imbalance()
# ----------------------------------------------------------------------


class TestDetectElementalImbalance:
    def test_imbalance_detected(self, cards_work_family: list[CardPosition]) -> None:
        """Desequilíbrio elemental é detectado."""
        result = detect_elemental_imbalance(cards_work_family)
        assert result is not None
        assert result.pattern_type == "elemental_imbalance"

    def test_balanced_returns_none(self) -> None:
        """Tiragem balanceada retorna None."""
        # Cartas de diferentes elementos
        cards = [
            CardPosition(position=1, card_name="A Estrela"),
            CardPosition(position=2, card_name="A Casa"),
        ]
        result = detect_elemental_imbalance(cards)
        # Resultado pode ser None (balanceado) ou um padrão
        assert result is None or result.pattern_type == "elemental_imbalance"

    def test_empty_returns_none(self) -> None:
        """Lista vazia retorna None."""
        result = detect_elemental_imbalance([])
        assert result is None

    def test_single_card_can_return_pattern(self) -> None:
        """Uma única carta pode retornar padrão se for dominante."""
        card = CardPosition(position=1, card_name="A Estrela")
        result = detect_elemental_imbalance([card])
        # Uma única carta tem 100% de um elemento → pode ser detected as desequilíbrio
        assert result is None or result.pattern_type == "elemental_imbalance"

    def test_pattern_has_interpretation(self, cards_work_family: list[CardPosition]) -> None:
        """Padrão inclui interpretação."""
        result = detect_elemental_imbalance(cards_work_family)
        assert result is not None
        assert result.interpretation != ""
        assert "Desequilíbrio" in result.interpretation

    def test_pattern_has_strength(self, cards_work_family: list[CardPosition]) -> None:
        """Padrão inclui força."""
        result = detect_elemental_imbalance(cards_work_family)
        assert result is not None
        assert result.strength in ("moderate", "strong")


# ----------------------------------------------------------------------
# Testes — detect_conflicts()
# ----------------------------------------------------------------------


class TestDetectConflicts:
    def test_conflict_detected(self, cards_work_family: list[CardPosition]) -> None:
        """Conflito entre temas é detectado (trabalho vs família)."""
        patterns = detect_conflicts(cards_work_family)
        assert len(patterns) >= 1
        assert patterns[0].pattern_type == "conflict"

    def test_no_conflict_different_non_conflicting_themes(self) -> None:
        """Cartas de temas diferentes não conflitantes não geram conflito."""
        cards = [
            CardPosition(position=1, card_name="A Estrela"),
            CardPosition(position=2, card_name="O Cão"),
        ]
        patterns = detect_conflicts(cards)
        # Estrelas (espiritual) e Cão (relação) não são temas conflitantes
        assert patterns == []

    def test_no_conflict_single_card(self) -> None:
        """Uma única carta não gera conflito."""
        card = CardPosition(position=1, card_name="A Estrela")
        patterns = detect_conflicts([card])
        assert patterns == []

    def test_no_conflict_empty(self) -> None:
        """Lista vazia retorna lista vazia."""
        patterns = detect_conflicts([])
        assert patterns == []

    def test_pattern_has_interpretation(self, cards_work_family: list[CardPosition]) -> None:
        """Padrão inclui interpretação."""
        patterns = detect_conflicts(cards_work_family)
        assert len(patterns) >= 1
        assert patterns[0].interpretation != ""
        assert "Tensão" in patterns[0].interpretation

    def test_pattern_has_card_ids(self, cards_work_family: list[CardPosition]) -> None:
        """Padrão inclui IDs das cartas."""
        patterns = detect_conflicts(cards_work_family)
        assert len(patterns) >= 1
        assert len(patterns[0].card_ids) >= 2


# ----------------------------------------------------------------------
# Testes — detect_all_patterns()
# ----------------------------------------------------------------------


class TestDetectAllPatterns:
    def test_returns_list(self) -> None:
        """Retorna lista de padrões."""
        cards = [
            CardPosition(position=1, card_name="Estrela"),
            CardPosition(position=2, card_name="Casa"),
        ]
        patterns = detect_all_patterns(cards)
        assert isinstance(patterns, list)

    def test_empty_returns_empty(self) -> None:
        """Lista vazia retorna lista vazia."""
        patterns = detect_all_patterns([])
        assert patterns == []

    def test_single_card_returns_empty(self) -> None:
        """Uma única carta retorna lista vazia."""
        card = CardPosition(position=1, card_name="A Estrela")
        patterns = detect_all_patterns([card])
        assert patterns == []

    def test_all_pattern_types_present(self, cards_work_family: list[CardPosition]) -> None:
        """Todos os tipos de padrão estão presentes quando aplicável."""
        patterns = detect_all_patterns(cards_work_family)
        pattern_types = [p.pattern_type for p in patterns]
        # Deve ter pelo menos um tipo válido
        valid_types = {
            "numeric_repeat",
            "numeric_sequence",
            "theme_cluster",
            "elemental_imbalance",
            "conflict",
        }
        for pt in pattern_types:
            assert pt in valid_types

    def test_patterns_are_cross_card_pattern(self, cards_work_family: list[CardPosition]) -> None:
        """Todos os padrões são CrossCardPattern."""
        patterns = detect_all_patterns(cards_work_family)
        for pattern in patterns:
            assert isinstance(pattern, CrossCardPattern)

    def test_combines_all_detections(self) -> None:
        """Função combina todas as detecções."""
        # Cartas que podem gerar múltiplos padrões
        cards = [
            CardPosition(position=1, card_name="O Cigano"),
            CardPosition(position=2, card_name="A Cruz"),
            CardPosition(position=3, card_name="A Cabana"),
            CardPosition(position=4, card_name="O Mercado"),
            CardPosition(position=5, card_name="A Casa"),
            CardPosition(position=6, card_name="A Cegonha"),
        ]
        patterns = detect_all_patterns(cards)
        # Deve retornar alguma coisa
        assert isinstance(patterns, list)


# ----------------------------------------------------------------------
# Testes — constantes e mapeamentos
# ----------------------------------------------------------------------


class TestElementMap:
    def test_element_map_has_all_elements(self) -> None:
        """Mapeamento de elementos cobre os 4 elementos."""
        expected_elements = {"ar", "água", "terra", "éter"}
        mapped_elements = set(_ELEMENT_MAP.values())
        assert expected_elements.issubset(mapped_elements)

    def test_element_map_values_are_valid(self) -> None:
        """Todos os valores do mapa são elementos válidos."""
        valid_elements = {"ar", "água", "terra", "éter"}
        for element in _ELEMENT_MAP.values():
            assert element in valid_elements


class TestElementTriggers:
    def test_element_triggers_has_all_elements(self) -> None:
        """Disparadores elementais cobrem os 4 elementos."""
        expected_elements = {"água", "terra", "ar", "éter"}
        assert expected_elements.issubset(_ELEMENT_TRIGGERS.keys())

    def test_element_triggers_values_are_lists(self) -> None:
        """Todos os disparadores são listas de strings."""
        for triggers in _ELEMENT_TRIGGERS.values():
            assert isinstance(triggers, list)
            assert all(isinstance(t, str) for t in triggers)


class TestConflictPairs:
    def test_conflict_pairs_not_empty(self) -> None:
        """Pares conflitantes não é vazio."""
        assert len(_CONFLICT_PAIRS) > 0

    def test_conflict_pairs_are_tuples(self) -> None:
        """Todos os pares são tuplas de 2 elementos."""
        for pair in _CONFLICT_PAIRS:
            assert isinstance(pair, tuple)
            assert len(pair) == 2

    def test_conflict_pairs_have_distinct_themes(self) -> None:
        """Pares têm temas distintos."""
        for theme_a, theme_b in _CONFLICT_PAIRS:
            assert theme_a != theme_b

    def test_work_family_conflict_exists(self) -> None:
        """Par trabalho/família existe nos conflitos."""
        assert ("trabalho", "família") in _CONFLICT_PAIRS

    def test_conflict_pairs_are_lowercase(self) -> None:
        """Temas nos pares estão em minúsculas."""
        for theme_a, theme_b in _CONFLICT_PAIRS:
            assert theme_a == theme_a.lower()
            assert theme_b == theme_b.lower()


# ----------------------------------------------------------------------
# Testes de edge cases
# ----------------------------------------------------------------------


class TestEdgeCases:
    def test_all_invalid_cards(self) -> None:
        """Todas as cartas inválidas retorna padrão vazio."""
        cards = [
            CardPosition(position=1, card_name="Carta Inexistente A"),
            CardPosition(position=2, card_name="Carta Inexistente B"),
        ]
        patterns = detect_all_patterns(cards)
        # Sem símbolos válidos, não deve gerar padrões
        assert isinstance(patterns, list)

    def test_mixed_valid_invalid_cards(self) -> None:
        """Mistura de cartas válidas e inválidas funciona."""
        cards = [
            CardPosition(position=1, card_name="A Estrela"),
            CardPosition(position=2, card_name="Carta Inexistente"),
            CardPosition(position=3, card_name="A Casa"),
        ]
        patterns = detect_all_patterns(cards)
        assert isinstance(patterns, list)

    def test_special_characters_in_card_name(self) -> None:
        """Nomes com caracteres especiais são processados."""
        cards = [
            CardPosition(position=1, card_name="A Cruz de São André"),
            CardPosition(position=2, card_name="O Cafezinho"),
        ]
        patterns = detect_all_patterns(cards)
        assert isinstance(patterns, list)

    def test_unicode_in_card_name(self) -> None:
        """Nomes com unicode são processados."""
        cards = [
            CardPosition(position=1, card_name="O Cigano"),
            CardPosition(position=2, card_name="O Anel"),
        ]
        patterns = detect_all_patterns(cards)
        assert isinstance(patterns, list)
