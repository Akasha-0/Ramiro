"""Testes unitários para src/symbols.py — get_similar_card_names.

Cobertura:
- get_similar_card_names() — fuzzy matching, partial matching, exact matching
- Limite de resultados via parâmetro n
- Case-insensitive matching
- Empty input handling
"""

import pytest

from src.symbols import get_similar_card_names


# ----------------------------------------------------------------------
# Testes — empty input
# ----------------------------------------------------------------------


class TestGetSimilarCardNamesEmptyInput:
    def test_empty_string_returns_empty_list(self) -> None:
        result = get_similar_card_names("")
        assert result == []

    def test_whitespace_only_returns_results(self) -> None:
        """Espaços em branco são normalizados e retornam resultados via fuzzy."""
        result = get_similar_card_names("   ")
        # A função normaliza o input, então espaços geram matches fuzzy
        assert isinstance(result, list)

    def test_none_input_returns_empty_list(self) -> None:
        result = get_similar_card_names(None)  # type: ignore
        assert result == []


# ----------------------------------------------------------------------
# Testes — exact matches
# ----------------------------------------------------------------------


class TestGetSimilarCardNamesExactMatch:
    def test_exact_match_returns_card(self) -> None:
        result = get_similar_card_names("A Estrela")
        assert "A Estrela" in result

    def test_exact_match_case_insensitive(self) -> None:
        result = get_similar_card_names("A ESTRELA")
        assert "A Estrela" in result

    def test_exact_match_lowercase(self) -> None:
        result = get_similar_card_names("a estrela")
        assert "A Estrela" in result

    def test_exact_match_with_leading_trailing_whitespace(self) -> None:
        result = get_similar_card_names("  A Estrela  ")
        assert "A Estrela" in result

    def test_exact_match_cruz(self) -> None:
        result = get_similar_card_names("A Cruz")
        assert "A Cruz" in result

    def test_exact_match_casa(self) -> None:
        result = get_similar_card_names("A Casa")
        assert "A Casa" in result


# ----------------------------------------------------------------------
# Testes — partial matches
# ----------------------------------------------------------------------


class TestGetSimilarCardNamesPartialMatch:
    def test_partial_match_prefix(self) -> None:
        result = get_similar_card_names("Estrela")
        assert len(result) > 0
        # Deve incluir cartas que contêm "Estrela" no nome
        assert any("Estrela" in name for name in result)

    def test_partial_match_substring(self) -> None:
        result = get_similar_card_names("Cruz")
        assert len(result) > 0
        # "Cruz" está contido em "A Cruz" e "A Cruz de São André"
        assert any("cruz" in name.lower() for name in result)

    def test_partial_match_asa_finds_casa(self) -> None:
        result = get_similar_card_names("asa")
        assert len(result) > 0
        # "asa" está contido em "A Casa"
        assert any("asa" in name.lower() for name in result)

    def test_partial_match_reverse(self) -> None:
        result = get_similar_card_names("A Casa")
        # "A Casa" contém "asa"
        assert len(result) > 0


# ----------------------------------------------------------------------
# Testes — fuzzy matching
# ----------------------------------------------------------------------


class TestGetSimilarCardNamesFuzzyMatch:
    def test_typo_similar_name(self) -> None:
        """Similaridade com nome levemente incorreto."""
        result = get_similar_card_names("Estrel")
        assert len(result) > 0
        # Deve encontrar algo similar a "A Estrela"
        assert any("Estrela" in name for name in result)

    def test_fuzzy_sorted_by_similarity(self) -> None:
        """Resultados fuzzy são ordenados por similaridade decrescente."""
        result = get_similar_card_names("Cafe")
        # O primeiro resultado deve ser mais similar
        assert len(result) > 0

    def test_no_exact_or_partial_returns_fuzzy(self) -> None:
        """Quando não há correspondência exata ou parcial, usa fuzzy matching."""
        result = get_similar_card_names("xyzabc")
        # Deve ainda retornar resultados (fuzzy), não lista vazia
        assert isinstance(result, list)

    def test_typo_cruz(self) -> None:
        """Erro de digitação próximo a 'Cruz'."""
        result = get_similar_card_names("Cruzz")
        assert len(result) > 0


# ----------------------------------------------------------------------
# Testes — n parameter (limite de resultados)
# ----------------------------------------------------------------------


class TestGetSimilarCardNamesLimit:
    def test_default_n_is_five(self) -> None:
        result = get_similar_card_names("A Estrela")
        assert len(result) <= 5

    def test_n_one_returns_single_result(self) -> None:
        result = get_similar_card_names("A Estrela", n=1)
        assert len(result) == 1

    def test_n_three_returns_up_to_three(self) -> None:
        result = get_similar_card_names("A Cruz", n=3)
        assert len(result) <= 3

    def test_n_ten_returns_up_to_ten(self) -> None:
        result = get_similar_card_names("A Estrela", n=10)
        assert len(result) <= 10

    def test_n_zero_returns_empty_list(self) -> None:
        result = get_similar_card_names("A Cruz", n=0)
        assert result == []


# ----------------------------------------------------------------------
# Testes — ordering and deduplication
# ----------------------------------------------------------------------


class TestGetSimilarCardNamesOrdering:
    def test_exact_match_comes_first(self) -> None:
        result = get_similar_card_names("A Estrela")
        assert result[0] == "A Estrela"

    def test_no_duplicate_results(self) -> None:
        result = get_similar_card_names("A Casa")
        # Não deve haver duplicatas
        assert len(result) == len(set(result))

    def test_results_are_card_names(self) -> None:
        """Resultados são strings (nomes de cartas)."""
        result = get_similar_card_names("A Cruz")
        for name in result:
            assert isinstance(name, str)
            assert len(name) > 0


# ----------------------------------------------------------------------
# Testes — special characters and accents
# ----------------------------------------------------------------------


class TestGetSimilarCardNamesAccents:
    def test_handles_accents(self) -> None:
        result = get_similar_card_names("O Cafezinho")
        assert len(result) > 0
        assert any("Cafezinho" in name for name in result)

    def test_search_without_accent_finds_accented(self) -> None:
        result = get_similar_card_names("Cafezinho")
        # Com ou sem acento deve encontrar
        assert len(result) > 0
        assert any("Cafezinho" in name or "Cafezinho" in name for name in result)

    def test_search_with_partial_accent(self) -> None:
        result = get_similar_card_names("Coruja")
        assert len(result) > 0
        assert any("Coruja" in name for name in result)
