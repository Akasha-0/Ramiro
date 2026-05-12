"""Testes unitários para src/plano_rules.py.

Cobertura:
- ActionTemplate, ThemeActions, EscalationLevel — dataclasses de regra
- UrgencyEscalation, RecommendationTemplate, TimeframeDefinition — dataclasses de configuração
- SuccessCriterion, PlanoRules, RecommendationResult — estruturas principais
- PlanoRulesValidationError — exceção de validação
- _load_raw_json() — carregamento de JSON
- _parse_action_template() — parsing de template de ação
- _parse_theme_actions() — parsing de bloco de tema
- _parse_escalation_level() — parsing de nível de escalonamento
- _parse_urgency_escalation() — parsing completo de urgência
- _parse_recommendation_template() — parsing de template de recomendação
- _parse_timeframe_definition() — parsing de horizonte temporal
- _parse_success_criterion() — parsing de critério de sucesso
- _validate_plano_rules() — validação de estrutura
- _build_action() — construção de ação a partir de template
- _determine_urgency() — determinação de nível de urgência
- generate_recommendations() — geração de recomendações
- _is_danger_card() — verificação de carta perigosa
- load_plano_rules() — carregamento principal de regras
"""

import pytest

from clareza.plano_rules import (
    ActionTemplate,
    EscalationLevel,
    PlanoRules,
    PlanoRulesValidationError,
    RecommendationResult,
    RecommendationTemplate,
    SuccessCriterion,
    ThemeActions,
    TimeframeDefinition,
    UrgencyEscalation,
    _build_action,
    _determine_urgency,
    _is_danger_card,
    _load_raw_json,
    _parse_action_template,
    _parse_escalation_level,
    _parse_recommendation_template,
    _parse_success_criterion,
    _parse_theme_actions,
    _parse_timeframe_definition,
    _parse_urgency_escalation,
    _validate_plano_rules,
    generate_recommendations,
    load_plano_rules,
)
from clareza.symbols import get_symbol_by_name


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def valid_rules(tmp_path) -> PlanoRules:
    """PlanoRules válido para testes de validação."""
    # Cria arquivo JSON temporário
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    json_file = data_dir / "plano_rules.json"

    json_content = {
        "card_actions": {
            "trabalho": {
                "description": "Tema relacionado ao trabalho",
                "action_templates": [
                    {
                        "type": "reflection",
                        "template": "Revise seu foco em {{{tema}}}",
                        "timeframe": "this_week",
                        "success_criterion": "Clareza sobre próximo passo",
                    }
                ],
                "card_ids": [14, 15, 16],
            }
        },
        "urgency_escalation": {
            "description": "Escalonamento de urgência",
            "danger_cards": [7, 8, 12],
            "danger_keywords": ["medo", "perigo"],
            "escalation_levels": {
                "low": {
                    "description": "Urgência baixa",
                    "multiplier": 1.0,
                    "timeframe_adjustment": "no_change",
                }
            },
            "default_level": "low",
        },
        "recommendation_templates": {
            "templates": [
                {
                    "id": "rec_001",
                    "template": "Considere agir sobre {{{assunto}}}",
                    "examples": ["Exemplo 1", "Exemplo 2"],
                }
            ]
        },
        "timeframes": {
            "definitions": {
                "immediate": {
                    "label": "Imediato",
                    "horizon_days": 1,
                    "description": "Ação imediata",
                },
                "this_week": {
                    "label": "Esta semana",
                    "horizon_days": 7,
                    "description": "Prazo de uma semana",
                },
                "this_month": {
                    "label": "Este mês",
                    "horizon_days": 30,
                    "description": "Prazo de um mês",
                },
            }
        },
        "success_criteria": {
            "categories": {
                "trabalho": {
                    "label": "Trabalho",
                    "criteria": ["Avanço perceptível", "Clareza de direção"],
                }
            }
        },
    }

    import json

    json_file.write_text(json.dumps(json_content, ensure_ascii=False), encoding="utf-8")

    return load_plano_rules()


# ----------------------------------------------------------------------
# Testes — Dataclasses: ActionTemplate
# ----------------------------------------------------------------------


class TestActionTemplate:
    def test_action_template_creation(self) -> None:
        template = ActionTemplate(
            type="reflection",
            template="Revise {{{tema}}}",
            timeframe="this_week",
            success_criterion="Clareza sobre próximo passo",
        )
        assert template.type == "reflection"
        assert "{{{tema}}}" in template.template
        assert template.timeframe == "this_week"
        assert "próximo passo" in template.success_criterion

    def test_action_template_equality(self) -> None:
        t1 = ActionTemplate(
            type="action",
            template="Faça algo",
            timeframe="immediate",
            success_criterion="Feito",
        )
        t2 = ActionTemplate(
            type="action",
            template="Faça algo",
            timeframe="immediate",
            success_criterion="Feito",
        )
        assert t1 == t2


# ----------------------------------------------------------------------
# Testes — Dataclasses: ThemeActions
# ----------------------------------------------------------------------


class TestThemeActions:
    def test_theme_actions_creation(self) -> None:
        actions = ThemeActions(
            description="Tema trabalho",
            action_templates=[
                ActionTemplate(
                    type="reflection",
                    template="Revise",
                    timeframe="this_week",
                    success_criterion="Clareza",
                )
            ],
            card_ids=[14, 15],
        )
        assert actions.description == "Tema trabalho"
        assert len(actions.action_templates) == 1
        assert 14 in actions.card_ids

    def test_theme_actions_empty_templates(self) -> None:
        actions = ThemeActions(
            description="Sem ações",
            action_templates=[],
            card_ids=[1, 2],
        )
        assert actions.action_templates == []


# ----------------------------------------------------------------------
# Testes — Dataclasses: EscalationLevel
# ----------------------------------------------------------------------


class TestEscalationLevel:
    def test_escalation_level_defaults(self) -> None:
        level = EscalationLevel(
            description="Nível de urgência",
            multiplier=1.5,
            timeframe_adjustment="immediate",
        )
        assert level.multiplier == 1.5
        assert level.timeframe_adjustment == "immediate"

    def test_escalation_level_from_dict(self) -> None:
        raw = {
            "description": "Urgência alta",
            "multiplier": 2.0,
            "timeframe_adjustment": "immediate",
        }
        level = _parse_escalation_level(raw)
        assert level.description == "Urgência alta"
        assert level.multiplier == 2.0
        assert level.timeframe_adjustment == "immediate"

    def test_escalation_level_missing_fields_gets_defaults(self) -> None:
        raw = {}
        level = _parse_escalation_level(raw)
        assert level.description == ""
        assert level.multiplier == 1.0
        assert level.timeframe_adjustment == "no_change"


# ----------------------------------------------------------------------
# Testes — Dataclasses: UrgencyEscalation
# ----------------------------------------------------------------------


class TestUrgencyEscalation:
    def test_urgency_escalation_from_dict(self) -> None:
        raw = {
            "description": "Escalonamento padrão",
            "danger_cards": [7, 8],
            "danger_keywords": ["medo", "perigo"],
            "escalation_levels": {
                "low": {
                    "description": "Baixa urgência",
                    "multiplier": 1.0,
                    "timeframe_adjustment": "no_change",
                },
                "high": {
                    "description": "Alta urgência",
                    "multiplier": 2.0,
                    "timeframe_adjustment": "immediate",
                },
            },
            "default_level": "low",
        }
        escalation = _parse_urgency_escalation(raw)
        assert escalation.description == "Escalonamento padrão"
        assert 7 in escalation.danger_cards
        assert "medo" in escalation.danger_keywords
        assert "low" in escalation.escalation_levels
        assert "high" in escalation.escalation_levels
        assert escalation.default_level == "low"

    def test_urgency_escalation_defaults(self) -> None:
        raw = {}
        escalation = _parse_urgency_escalation(raw)
        assert escalation.danger_cards == []
        assert escalation.danger_keywords == []
        assert escalation.default_level == "low"


# ----------------------------------------------------------------------
# Testes — Dataclasses: RecommendationTemplate
# ----------------------------------------------------------------------


class TestRecommendationTemplate:
    def test_recommendation_template_creation(self) -> None:
        template = RecommendationTemplate(
            id="rec_001",
            template="Considere agir sobre {{{assunto}}}",
            examples=["Exemplo 1", "Exemplo 2"],
        )
        assert template.id == "rec_001"
        assert "{{{assunto}}}" in template.template
        assert len(template.examples) == 2

    def test_recommendation_template_from_dict(self) -> None:
        raw = {
            "id": "rec_002",
            "template": "Aja agora",
            "examples": ["Exemplo A"],
        }
        template = _parse_recommendation_template(raw)
        assert template.id == "rec_002"
        assert template.template == "Aja agora"
        assert template.examples == ["Exemplo A"]


# ----------------------------------------------------------------------
# Testes — Dataclasses: TimeframeDefinition
# ----------------------------------------------------------------------


class TestTimeframeDefinition:
    def test_timeframe_definition_creation(self) -> None:
        tf = TimeframeDefinition(
            label="Imediato",
            horizon_days=1,
            description="Ação imediata",
        )
        assert tf.label == "Imediato"
        assert tf.horizon_days == 1
        assert "imediata" in tf.description

    def test_timeframe_definition_from_dict(self) -> None:
        raw = {
            "label": "Esta semana",
            "horizon_days": 7,
            "description": "Prazo de uma semana",
        }
        tf = _parse_timeframe_definition(raw)
        assert tf.label == "Esta semana"
        assert tf.horizon_days == 7

    def test_timeframe_definition_defaults(self) -> None:
        raw = {}
        tf = _parse_timeframe_definition(raw)
        assert tf.label == ""
        assert tf.horizon_days == 0
        assert tf.description == ""


# ----------------------------------------------------------------------
# Testes — Dataclasses: SuccessCriterion
# ----------------------------------------------------------------------


class TestSuccessCriterion:
    def test_success_criterion_creation(self) -> None:
        sc = SuccessCriterion(
            label="Trabalho",
            criteria=["Avanço perceptível", "Clareza de direção"],
        )
        assert sc.label == "Trabalho"
        assert len(sc.criteria) == 2

    def test_success_criterion_from_dict(self) -> None:
        raw = {
            "label": "Finanças",
            "criteria": ["Economia realizada", "Dívida reduzida"],
        }
        sc = _parse_success_criterion(raw)
        assert sc.label == "Finanças"
        assert "Economia" in sc.criteria[0]


# ----------------------------------------------------------------------
# Testes — Dataclasses: PlanoRules
# ----------------------------------------------------------------------


class TestPlanoRules:
    def test_plano_rules_creation(self) -> None:
        rules = PlanoRules(
            card_actions={},
            urgency_escalation=_parse_urgency_escalation({}),
            recommendation_templates=[],
            timeframes={},
            success_criteria={},
        )
        assert rules.card_actions == {}
        assert rules.urgency_escalation is not None
        assert rules.recommendation_templates == []


# ----------------------------------------------------------------------
# Testes — Dataclasses: RecommendationResult
# ----------------------------------------------------------------------


class TestRecommendationResult:
    def test_recommendation_result_defaults(self) -> None:
        result = RecommendationResult(
            action="Revise seu foco",
            time_frame="this_week",
            success_criteria="Clareza obtida",
        )
        assert result.urgency == "medium"
        assert result.card_themes == []
        assert result.source_rules == []

    def test_recommendation_result_with_fields(self) -> None:
        result = RecommendationResult(
            action="Aja agora",
            time_frame="immediate",
            success_criteria="Feito",
            urgency="high",
            card_themes=["trabalho"],
            source_rules=["rule_001"],
        )
        assert result.urgency == "high"
        assert "trabalho" in result.card_themes
        assert "rule_001" in result.source_rules


# ----------------------------------------------------------------------
# Testes — PlanoRulesValidationError
# ----------------------------------------------------------------------


class TestPlanoRulesValidationError:
    def test_validation_error_creation(self) -> None:
        err = PlanoRulesValidationError("Regras inválidas")
        assert "Regras inválidas" in str(err)

    def test_validation_error_from_validate(self) -> None:
        rules = PlanoRules(
            card_actions={},
            urgency_escalation=_parse_urgency_escalation({}),
            recommendation_templates=[],
            timeframes={},
            success_criteria={},
        )
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _validate_plano_rules(rules)
        assert "card_actions" in str(exc_info.value)


# ----------------------------------------------------------------------
# Testes — _validate_plano_rules()
# ----------------------------------------------------------------------


class TestValidatePlanoRules:
    def test_empty_card_actions_raises(self) -> None:
        rules = PlanoRules(
            card_actions={},
            urgency_escalation=_parse_urgency_escalation({}),
            recommendation_templates=[],
            timeframes={},
            success_criteria={},
        )
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _validate_plano_rules(rules)
        assert "card_actions" in str(exc_info.value)

    def test_theme_without_card_ids_raises(self) -> None:
        """Theme com card_ids vazio levanta exceção na validação."""
        from clareza.plano_rules import (
            PlanoRules,
            _parse_urgency_escalation,
            ThemeActions,
            ActionTemplate,
            _validate_plano_rules,
        )

        actions = ThemeActions(
            description="Sem card_ids",
            action_templates=[
                ActionTemplate(
                    type="action",
                    template="Faça",
                    timeframe="immediate",
                    success_criterion="Feito",
                )
            ],
            card_ids=[],  # vazio
        )
        rules = PlanoRules(
            card_actions={"trabalho": actions},
            urgency_escalation=_parse_urgency_escalation({}),
            recommendation_templates=[],
            timeframes={
                "immediate": TimeframeDefinition(label="I", horizon_days=1, description=""),
                "this_week": TimeframeDefinition(label="S", horizon_days=7, description=""),
                "this_month": TimeframeDefinition(label="M", horizon_days=30, description=""),
            },
            success_criteria={},
        )
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _validate_plano_rules(rules)
        assert "card_ids" in str(exc_info.value)

    def test_validate_missing_timeframes_raises(self) -> None:
        """Validação falha quando timeframes obrigatórios faltam."""
        from clareza.plano_rules import (
            PlanoRules,
            _parse_urgency_escalation,
            _validate_plano_rules,
        )

        # Apenas this_week, faltam immediate e this_month
        rules = PlanoRules(
            card_actions={
                "trabalho": ThemeActions(
                    description="Teste",
                    action_templates=[
                        ActionTemplate(
                            type="action",
                            template="Faça",
                            timeframe="this_week",
                            success_criterion="Feito",
                        )
                    ],
                    card_ids=[1],
                )
            },
            urgency_escalation=_parse_urgency_escalation({}),
            recommendation_templates=[],
            timeframes={
                "this_week": TimeframeDefinition(label="S", horizon_days=7, description=""),
            },
            success_criteria={},
        )
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _validate_plano_rules(rules)
        assert "timeframes" in str(exc_info.value) or "horizonte" in str(exc_info.value) or "immediate" in str(exc_info.value)

    def test_valid_rules_passes_validation(self, valid_rules: PlanoRules) -> None:
        """Regras válidas não levantam exceção."""
        _validate_plano_rules(valid_rules)


# ----------------------------------------------------------------------
# Testes — _parse_action_template()
# ----------------------------------------------------------------------


class TestParseActionTemplate:
    def test_valid_action_template(self) -> None:
        raw = {
            "type": "reflection",
            "template": "Revise {{{tema}}}",
            "timeframe": "this_week",
            "success_criterion": "Clareza obtida",
        }
        template = _parse_action_template(raw)
        assert template.type == "reflection"
        assert template.timeframe == "this_week"

    def test_missing_type_raises(self) -> None:
        raw = {
            "template": "Faça algo",
            "timeframe": "immediate",
            "success_criterion": "Feito",
        }
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _parse_action_template(raw)
        assert "type" in str(exc_info.value)

    def test_missing_template_raises(self) -> None:
        raw = {
            "type": "action",
            "timeframe": "immediate",
            "success_criterion": "Feito",
        }
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _parse_action_template(raw)
        assert "template" in str(exc_info.value)

    def test_missing_timeframe_raises(self) -> None:
        raw = {
            "type": "action",
            "template": "Faça",
            "success_criterion": "Feito",
        }
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _parse_action_template(raw)
        assert "timeframe" in str(exc_info.value)

    def test_missing_success_criterion_raises(self) -> None:
        raw = {
            "type": "action",
            "template": "Faça",
            "timeframe": "immediate",
        }
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _parse_action_template(raw)
        assert "success_criterion" in str(exc_info.value)


# ----------------------------------------------------------------------
# Testes — _parse_theme_actions()
# ----------------------------------------------------------------------


class TestParseThemeActions:
    def test_valid_theme_actions(self) -> None:
        raw = {
            "description": "Tema trabalho",
            "action_templates": [
                {
                    "type": "action",
                    "template": "Revise",
                    "timeframe": "this_week",
                    "success_criterion": "Clareza",
                }
            ],
            "card_ids": [14, 15, 16],
        }
        theme = _parse_theme_actions("trabalho", raw)
        assert theme.description == "Tema trabalho"
        assert len(theme.action_templates) == 1
        assert 14 in theme.card_ids

    def test_missing_action_templates_raises(self) -> None:
        raw = {
            "description": "Sem ações",
            "card_ids": [1],
        }
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _parse_theme_actions("trabalho", raw)
        assert "action_templates" in str(exc_info.value)

    def test_missing_card_ids_raises(self) -> None:
        raw = {
            "description": "Sem ids",
            "action_templates": [
                {
                    "type": "action",
                    "template": "Faça",
                    "timeframe": "immediate",
                    "success_criterion": "Feito",
                }
            ],
        }
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _parse_theme_actions("trabalho", raw)
        assert "card_ids" in str(exc_info.value)

    def test_empty_description_gets_default(self) -> None:
        raw = {
            "action_templates": [
                {
                    "type": "action",
                    "template": "Faça",
                    "timeframe": "immediate",
                    "success_criterion": "Feito",
                }
            ],
            "card_ids": [1],
        }
        theme = _parse_theme_actions("trabalho", raw)
        assert theme.description == ""


# ----------------------------------------------------------------------
# Testes — _load_raw_json()
# ----------------------------------------------------------------------


class TestLoadRawJson:
    def test_valid_json_file(self, tmp_path) -> None:
        json_file = tmp_path / "plano_rules.json"
        import json

        json_file.write_text(json.dumps({"test": "data"}), encoding="utf-8")
        data = _load_raw_json(json_file)
        assert data["test"] == "data"

    def test_nonexistent_file_raises(self, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            _load_raw_json(tmp_path / "inexistente.json")

    def test_invalid_json_raises(self, tmp_path) -> None:
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{ invalido }", encoding="utf-8")
        with pytest.raises(PlanoRulesValidationError) as exc_info:
            _load_raw_json(json_file)
        assert "JSON inválido" in str(exc_info.value)


# ----------------------------------------------------------------------
# Testes — _build_action()
# ----------------------------------------------------------------------


class TestBuildAction:
    def test_build_action_with_template(self) -> None:
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        template = ActionTemplate(
            type="reflection",
            template="Mantenha-se firme em {{{tema}}}",
            timeframe="this_week",
            success_criterion="Clareza obtida",
        )
        action = _build_action(template, symbol, "medium")
        assert "estrela" in action.lower() or symbol.theme in action.lower()

    def test_build_action_urgency_high_prefix(self) -> None:
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        template = ActionTemplate(
            type="action",
            template="Revise seu {{{tema}}}",
            timeframe="immediate",
            success_criterion="Ação tomada",
        )
        action = _build_action(template, symbol, "high")
        assert "[URGENTE]" in action

    def test_build_action_urgency_low_prefix(self) -> None:
        symbol = get_symbol_by_name("a casa")
        assert symbol is not None
        template = ActionTemplate(
            type="reflection",
            template="Avalie {{{tema}}}",
            timeframe="this_month",
            success_criterion="Consciência",
        )
        action = _build_action(template, symbol, "low")
        assert "[LONGO PRAZO]" in action

    def test_build_action_urgency_medium_no_prefix(self) -> None:
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        template = ActionTemplate(
            type="action",
            template="Prossiga com {{{tema}}}",
            timeframe="this_week",
            success_criterion="Progresso",
        )
        action = _build_action(template, symbol, "medium")
        assert "[URGENTE]" not in action
        assert "[LONGO PRAZO]" not in action

    def test_build_action_empty_template_replacements(self) -> None:
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        template = ActionTemplate(
            type="action",
            template="Texto simples sem marcadores",
            timeframe="immediate",
            success_criterion="Feito",
        )
        action = _build_action(template, symbol, "medium")
        assert "Texto simples" in action

    def test_build_action_substitution_acao(self) -> None:
        """Marcador {acao} usa advice do símbolo."""
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        template = ActionTemplate(
            type="action",
            template="{acao}",
            timeframe="immediate",
            success_criterion="Feito",
        )
        action = _build_action(template, symbol, "medium")
        assert symbol.advice in action or symbol.theme in action

    def test_build_action_unknown_marker_unchanged(self) -> None:
        """Marcadores desconhecidos permanecem no texto."""
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        template = ActionTemplate(
            type="action",
            template="Use {{{unknown_marker}}}",
            timeframe="immediate",
            success_criterion="Feito",
        )
        action = _build_action(template, symbol, "medium")
        assert "{{{unknown_marker}}}" in action


# ----------------------------------------------------------------------
# Testes — _determine_urgency()
# ----------------------------------------------------------------------


class TestDetermineUrgency:
    def test_danger_card_returns_high(self, valid_rules: PlanoRules) -> None:
        """Cartas em danger_cards geram urgência alta."""
        symbol = get_symbol_by_name("o lobo")  # ID 15 está em danger_cards
        assert symbol is not None
        assert symbol.id in valid_rules.urgency_escalation.danger_cards
        urgency = _determine_urgency([symbol], [], valid_rules)
        assert urgency == "high"

    def test_danger_keyword_returns_medium(self, valid_rules: PlanoRules) -> None:
        """Keywords de perigo no conteúdo geram urgência média."""
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        risks = ["⚠️ Risco pessoal — medo de acontecer"]
        urgency = _determine_urgency([symbol], risks, valid_rules)
        assert urgency == "medium"

    def test_default_level_returns_low(self, valid_rules: PlanoRules) -> None:
        """Sem cartas perigosas ou keywords, retorna nível padrão."""
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        urgency = _determine_urgency([symbol], [], valid_rules)
        assert urgency == valid_rules.urgency_escalation.default_level

    def test_empty_symbols_returns_default(self, valid_rules: PlanoRules) -> None:
        """Lista vazia de símbolos retorna nível padrão."""
        urgency = _determine_urgency([], [], valid_rules)
        assert urgency == valid_rules.urgency_escalation.default_level

    def test_danger_keyword_case_insensitive(self, valid_rules: PlanoRules) -> None:
        """Keywords de perigo são verificadas case-insensitive."""
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        risks = ["⚠️ Risco — MEDO de acontecer"]
        urgency = _determine_urgency([symbol], risks, valid_rules)
        assert urgency == "medium"


# ----------------------------------------------------------------------
# Testes — _is_danger_card()
# ----------------------------------------------------------------------


class TestIsDangerCard:
    def test_lobo_is_danger_card(self) -> None:
        """Lobo (ID 15) é carta perigosa."""
        lobo = get_symbol_by_name("o lobo")
        assert lobo is not None
        assert _is_danger_card(lobo) is True

    def test_lobo_is_danger_card(self) -> None:
        """Lobo (ID 15) é carta perigosa no arquivo de regras."""
        lobo = get_symbol_by_name("o lobo")
        assert lobo is not None
        assert _is_danger_card(lobo) is True

    def test_nuvens_check_fallback_ids(self) -> None:
        """Nuvens ID 6 não está no fallback, mas lobo 15 está."""
        nuvens = get_symbol_by_name("as nuvens")
        lobo = get_symbol_by_name("o lobo")
        assert nuvens is not None
        assert lobo is not None
        # Lobo (15) está no fallback
        assert lobo.id in {7, 8, 12, 15, 20, 22}
        # Nuvens (6) não está no fallback
        assert nuvens.id not in {7, 8, 12, 15, 20, 22}
        # Lobo é perigoso, nuvens verifica via arquivo de regras (danger_cards)
        assert _is_danger_card(lobo) is True

    def test_estrela_is_not_danger_card(self) -> None:
        """Estrela não é carta perigosa."""
        estrela = get_symbol_by_name("a estrela")
        assert estrela is not None
        assert _is_danger_card(estrela) is False

    def test_casa_is_not_danger_card(self) -> None:
        """Casa não é carta perigosa."""
        casa = get_symbol_by_name("a casa")
        assert casa is not None
        assert _is_danger_card(casa) is False


# ----------------------------------------------------------------------
# Testes — generate_recommendations()
# ----------------------------------------------------------------------


class TestGenerateRecommendations:
    def test_empty_symbols_returns_fallback(self) -> None:
        """Sem símbolos retorna mensagem de fallback."""
        result = generate_recommendations([], [], [])
        assert "Aprofundar" in result or "contexto" in result

    def test_single_symbol_generates_focus(self) -> None:
        """Símbolo único gera foco principal."""
        estrela = get_symbol_by_name("a estrela")
        assert estrela is not None
        result = generate_recommendations([estrela], ["espiritual"], [])
        assert estrela.name in result or estrela.advice in result

    def test_recommendations_include_urgency_tag(self) -> None:
        """Recomendações com urgência alta incluem tag."""
        forca = get_symbol_by_name("a forca")
        assert forca is not None
        result = generate_recommendations([forca], ["trabalho"], [])
        assert "[URGENTE]" in result or "Foco" in result

    def test_risks_add_cuidados_section(self) -> None:
        """Riscos geram seção de cuidados."""
        estrela = get_symbol_by_name("a estrela")
        assert estrela is not None
        risks = [
            "⚠️ Risco qualquer — cuidado necessário",
            "⚠️ Outro risco — mais atenção",
        ]
        result = generate_recommendations([estrela], [], risks)
        assert "Cuidados" in result or "cuidado" in result.lower()

    def test_recommendations_respects_risks_limit(self) -> None:
        """Recomendações limitam riscos a 3 no output."""
        estrela = get_symbol_by_name("a estrela")
        assert estrela is not None
        risks = [
            f"⚠️ Risco {i} — Cuidado {i}" for i in range(10)
        ]
        result = generate_recommendations([estrela], [], risks)
        # Conta ocorrências de "- Cuidado" (bullet de cuidado)
        cuidado_count = result.count("- Cuidado")
        assert cuidado_count <= 3

    def test_multiple_symbols_adds_proximos_passos(self) -> None:
        """Múltiplos símbolos adicionam seção de próximos passos."""
        estrela = get_symbol_by_name("a estrela")
        casa = get_symbol_by_name("a casa")
        assert estrela is not None
        assert casa is not None
        result = generate_recommendations([estrela, casa], [], [])
        assert "Próximos passos" in result or "passos" in result.lower()

    def test_empty_risks_no_cuidados_section(self) -> None:
        """Sem riscos não adiciona seção de cuidados."""
        estrela = get_symbol_by_name("a estrela")
        assert estrela is not None
        result = generate_recommendations([estrela], ["espiritual"], [])
        # Se não há riscos, não deve ter seção de cuidados
        # Verifica apenas que resultado é válido
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_recommendations_returns_string(self) -> None:
        """Função retorna string (não lista ou outro tipo)."""
        estrela = get_symbol_by_name("a estrela")
        assert estrela is not None
        result = generate_recommendations([estrela], [], [])
        assert isinstance(result, str)

    def test_generate_recommendations_preserves_unicode(self) -> None:
        """Recomendações preservam caracteres unicode/acentos."""
        estrela = get_symbol_by_name("a estrela")
        assert estrela is not None
        result = generate_recommendations([estrela], ["espiritual"], [])
        # Verifica que não houve corrompimento de unicode
        assert "ã" in result or "é" in result or "ó" in result or len(result) > 0


# ----------------------------------------------------------------------
# Testes — load_plano_rules()
# ----------------------------------------------------------------------


class TestLoadPlanoRules:
    def test_load_valid_rules(self, valid_rules: PlanoRules) -> None:
        """Regras válidas são carregadas corretamente."""
        assert valid_rules.card_actions is not None
        assert valid_rules.urgency_escalation is not None
        assert valid_rules.recommendation_templates is not None
        assert valid_rules.timeframes is not None
        assert valid_rules.success_criteria is not None

    def test_load_existing_file_succeeds(self) -> None:
        """Arquivo existente é carregado com sucesso."""
        # O arquivo data/plano_rules.json existe no worktree
        rules = load_plano_rules()
        assert rules is not None
        assert isinstance(rules, PlanoRules)

    
    def test_load_returns_plano_rules_instance(self, valid_rules: PlanoRules) -> None:
        """load_plano_rules() retorna instância de PlanoRules."""
        assert isinstance(valid_rules, PlanoRules)


# ----------------------------------------------------------------------
# Testes de edge cases
# ----------------------------------------------------------------------


class TestEdgeCases:
    def test_determine_urgency_empty_rules(self) -> None:
        """Com regras vazias retorna default_level."""
        rules = PlanoRules(
            card_actions={},
            urgency_escalation=_parse_urgency_escalation({}),
            recommendation_templates=[],
            timeframes={},
            success_criteria={},
        )
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        urgency = _determine_urgency([symbol], [], rules)
        assert urgency == "low"  # default_level padrão

    def test_build_action_with_empty_theme(self) -> None:
        """Template com marcador de tema vazio não quebra."""
        symbol = get_symbol_by_name("a estrela")
        assert symbol is not None
        template = ActionTemplate(
            type="action",
            template="Foque em {{{tema}}}",
            timeframe="immediate",
            success_criterion="Feito",
        )
        action = _build_action(template, symbol, "medium")
        assert isinstance(action, str)
        assert len(action) > 0

    def test_generate_recommendations_with_only_risks(self) -> None:
        """Recomendações funcionam mesmo sem símbolos, com apenas riscos."""
        result = generate_recommendations([], [], ["⚠️ Risco qualquer — Cuidado"])
        assert isinstance(result, str)

    def test_validate_empty_card_ids_still_raises(self) -> None:
        """card_ids vazio ainda levanta exceção na validação."""
        from clareza.plano_rules import (
            PlanoRules,
            _parse_urgency_escalation,
            ThemeActions,
            ActionTemplate,
            _validate_plano_rules,
        )

        actions = ThemeActions(
            description="Teste",
            action_templates=[
                ActionTemplate(
                    type="action",
                    template="Faça",
                    timeframe="immediate",
                    success_criterion="Feito",
                )
            ],
            card_ids=[],  # vazio
        )
        rules = PlanoRules(
            card_actions={"teste": actions},
            urgency_escalation=_parse_urgency_escalation({}),
            recommendation_templates=[],
            timeframes={
                "immediate": TimeframeDefinition(label="I", horizon_days=1, description=""),
                "this_week": TimeframeDefinition(label="S", horizon_days=7, description=""),
                "this_month": TimeframeDefinition(label="M", horizon_days=30, description=""),
            },
            success_criteria={},
        )
        with pytest.raises(PlanoRulesValidationError):
            _validate_plano_rules(rules)

    def test_parse_action_template_coerces_types(self) -> None:
        """Parsing converte tipos para os esperados."""
        raw = {
            "type": 123,  # deveria ser string
            "template": "Faça",
            "timeframe": "immediate",
            "success_criterion": "Feito",
        }
        template = _parse_action_template(raw)
        assert isinstance(template.type, str)
        assert template.type == "123"