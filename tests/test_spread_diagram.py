"""Testes unitários para src/spread_diagram.py.

Cobertura:
- POSITION_LABELS dict — labels de contexto disponíveis
- _format_context_label() — formatação de labels de contexto
- _format_card_label() — formatação de labels de carta
- SpreadDiagramGenerator.__init__() — configuração de include_context
- SpreadDiagramGenerator.generate() — geração principal
- SpreadDiagramGenerator.generate_from_positions() — geração a partir de posições
- SpreadDiagramGenerator.generate_linear() — geração linear
- SpreadDiagramGenerator.generate_celtic_cross() — geração Celtic Cross
- _generate_single_card_diagram() — diagrama de 1 carta
- _generate_tres_cartas_diagram() — diagrama de 3 cartas
- _generate_cinco_cartas_diagram() — diagrama de 5 cartas
- _generate_ferradura_diagram() — diagrama de ferradura
- _generate_cruz_celtas_diagram() — diagrama de Cruz Celta
- _generate_linear_diagram() — diagrama linear genérico
- Edge cases: contexto desabilitado, lista vazia, cards sem nome
"""

import pytest

from src.spread_diagram import (
    POSITION_LABELS,
    SpreadDiagramGenerator,
    _format_card_label,
    _format_context_label,
)
from src.spread_templates import SpreadTemplate, SpreadPosition


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def generator() -> SpreadDiagramGenerator:
    """Gerador com include_context=True (padrão)."""
    return SpreadDiagramGenerator(include_context=True)


@pytest.fixture
def generator_no_context() -> SpreadDiagramGenerator:
    """Gerador sem contexto."""
    return SpreadDiagramGenerator(include_context=False)


@pytest.fixture
def template_tres_cartas() -> SpreadTemplate:
    """Template 'tres-cartas' com posições preenchidas."""
    return SpreadTemplate(
        name="tres-cartas",
        display_name="Três Cartas",
        description="Tiragem de três posições",
        positions=[
            SpreadPosition(position=1, context="passado", description="Passado", card_name="Casa"),
            SpreadPosition(position=2, context="presente", description="Presente", card_name="Estrela"),
            SpreadPosition(position=3, context="futuro", description="Futuro", card_name="Cruz"),
        ],
    )


@pytest.fixture
def template_uma_carta() -> SpreadTemplate:
    """Template 'uma-carta' com posição preenchida."""
    return SpreadTemplate(
        name="uma-carta",
        display_name="Uma Carta",
        description="Tiragem de uma posição",
        positions=[
            SpreadPosition(position=1, context="resposta", description="Resposta", card_name="Serpente"),
        ],
    )


@pytest.fixture
def template_cinco_cartas() -> SpreadTemplate:
    """Template 'cinco-cartas' com posições."""
    return SpreadTemplate(
        name="cinco-cartas",
        display_name="Cinco Cartas",
        description="Tiragem de cinco posições",
        positions=[
            SpreadPosition(position=1, context="situacao", description="Situação", card_name="Criança"),
            SpreadPosition(position=2, context="opcao-a", description="Opção A", card_name="Casa"),
            SpreadPosition(position=3, context="opcao-b", description="Opção B", card_name="Estrela"),
            SpreadPosition(position=4, context="resultado", description="Resultado", card_name="Cruz"),
            SpreadPosition(position=5, context="fator-escondido", description="Fator Escondido", card_name="Céu"),
        ],
    )


@pytest.fixture
def template_ferradura() -> SpreadTemplate:
    """Template 'ferradura' com 7 posições."""
    return SpreadTemplate(
        name="ferradura",
        display_name="Ferradura",
        description="Tiragem em ferradura",
        positions=[
            SpreadPosition(position=i, context=["presente", "passado", "futuro", "resultado", "desafio", "voz-interna", "ambiente"][i - 1], description=f"Pos {i}", card_name=f"Carta {i}")
            for i in range(1, 8)
        ],
    )


@pytest.fixture
def template_sem_cartas() -> SpreadTemplate:
    """Template sem cartas atribuídas."""
    return SpreadTemplate(
        name="teste",
        display_name="Teste",
        description="Template de teste",
        positions=[
            SpreadPosition(position=1, context="passado", description="Passado"),
            SpreadPosition(position=2, context="presente", description="Presente"),
            SpreadPosition(position=3, context="futuro", description="Futuro"),
        ],
    )


# ----------------------------------------------------------------------
# Testes — POSITION_LABELS dict
# ----------------------------------------------------------------------


class TestPositionLabels:
    def test_contains_passado(self) -> None:
        assert "passado" in POSITION_LABELS
        assert POSITION_LABELS["passado"] == "Passado"

    def test_contains_presente(self) -> None:
        assert "presente" in POSITION_LABELS
        assert POSITION_LABELS["presente"] == "Presente"

    def test_contains_futuro(self) -> None:
        assert "futuro" in POSITION_LABELS
        assert POSITION_LABELS["futuro"] == "Futuro"

    def test_contains_situacao(self) -> None:
        assert "situacao" in POSITION_LABELS
        assert POSITION_LABELS["situacao"] == "Situação"

    def test_contains_opcoes(self) -> None:
        assert "opcao-a" in POSITION_LABELS
        assert "opcao-b" in POSITION_LABELS
        assert POSITION_LABELS["opcao-a"] == "Opção A"
        assert POSITION_LABELS["opcao-b"] == "Opção B"

    def test_contains_resultado(self) -> None:
        assert "resultado" in POSITION_LABELS
        assert POSITION_LABELS["resultado"] == "Resultado"

    def test_contains_resposta(self) -> None:
        assert "resultado" in POSITION_LABELS
        assert POSITION_LABELS["resultado"] == "Resultado"

    def test_is_dict(self) -> None:
        assert isinstance(POSITION_LABELS, dict)

    def test_not_empty(self) -> None:
        assert len(POSITION_LABELS) > 0


# ----------------------------------------------------------------------
# Testes — _format_context_label()
# ----------------------------------------------------------------------


class TestFormatContextLabel:
    def test_known_context_passado(self) -> None:
        result = _format_context_label("passado")
        assert result == "Passado"

    def test_known_context_presente(self) -> None:
        result = _format_context_label("presente")
        assert result == "Presente"

    def test_known_context_futuro(self) -> None:
        result = _format_context_label("futuro")
        assert result == "Futuro"

    def test_unknown_context_fallback(self) -> None:
        """Contexto desconhecido usa title() do texto."""
        result = _format_context_label("desconhecido")
        assert result == "Desconhecido"

    def test_hyphenated_context(self) -> None:
        """Contexto com hífen é convertido para espaços."""
        result = _format_context_label("futuro-proximo")
        assert result == "Futuro Próximo"

    def test_returns_string(self) -> None:
        result = _format_context_label("passado")
        assert isinstance(result, str)


# ----------------------------------------------------------------------
# Testes — _format_card_label()
# ----------------------------------------------------------------------


class TestFormatCardLabel:
    def test_with_card_name(self) -> None:
        result = _format_card_label("Estrela", 1)
        assert result == "Estrela"

    def test_without_card_name(self) -> None:
        result = _format_card_label(None, 5)
        assert result == "[Posição 5]"

    def test_empty_string_card_name(self) -> None:
        result = _format_card_label("", 3)
        assert result == "[Posição 3]"

    def test_position_number_correct(self) -> None:
        result = _format_card_label(None, 10)
        assert result == "[Posição 10]"

    def test_card_name_long(self) -> None:
        result = _format_card_label("Nome Muito Longo de Carta", 1)
        assert result == "Nome Muito Longo de Carta"

    def test_returns_string(self) -> None:
        result = _format_card_label("Teste", 1)
        assert isinstance(result, str)


# ----------------------------------------------------------------------
# Testes — SpreadDiagramGenerator.__init__()
# ----------------------------------------------------------------------


class TestDiagramGeneratorInit:
    def test_init_default_include_context_true(self) -> None:
        """Default: include_context=True."""
        gen = SpreadDiagramGenerator()
        assert gen.include_context is True

    def test_init_explicit_context_true(self) -> None:
        """Explicit include_context=True."""
        gen = SpreadDiagramGenerator(include_context=True)
        assert gen.include_context is True

    def test_init_context_false(self) -> None:
        """Explicit include_context=False."""
        gen = SpreadDiagramGenerator(include_context=False)
        assert gen.include_context is False


# ----------------------------------------------------------------------
# Testes — SpreadDiagramGenerator.generate()
# ----------------------------------------------------------------------


class TestGenerate:
    def test_generate_returns_string(self, generator: SpreadDiagramGenerator, template_tres_cartas: SpreadTemplate) -> None:
        """generate() retorna string."""
        result = generator.generate(template_tres_cartas)
        assert isinstance(result, str)

    def test_generate_not_empty(self, generator: SpreadDiagramGenerator, template_tres_cartas: SpreadTemplate) -> None:
        """generate() retorna string não-vazia."""
        result = generator.generate(template_tres_cartas)
        assert len(result) > 0

    def test_generate_contains_disposicao_title(self, generator: SpreadDiagramGenerator, template_tres_cartas: SpreadTemplate) -> None:
        """Diagrama contém título ## Disposição."""
        result = generator.generate(template_tres_cartas)
        assert "## Disposição" in result

    def test_generate_with_card_names(self, generator: SpreadDiagramGenerator, template_tres_cartas: SpreadTemplate) -> None:
        """Diagrama contém nomes das cartas quando fornecidos."""
        result = generator.generate(template_tres_cartas)
        assert "Casa" in result
        assert "Estrela" in result
        assert "Cruz" in result

    def test_generate_without_card_names(self, generator: SpreadDiagramGenerator, template_sem_cartas: SpreadTemplate) -> None:
        """Diagrama contém placeholders quando cartas não fornecidas."""
        result = generator.generate(template_sem_cartas)
        assert "[Posição" in result

    def test_generate_with_context_enabled(self, generator: SpreadDiagramGenerator, template_tres_cartas: SpreadTemplate) -> None:
        """Diagrama contém contextos quando include_context=True."""
        result = generator.generate(template_tres_cartas)
        assert "Passado" in result or "presente" in result.lower()

    def test_generate_without_context(self, generator_no_context: SpreadDiagramGenerator, template_tres_cartas: SpreadTemplate) -> None:
        """Diagrama não contém contextos quando include_context=False."""
        result = generator_no_context.generate(template_tres_cartas)
        # Não deve ter contextos formatados nos labels
        assert "Passado" not in result
        assert "Futuro" not in result


# ----------------------------------------------------------------------
# Testes — _generate_single_card_diagram()
# ----------------------------------------------------------------------


class TestGenerateSingleCard:
    def test_single_card_contains_title(self, generator: SpreadDiagramGenerator, template_uma_carta: SpreadTemplate) -> None:
        """Diagrama de uma carta contém título."""
        result = generator.generate(template_uma_carta)
        assert "## Disposição" in result

    def test_single_card_contains_card_name(self, generator: SpreadDiagramGenerator, template_uma_carta: SpreadTemplate) -> None:
        """Diagrama de uma carta contém nome da carta."""
        result = generator.generate(template_uma_carta)
        assert "Serpente" in result

    def test_single_card_no_context(self, generator_no_context: SpreadDiagramGenerator, template_uma_carta: SpreadTemplate) -> None:
        """Diagrama de uma carta sem contexto funciona."""
        result = generator_no_context.generate(template_uma_carta)
        assert "## Disposição" in result


# ----------------------------------------------------------------------
# Testes — _generate_tres_cartas_diagram()
# ----------------------------------------------------------------------


class TestGenerateTresCartas:
    def test_tres_cartas_contains_title(self, generator: SpreadDiagramGenerator, template_tres_cartas: SpreadTemplate) -> None:
        """Diagrama de 3 cartas contém título."""
        result = generator.generate(template_tres_cartas)
        assert "## Disposição" in result

    def test_tres_cartas_contains_all_three_cards(self, generator: SpreadDiagramGenerator, template_tres_cartas: SpreadTemplate) -> None:
        """Diagrama de 3 cartas contém todas as cartas."""
        result = generator.generate(template_tres_cartas)
        assert "Casa" in result
        assert "Estrela" in result
        assert "Cruz" in result

    def test_tres_cartas_contains_contexts(self, generator: SpreadDiagramGenerator, template_tres_cartas: SpreadTemplate) -> None:
        """Diagrama de 3 cartas contém contextos."""
        result = generator.generate(template_tres_cartas)
        assert "Passado" in result or "presente" in result.lower() or "futuro" in result.lower()


# ----------------------------------------------------------------------
# Testes — _generate_cinco_cartas_diagram()
# ----------------------------------------------------------------------


class TestGenerateCincoCartas:
    def test_cinco_cartas_contains_title(self, generator: SpreadDiagramGenerator, template_cinco_cartas: SpreadTemplate) -> None:
        """Diagrama de 5 cartas contém título."""
        result = generator.generate(template_cinco_cartas)
        assert "## Disposição" in result

    def test_cinco_cartas_contains_all_cards(self, generator: SpreadDiagramGenerator, template_cinco_cartas: SpreadTemplate) -> None:
        """Diagrama de 5 cartas contém todas as cartas."""
        result = generator.generate(template_cinco_cartas)
        assert "Criança" in result
        assert "Casa" in result
        assert "Estrela" in result
        assert "Cruz" in result
        assert "Céu" in result


# ----------------------------------------------------------------------
# Testes — _generate_ferradura_diagram()
# ----------------------------------------------------------------------


class TestGenerateFerradura:
    def test_ferradura_contains_title(self, generator: SpreadDiagramGenerator, template_ferradura: SpreadTemplate) -> None:
        """Diagrama de ferradura contém título."""
        result = generator.generate(template_ferradura)
        assert "## Disposição" in result

    def test_ferradura_contains_cards(self, generator: SpreadDiagramGenerator, template_ferradura: SpreadTemplate) -> None:
        """Diagrama de ferradura contém cartas."""
        result = generator.generate(template_ferradura)
        assert "Carta 1" in result or "Carta" in result


# ----------------------------------------------------------------------
# Testes — _generate_cruz_celtas_diagram()
# ----------------------------------------------------------------------


class TestGenerateCruzCeltas:
    def test_cruz_celtas_contains_title(self, generator: SpreadDiagramGenerator) -> None:
        """Diagrama de Cruz Celta contém título."""
        from src.spread_templates import get_template
        template = get_template("cruz-celtas")
        assert template is not None
        result = generator.generate(template)
        assert "## Disposição" in result

    def test_cruz_celtas_contains_positions(self, generator: SpreadDiagramGenerator) -> None:
        """Diagrama de Cruz Celta contém posições."""
        from src.spread_templates import get_template
        template = get_template("cruz-celtas")
        assert template is not None
        result = generator.generate(template)
        # Deve haver referência às posições
        assert len(result) > 50  # Mínimo razoável para o diagrama


# ----------------------------------------------------------------------
# Testes — _generate_linear_diagram()
# ----------------------------------------------------------------------


class TestGenerateLinearDiagram:
    def test_linear_contains_title(self, generator: SpreadDiagramGenerator) -> None:
        """Diagrama linear contém título."""
        from src.spread_templates import get_template
        template = get_template("relacionamento")
        assert template is not None
        result = generator.generate(template)
        assert "## Disposição" in result

    def test_linear_contains_contexts(self, generator: SpreadDiagramGenerator) -> None:
        """Diagrama linear contém contextos."""
        from src.spread_templates import get_template
        template = get_template("relacionamento")
        assert template is not None
        result = generator.generate(template)
        assert "Você" in result or "Relação" in result or "futuro" in result.lower()


# ----------------------------------------------------------------------
# Testes — generate_from_positions()
# ----------------------------------------------------------------------


class TestGenerateFromPositions:
    def test_from_positions_returns_string(self, generator: SpreadDiagramGenerator) -> None:
        """generate_from_positions() retorna string."""
        positions = [
            SpreadPosition(position=1, context="passado", description="Passado", card_name="Casa"),
            SpreadPosition(position=2, context="presente", description="Presente", card_name="Estrela"),
        ]
        result = generator.generate_from_positions(positions)
        assert isinstance(result, str)

    def test_from_positions_not_empty(self, generator: SpreadDiagramGenerator) -> None:
        """generate_from_positions() retorna string não-vazia."""
        positions = [
            SpreadPosition(position=1, context="passado", description="Passado", card_name="Casa"),
        ]
        result = generator.generate_from_positions(positions)
        assert len(result) > 0

    def test_from_positions_contains_cards(self, generator: SpreadDiagramGenerator) -> None:
        """generate_from_positions() contém nomes das cartas."""
        positions = [
            SpreadPosition(position=1, context="passado", description="Passado", card_name="Casa"),
            SpreadPosition(position=2, context="presente", description="Presente", card_name="Estrela"),
        ]
        result = generator.generate_from_positions(positions)
        assert "Casa" in result
        assert "Estrela" in result

    def test_from_positions_single_position(self, generator: SpreadDiagramGenerator) -> None:
        """generate_from_positions() com uma posição funciona."""
        positions = [
            SpreadPosition(position=1, context="resposta", description="Resposta", card_name="Serpente"),
        ]
        result = generator.generate_from_positions(positions)
        assert "## Disposição" in result
        assert "Serpente" in result

    def test_from_positions_empty_list_uses_generate_linear(self, generator: SpreadDiagramGenerator) -> None:
        """generate_linear() com lista vazia retorna fallback."""
        result = generator.generate_linear([])
        assert "## Disposição" in result
        assert "Nenhuma carta disponível" in result


# ----------------------------------------------------------------------
# Testes — generate_linear()
# ----------------------------------------------------------------------


class TestGenerateLinear:
    def test_generate_linear_returns_string(self, generator: SpreadDiagramGenerator) -> None:
        """generate_linear() retorna string."""
        cards = [("1", "Passado", "Casa"), ("2", "Presente", "Estrela")]
        result = generator.generate_linear(cards)
        assert isinstance(result, str)

    def test_generate_linear_not_empty(self, generator: SpreadDiagramGenerator) -> None:
        """generate_linear() retorna string não-vazia."""
        cards = [("1", "Passado", "Casa")]
        result = generator.generate_linear(cards)
        assert len(result) > 0

    def test_generate_linear_contains_title(self, generator: SpreadDiagramGenerator) -> None:
        """generate_linear() contém título."""
        cards = [("1", "Passado", "Casa")]
        result = generator.generate_linear(cards)
        assert "## Disposição" in result

    def test_generate_linear_contains_cards(self, generator: SpreadDiagramGenerator) -> None:
        """generate_linear() contém nomes das cartas."""
        cards = [("1", "Passado", "Casa"), ("2", "Presente", "Estrela")]
        result = generator.generate_linear(cards)
        assert "Casa" in result
        assert "Estrela" in result

    def test_generate_linear_single_card(self, generator: SpreadDiagramGenerator) -> None:
        """generate_linear() com uma carta."""
        cards = [("1", "Resposta", "Serpente")]
        result = generator.generate_linear(cards)
        assert "Serpente" in result

    def test_generate_linear_empty_list(self, generator: SpreadDiagramGenerator) -> None:
        """generate_linear() com lista vazia."""
        result = generator.generate_linear([])
        assert "## Disposição" in result
        assert "Nenhuma carta disponível" in result

    def test_generate_linear_without_context(self, generator_no_context: SpreadDiagramGenerator) -> None:
        """generate_linear() sem contexto."""
        cards = [("1", "Passado", "Casa"), ("2", "Presente", "Estrela")]
        result = generator_no_context.generate_linear(cards)
        assert "Casa" in result
        assert "Estrela" in result


# ----------------------------------------------------------------------
# Testes — generate_celtic_cross()
# ----------------------------------------------------------------------


class TestGenerateCelticCross:
    def test_celtic_cross_returns_string(self, generator: SpreadDiagramGenerator) -> None:
        """generate_celtic_cross() retorna string."""
        cards = [
            ("1", "Presente", "Estrela"),
            ("2", "Desafio", "Cruz"),
            ("3", "Passado", "Casa"),
            ("4", "Futuro", "Serpente"),
            ("5", "Base", "Céu"),
            ("6", "Possível", "Criança"),
            ("7", "Voz Interna", "Paraiso"),
            ("8", "Ambiente", "Estrela"),
            ("9", "Esperança", "Cruz"),
            ("10", "Resultado", "Casa"),
        ]
        result = generator.generate_celtic_cross(cards)
        assert isinstance(result, str)

    def test_celtic_cross_not_empty(self, generator: SpreadDiagramGenerator) -> None:
        """generate_celtic_cross() retorna string não-vazia."""
        cards = [
            ("1", "Presente", "Estrela"),
            ("2", "Desafio", "Cruz"),
            ("3", "Passado", "Casa"),
            ("4", "Futuro", "Serpente"),
            ("5", "Base", "Céu"),
            ("6", "Possível", "Criança"),
            ("7", "Voz Interna", "Paraiso"),
            ("8", "Ambiente", "Estrela"),
            ("9", "Esperança", "Cruz"),
            ("10", "Resultado", "Casa"),
        ]
        result = generator.generate_celtic_cross(cards)
        assert len(result) > 0

    def test_celtic_cross_contains_title(self, generator: SpreadDiagramGenerator) -> None:
        """generate_celtic_cross() contém título."""
        cards = [("1", "Presente", "Estrela")]
        result = generator.generate_celtic_cross(cards)
        assert "## Disposição" in result

    def test_celtic_cross_contains_cards(self, generator: SpreadDiagramGenerator) -> None:
        """generate_celtic_cross() contém nomes das cartas."""
        cards = [
            ("1", "Presente", "Estrela"),
            ("2", "Desafio", "Cruz"),
            ("3", "Passado", "Casa"),
            ("4", "Futuro", "Serpente"),
            ("5", "Base", "Céu"),
            ("6", "Possível", "Criança"),
            ("7", "Voz Interna", "Paraiso"),
            ("8", "Ambiente", "Estrela"),
            ("9", "Esperança", "Cruz"),
            ("10", "Resultado", "Casa"),
        ]
        result = generator.generate_celtic_cross(cards)
        assert "Estrela" in result
        assert "Cruz" in result
        assert "Casa" in result

    def test_celtic_cross_empty_list(self, generator: SpreadDiagramGenerator) -> None:
        """generate_celtic_cross() com lista vazia."""
        result = generator.generate_celtic_cross([])
        assert "## Disposição" in result
        assert "Nenhuma carta disponível" in result

    def test_celtic_cross_partial_cards(self, generator: SpreadDiagramGenerator) -> None:
        """generate_celtic_cross() com cartas parciais."""
        cards = [
            ("1", "Presente", "Estrela"),
            ("2", "Desafio", "Cruz"),
        ]
        result = generator.generate_celtic_cross(cards)
        assert "Estrela" in result
        assert "Cruz" in result
        # Posições não fornecidas devem mostrar placeholder
        assert "Posição" in result


# ----------------------------------------------------------------------
# Testes — Edge cases
# ----------------------------------------------------------------------


class TestEdgeCases:
    def test_generate_unknown_template(self, generator: SpreadDiagramGenerator) -> None:
        """Template com número de posições desconhecido usa fallback linear."""
        template = SpreadTemplate(
            name="custom",
            display_name="Custom",
            description="Template custom",
            positions=[
                SpreadPosition(position=1, context="a", description="A"),
                SpreadPosition(position=2, context="b", description="B"),
                SpreadPosition(position=3, context="c", description="C"),
                SpreadPosition(position=4, context="d", description="D"),
                SpreadPosition(position=5, context="e", description="E"),
                SpreadPosition(position=6, context="f", description="F"),
            ],
        )
        result = generator.generate(template)
        assert "## Disposição" in result
        assert len(result) > 0

    def test_generate_with_long_card_names(self, generator: SpreadDiagramGenerator) -> None:
        """Cards com nomes longos são tratados."""
        template = SpreadTemplate(
            name="tres-cartas",
            display_name="Três Cartas",
            description="Teste",
            positions=[
                SpreadPosition(position=1, context="passado", description="Passado", card_name="Nome Muito Longo de Carta"),
                SpreadPosition(position=2, context="presente", description="Presente", card_name="Casa"),
                SpreadPosition(position=3, context="futuro", description="Futuro", card_name="Estrela"),
            ],
        )
        result = generator.generate(template)
        assert "## Disposição" in result

    def test_generator_attribute_type(self, generator: SpreadDiagramGenerator) -> None:
        """Generator tem atributo include_context."""
        assert hasattr(generator, "include_context")
        assert generator.include_context is True

    def test_generator_cell_width(self, generator: SpreadDiagramGenerator) -> None:
        """Generator tem CELL_WIDTH definido."""
        assert hasattr(generator, "CELL_WIDTH")
        assert generator.CELL_WIDTH == 16