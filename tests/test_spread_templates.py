"""Testes unitários para src/spread_templates.py.

Cobertura:
- SpreadPosition dataclass — atributos e valores
- SpreadTemplate dataclass — atributos e valores
- TEMPLATES dict — templates disponíveis
- get_template() — recuperação por nome
- list_templates() — listagem de nomes
- Validação de templates individuais
"""

import pytest

from clareza.spread_templates import (
    TEMPLATES,
    SpreadPosition,
    SpreadTemplate,
    get_template,
    list_templates,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def tres_cartas() -> SpreadTemplate:
    """Template 'tres-cartas' para testes."""
    return TEMPLATES["tres-cartas"]


@pytest.fixture
def cruz_celtas() -> SpreadTemplate:
    """Template 'cruz-celtas' para testes."""
    return TEMPLATES["cruz-celtas"]


@pytest.fixture
def ferradura() -> SpreadTemplate:
    """Template 'ferradura' para testes."""
    return TEMPLATES["ferradura"]


@pytest.fixture
def cinco_cartas() -> SpreadTemplate:
    """Template 'cinco-cartas' para testes."""
    return TEMPLATES["cinco-cartas"]


@pytest.fixture
def uma_carta() -> SpreadTemplate:
    """Template 'uma-carta' para testes."""
    return TEMPLATES["uma-carta"]


@pytest.fixture
def relacionamento() -> SpreadTemplate:
    """Template 'relacionamento' para testes."""
    return TEMPLATES["relacionamento"]


# ----------------------------------------------------------------------
# Testes — SpreadPosition dataclass
# ----------------------------------------------------------------------


class TestSpreadPosition:
    def test_creation_with_required_fields(self) -> None:
        pos = SpreadPosition(position=1, context="passado", description="Teste")
        assert pos.position == 1
        assert pos.context == "passado"
        assert pos.description == "Teste"
        assert pos.card_name is None

    def test_creation_with_all_fields(self) -> None:
        pos = SpreadPosition(
            position=2,
            context="presente",
            description="Situação atual",
            card_name="Cruz",
        )
        assert pos.position == 2
        assert pos.context == "presente"
        assert pos.description == "Situação atual"
        assert pos.card_name == "Cruz"

    def test_position_is_1_based(self) -> None:
        pos = SpreadPosition(position=1, context="teste", description="desc")
        assert pos.position == 1

    def test_card_name_optional(self) -> None:
        pos = SpreadPosition(position=1, context="teste", description="desc")
        assert pos.card_name is None


# ----------------------------------------------------------------------
# Testes — SpreadTemplate dataclass
# ----------------------------------------------------------------------


class TestSpreadTemplate:
    def test_creation_with_required_fields(self) -> None:
        pos = SpreadPosition(position=1, context="teste", description="desc")
        template = SpreadTemplate(
            name="teste",
            display_name="Teste",
            description="Template de teste",
            positions=[pos],
        )
        assert template.name == "teste"
        assert template.display_name == "Teste"
        assert template.description == "Template de teste"
        assert len(template.positions) == 1
        assert template.positions[0].position == 1

    def test_positions_is_list(self) -> None:
        template = SpreadTemplate(
            name="teste",
            display_name="Teste",
            description="desc",
            positions=[],
        )
        assert isinstance(template.positions, list)
        assert template.positions == []


# ----------------------------------------------------------------------
# Testes — TEMPLATES dict
# ----------------------------------------------------------------------


class TestTemplatesDict:
    def test_all_templates_exist(self) -> None:
        expected_templates = [
            "tres-cartas",
            "cruz-celtas",
            "ferradura",
            "cinco-cartas",
            "uma-carta",
            "relacionamento",
        ]
        for name in expected_templates:
            assert name in TEMPLATES, f"Template '{name}' não encontrado"

    def test_templates_is_dict(self) -> None:
        assert isinstance(TEMPLATES, dict)

    def test_templates_not_empty(self) -> None:
        assert len(TEMPLATES) > 0


# ----------------------------------------------------------------------
# Testes — get_template()
# ----------------------------------------------------------------------


class TestGetTemplate:
    def test_get_existing_template(self) -> None:
        template = get_template("tres-cartas")
        assert template is not None
        assert template.name == "tres-cartas"

    def test_get_nonexistent_template_returns_none(self) -> None:
        template = get_template("inexistente")
        assert template is None

    def test_get_template_case_sensitive(self) -> None:
        template = get_template("TRES-CARTAS")
        assert template is None

    def test_get_template_empty_string(self) -> None:
        template = get_template("")
        assert template is None

    def test_get_all_templates(self) -> None:
        for name in TEMPLATES:
            template = get_template(name)
            assert template is not None
            assert template.name == name


# ----------------------------------------------------------------------
# Testes — list_templates()
# ----------------------------------------------------------------------


class TestListTemplates:
    def test_returns_list(self) -> None:
        result = list_templates()
        assert isinstance(result, list)

    def test_returns_all_template_names(self) -> None:
        result = list_templates()
        assert len(result) == len(TEMPLATES)
        for name in TEMPLATES:
            assert name in result

    def test_list_preserves_insertion_order(self) -> None:
        """Lista mantém a ordem de inserção do dict."""
        result = list_templates()
        # Verifica que todos os templates estão na mesma ordem que aparecem no TEMPLATES
        for i, name in enumerate(TEMPLATES.keys()):
            assert result[i] == name

    def test_list_contains_strings(self) -> None:
        result = list_templates()
        assert all(isinstance(name, str) for name in result)


# ----------------------------------------------------------------------
# Testes — Template: tres-cartas
# ----------------------------------------------------------------------


class TestTemplateTresCartas:
    def test_name_and_display_name(self, tres_cartas: SpreadTemplate) -> None:
        assert tres_cartas.name == "tres-cartas"
        assert tres_cartas.display_name == "Três Cartas"

    def test_description(self, tres_cartas: SpreadTemplate) -> None:
        assert "passado" in tres_cartas.description
        assert "presente" in tres_cartas.description
        assert "futuro" in tres_cartas.description

    def test_has_three_positions(self, tres_cartas: SpreadTemplate) -> None:
        assert len(tres_cartas.positions) == 3

    def test_positions_sequential(self, tres_cartas: SpreadTemplate) -> None:
        positions = tres_cartas.positions
        assert positions[0].position == 1
        assert positions[1].position == 2
        assert positions[2].position == 3

    def test_contexts(self, tres_cartas: SpreadTemplate) -> None:
        contexts = [p.context for p in tres_cartas.positions]
        assert "passado" in contexts
        assert "presente" in contexts
        assert "futuro" in contexts

    def test_descriptions_not_empty(self, tres_cartas: SpreadTemplate) -> None:
        for pos in tres_cartas.positions:
            assert len(pos.description) > 0

    def test_all_card_names_none(self, tres_cartas: SpreadTemplate) -> None:
        for pos in tres_cartas.positions:
            assert pos.card_name is None


# ----------------------------------------------------------------------
# Testes — Template: cruz-celtas
# ----------------------------------------------------------------------


class TestTemplateCruzCeltas:
    def test_name_and_display_name(self, cruz_celtas: SpreadTemplate) -> None:
        assert cruz_celtas.name == "cruz-celtas"
        assert cruz_celtas.display_name == "Cruz Celta"

    def test_has_ten_positions(self, cruz_celtas: SpreadTemplate) -> None:
        assert len(cruz_celtas.positions) == 10

    def test_positions_sequential(self, cruz_celtas: SpreadTemplate) -> None:
        positions = cruz_celtas.positions
        assert positions[0].position == 1
        assert positions[9].position == 10

    def test_contexts(self, cruz_celtas: SpreadTemplate) -> None:
        contexts = [p.context for p in cruz_celtas.positions]
        assert "presente" in contexts
        assert "desafio" in contexts
        assert "base" in contexts
        assert "passado" in contexts
        assert "futuro" in contexts
        assert "resultado" in contexts

    def test_descriptions_not_empty(self, cruz_celtas: SpreadTemplate) -> None:
        for pos in cruz_celtas.positions:
            assert len(pos.description) > 0


# ----------------------------------------------------------------------
# Testes — Template: ferradura
# ----------------------------------------------------------------------


class TestTemplateFerradura:
    def test_name_and_display_name(self, ferradura: SpreadTemplate) -> None:
        assert ferradura.name == "ferradura"
        assert ferradura.display_name == "Ferradura"

    def test_has_seven_positions(self, ferradura: SpreadTemplate) -> None:
        assert len(ferradura.positions) == 7

    def test_positions_sequential(self, ferradura: SpreadTemplate) -> None:
        positions = ferradura.positions
        assert positions[0].position == 1
        assert positions[6].position == 7

    def test_contexts(self, ferradura: SpreadTemplate) -> None:
        contexts = [p.context for p in ferradura.positions]
        assert "presente" in contexts
        assert "passado" in contexts
        assert "futuro" in contexts
        assert "resultado" in contexts

    def test_descriptions_not_empty(self, ferradura: SpreadTemplate) -> None:
        for pos in ferradura.positions:
            assert len(pos.description) > 0


# ----------------------------------------------------------------------
# Testes — Template: cinco-cartas
# ----------------------------------------------------------------------


class TestTemplateCincoCartas:
    def test_name_and_display_name(self, cinco_cartas: SpreadTemplate) -> None:
        assert cinco_cartas.name == "cinco-cartas"
        assert cinco_cartas.display_name == "Cinco Cartas"

    def test_has_five_positions(self, cinco_cartas: SpreadTemplate) -> None:
        assert len(cinco_cartas.positions) == 5

    def test_positions_sequential(self, cinco_cartas: SpreadTemplate) -> None:
        positions = cinco_cartas.positions
        assert positions[0].position == 1
        assert positions[4].position == 5

    def test_contexts(self, cinco_cartas: SpreadTemplate) -> None:
        contexts = [p.context for p in cinco_cartas.positions]
        assert "situacao" in contexts
        assert "opcao-a" in contexts
        assert "opcao-b" in contexts
        assert "resultado" in contexts

    def test_descriptions_not_empty(self, cinco_cartas: SpreadTemplate) -> None:
        for pos in cinco_cartas.positions:
            assert len(pos.description) > 0


# ----------------------------------------------------------------------
# Testes — Template: uma-carta
# ----------------------------------------------------------------------


class TestTemplateUmaCarta:
    def test_name_and_display_name(self, uma_carta: SpreadTemplate) -> None:
        assert uma_carta.name == "uma-carta"
        assert uma_carta.display_name == "Uma Carta"

    def test_has_one_position(self, uma_carta: SpreadTemplate) -> None:
        assert len(uma_carta.positions) == 1

    def test_position_is_1(self, uma_carta: SpreadTemplate) -> None:
        assert uma_carta.positions[0].position == 1

    def test_context_is_resposta(self, uma_carta: SpreadTemplate) -> None:
        assert uma_carta.positions[0].context == "resposta"

    def test_description_not_empty(self, uma_carta: SpreadTemplate) -> None:
        assert len(uma_carta.positions[0].description) > 0


# ----------------------------------------------------------------------
# Testes — Template: relacionamento
# ----------------------------------------------------------------------


class TestTemplateRelacionamento:
    def test_name_and_display_name(self, relacionamento: SpreadTemplate) -> None:
        assert relacionamento.name == "relacionamento"
        assert relacionamento.display_name == "Relacionamento"

    def test_has_five_positions(self, relacionamento: SpreadTemplate) -> None:
        assert len(relacionamento.positions) == 5

    def test_positions_sequential(self, relacionamento: SpreadTemplate) -> None:
        positions = relacionamento.positions
        assert positions[0].position == 1
        assert positions[4].position == 5

    def test_contexts(self, relacionamento: SpreadTemplate) -> None:
        contexts = [p.context for p in relacionamento.positions]
        assert "voce" in contexts
        assert "ele-ela" in contexts
        assert "relacao" in contexts
        assert "passado" in contexts
        assert "futuro" in contexts

    def test_descriptions_not_empty(self, relacionamento: SpreadTemplate) -> None:
        for pos in relacionamento.positions:
            assert len(pos.description) > 0


# ----------------------------------------------------------------------
# Testes — Consistência entre templates
# ----------------------------------------------------------------------


class TestTemplatesConsistency:
    def test_all_templates_have_name(self) -> None:
        for template in TEMPLATES.values():
            assert template.name is not None
            assert len(template.name) > 0

    def test_all_templates_have_display_name(self) -> None:
        for template in TEMPLATES.values():
            assert template.display_name is not None
            assert len(template.display_name) > 0

    def test_all_templates_have_description(self) -> None:
        for template in TEMPLATES.values():
            assert template.description is not None
            assert len(template.description) > 0

    def test_all_templates_have_positions(self) -> None:
        for template in TEMPLATES.values():
            assert template.positions is not None
            assert len(template.positions) > 0

    def test_all_position_numbers_positive(self) -> None:
        for template in TEMPLATES.values():
            for pos in template.positions:
                assert pos.position > 0

    def test_all_position_contexts_non_empty(self) -> None:
        for template in TEMPLATES.values():
            for pos in template.positions:
                assert pos.context is not None
                assert len(pos.context) > 0

    def test_all_position_descriptions_non_empty(self) -> None:
        for template in TEMPLATES.values():
            for pos in template.positions:
                assert pos.description is not None
                assert len(pos.description) > 0

    def test_template_names_unique(self) -> None:
        names = [t.name for t in TEMPLATES.values()]
        assert len(names) == len(set(names))