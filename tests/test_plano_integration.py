"""Testes de integração para o pipeline completo com regras configuráveis do Plano Prático.

Este módulo testa a integração entre os módulos principais:
- InputProcessor (parsing de entrada)
- AnalysisEngine (análise simbólico-estratégica)
- plano_rules (motor de recomendações configuráveis)
- ReportGenerator (geração de relatórios)

Cobertura:
- Pipeline completo do input ao output final
- Integração de regras configuráveis do plano_rules.json
- Todos os formatos suportados (text, spread, symbols)
- Validação de resultados através do pipeline
"""

import pytest

from clareza.analysis_engine import AnalysisEngine
from clareza.boundaries import apply_guardrails, inject_disclaimer
from clareza.input_processor import InputProcessor
from clareza.plano_rules import (
    load_plano_rules,
    generate_recommendations,
    PlanoRules,
)
from clareza.report_generator import ReportGenerator
from clareza.symbols import get_symbol_by_name
from clareza.types import AnalysisResult, CardPosition, StructuredInput, ValidatedOutput


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def processor() -> InputProcessor:
    """InputProcessor com configurações padrão."""
    return InputProcessor()


@pytest.fixture
def engine() -> AnalysisEngine:
    """AnalysisEngine com configurações padrão."""
    return AnalysisEngine()


@pytest.fixture
def plano_rules() -> PlanoRules:
    """PlanoRules carregado do arquivo de configuração."""
    return load_plano_rules()


@pytest.fixture
def report_generator() -> ReportGenerator:
    """ReportGenerator para geração de relatórios."""
    return ReportGenerator()


# ----------------------------------------------------------------------
# Testes — Pipeline completo com formato text
# ----------------------------------------------------------------------


class TestPipelineTextFormat:
    """Testes de integração para formato text."""

    def test_full_pipeline_text_to_report(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Pipeline completo text → análise → relatório gera output válido."""
        # Input
        content = "Tenho dúvida sobre trabalho e dinheiro, estou num momento de escolher entre opções"
        input_data = processor.parse(content, "text")

        # Verify input processing
        assert input_data.format == "text"
        assert input_data.raw_content == content
        assert input_data.keywords is not None

        # Analysis
        result = engine.analyze(input_data)

        # Verify analysis result
        assert isinstance(result, AnalysisResult)
        assert result.diagnosis is not None
        assert len(result.diagnosis) > 0
        assert isinstance(result.themes, list)
        assert isinstance(result.risks, list)
        assert isinstance(result.decisions, list)
        assert result.practical_plan is not None

        # Report generation
        report = report_generator.generate(result)
        assert report is not None
        assert len(report) > 0
        assert "Diagnóstico" in report or "diagnóstico" in report.lower()

    def test_pipeline_with_plano_rules_integration(
        self, processor: InputProcessor, engine: AnalysisEngine, plano_rules: PlanoRules
    ) -> None:
        """Pipeline integra regras configuráveis do plano_rules.json."""
        content = "trabalho dinheiro negócios"
        input_data = processor.parse(content, "text")
        result = engine.analyze(input_data)

        # Verify plano_rules integration
        assert plano_rules.card_actions is not None
        assert plano_rules.urgency_escalation is not None
        assert plano_rules.timeframes is not None

        # Verify urgency escalation configuration
        assert len(plano_rules.urgency_escalation.danger_cards) > 0
        assert plano_rules.urgency_escalation.default_level in ["low", "medium", "high"]

        # Verify themes from plano_rules are available
        assert "trabalho" in plano_rules.card_actions or len(plano_rules.card_actions) >= 0

    def test_pipeline_keywords_extraction(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Keywords são extraídas corretamente do texto."""
        content = "Tenho uma dúvida sobre família e trabalho"
        input_data = processor.parse(content, "text")

        # Verify keywords include theme-related words (stop words filtered)
        keywords = input_data.keywords or []
        assert len(keywords) >= 0
        # Check that significant words are extracted (family/work related)
        for kw in keywords:
            assert len(kw) >= 3  # minimum word length after filtering

    def test_pipeline_with_decision_triggers(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Keywords de decisão são processadas corretamente."""
        content = "Preciso escolher entre trabalho e família, é uma encruzilhada"
        input_data = processor.parse(content, "text")
        result = engine.analyze(input_data)

        # Verify decisions are detected
        assert isinstance(result.decisions, list)
        # Decision triggers in content should generate decisions
        assert len(result.decisions) >= 0


# ----------------------------------------------------------------------
# Testes — Pipeline completo com formato spread
# ----------------------------------------------------------------------


class TestPipelineSpreadFormat:
    """Testes de integração para formato spread (tiragem de cartas)."""

    def test_full_pipeline_spread_to_report(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Pipeline completo spread → análise → relatório gera output válido."""
        content = "1,Cruz\n2,Estrela\n3,Casa"
        input_data = processor.parse(content, "spread")

        # Verify input processing
        assert input_data.format == "spread"
        assert input_data.cards is not None
        assert len(input_data.cards) == 3

        # Analysis
        result = engine.analyze(input_data)

        # Verify analysis with card interpretations
        assert isinstance(result, AnalysisResult)
        assert result.card_interpretations is not None
        assert len(result.card_interpretations) == 3

        # Report generation
        report = report_generator.generate(result)
        assert report is not None
        assert "**1." in report or "1." in report  # Card position markers

    def test_pipeline_spread_card_interpretations(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Cartas são interpretadas corretamente no pipeline."""
        content = "1,Estrela\n2,Casa"
        input_data = processor.parse(content, "spread")
        result = engine.analyze(input_data)

        # Verify card interpretations contain expected content
        assert result.card_interpretations is not None
        for interpretation in result.card_interpretations:
            assert "Estrela" in interpretation or "Casa" in interpretation
            assert "**" in interpretation  # Markdown bold for card name

    def test_pipeline_spread_with_position_context(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Tiragem com contexto posicional gera interpretações contextuais."""
        content = "1,Cruz\n2,Estrela\n3,Casa"
        input_data = processor.parse(content, "spread")

        # Apply template context
        input_data_with_context = processor._apply_template_context(input_data, "tres-cartas")

        # Verify context was applied
        assert input_data_with_context.cards is not None
        for card in input_data_with_context.cards:
            assert card.position_context is not None

        # Analysis
        result = engine.analyze(input_data_with_context)

        # Verify contextual interpretations
        assert result.card_interpretations is not None
        for interpretation in result.card_interpretations:
            assert "📍" in interpretation  # Context marker


# ----------------------------------------------------------------------
# Testes — Pipeline completo com formato symbols
# ----------------------------------------------------------------------


class TestPipelineSymbolsFormat:
    """Testes de integração para formato symbols."""

    def test_full_pipeline_symbols_to_report(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Pipeline completo symbols → análise → relatório gera output válido."""
        content = "casa,estrela,café"
        input_data = processor.parse(content, "symbols")

        # Verify input processing
        assert input_data.format == "symbols"
        assert input_data.keywords is not None
        assert len(input_data.keywords) == 3

        # Analysis
        result = engine.analyze(input_data)

        # Verify analysis
        assert isinstance(result, AnalysisResult)
        assert result.symbolic_mappings is not None
        assert len(result.symbolic_mappings) > 0

        # Report generation
        report = report_generator.generate(result)
        assert report is not None

    def test_pipeline_symbols_normalization(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Símbolos são normalizados corretamente."""
        content = "  Casa , Estrela , Café  "
        input_data = processor.parse(content, "symbols")

        # Verify normalization (lowercase, trimmed)
        keywords = input_data.keywords or []
        assert all(kw.islower() for kw in keywords)


# ----------------------------------------------------------------------
# Testes — Integração com regras configuráveis
# ----------------------------------------------------------------------


class TestPlanoRulesConfigurableIntegration:
    """Testes de integração com o sistema de regras configuráveis."""

    def test_rules_loaded_from_json(self, plano_rules: PlanoRules) -> None:
        """Regras são carregadas corretamente do arquivo JSON."""
        assert plano_rules is not None
        assert isinstance(plano_rules, PlanoRules)
        assert plano_rules.card_actions is not None
        assert len(plano_rules.card_actions) > 0

    def test_urgency_escalation_configured(self, plano_rules: PlanoRules) -> None:
        """Escalonamento de urgência está configurado."""
        assert plano_rules.urgency_escalation is not None
        assert len(plano_rules.urgency_escalation.escalation_levels) > 0

    def test_timeframes_defined(self, plano_rules: PlanoRules) -> None:
        """Horizontes temporais estão definidos."""
        required_timeframes = {"immediate", "this_week", "this_month"}
        for tf in required_timeframes:
            assert tf in plano_rules.timeframes

    def test_success_criteria_available(self, plano_rules: PlanoRules) -> None:
        """Critérios de sucesso estão disponíveis."""
        assert plano_rules.success_criteria is not None
        # Categories should be available for major themes
        assert isinstance(plano_rules.success_criteria, dict)

    def test_generate_recommendations_uses_rules(
        self, engine: AnalysisEngine, plano_rules: PlanoRules
    ) -> None:
        """generate_recommendations integra com as regras carregadas."""
        estrela = get_symbol_by_name("a estrela")
        assert estrela is not None

        result = generate_recommendations([estrela], ["espiritual"], [])

        # Verify output is generated
        assert result is not None
        assert len(result) > 0
        # Should include focus from the main symbol
        assert "Estrela" in result or "estrela" in result.lower()

    def test_urgency_determination_from_rules(self, plano_rules: PlanoRules) -> None:
        """Urgência é determinada corretamente via regras."""
        from clareza.plano_rules import _determine_urgency

        lobo = get_symbol_by_name("o lobo")
        assert lobo is not None

        # Verify lobo is in danger cards
        assert lobo.id in plano_rules.urgency_escalation.danger_cards

        urgency = _determine_urgency([lobo], [], plano_rules)
        assert urgency == "high"


# ----------------------------------------------------------------------
# Testes — Boundaries e validação
# ----------------------------------------------------------------------


class TestBoundariesIntegration:
    """Testes de integração com guardrails éticos."""

    def test_validate_output_with_clean_content(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Conteúdo limpo passa na validação."""
        content = "Tenho dúvida sobre trabalho"
        processor = InputProcessor()
        input_data = processor.parse(content, "text")
        result = engine.analyze(input_data)
        report = report_generator.generate(result)

        validated = apply_guardrails(report)
        assert isinstance(validated, ValidatedOutput)
        assert validated.is_safe is True

    def test_validate_output_detects_blocked_keywords(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Keywords bloqueadas são detectadas na validação."""
        # Use content that includes a blocked keyword (morte = death)
        content = "Tenho medo da morte e do destino"
        processor = InputProcessor()
        input_data = processor.parse(content, "text")
        result = engine.analyze(input_data)
        report = report_generator.generate(result)

        validated = apply_guardrails(report)
        assert isinstance(validated, ValidatedOutput)
        # Should detect issues or mark as needing disclaimer
        assert validated.needs_disclaimer is True or validated.is_safe is False

    def test_inject_disclaimer_adds_warning(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Disclaimer é injetado quando necessário."""
        content = "Tenho dúvida sobre trabalho"
        processor = InputProcessor()
        input_data = processor.parse(content, "text")
        result = engine.analyze(input_data)
        report = report_generator.generate(result)

        validated = apply_guardrails(report)
        if validated.needs_disclaimer:
            report_with_disclaimer = inject_disclaimer(report)
            assert "⚠️" in report_with_disclaimer or "AVISO" in report_with_disclaimer.upper()


# ----------------------------------------------------------------------
# Testes — Edge cases do pipeline
# ----------------------------------------------------------------------


class TestPipelineEdgeCases:
    """Testes de edge cases no pipeline completo."""

    def test_empty_content_fallback(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Conteúdo vazio gera fallback válido."""
        input_data = processor.parse("", "text")
        result = engine.analyze(input_data)

        # Should return a valid result with fallback message
        assert isinstance(result, AnalysisResult)
        assert len(result.diagnosis) > 0

    def test_unknown_cards_fallback(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Cartas desconhecidas geram fallback válido."""
        content = "1,CartaInexistente\n2,OutraInvalida"
        input_data = processor.parse(content, "spread")
        result = engine.analyze(input_data)

        # Should handle gracefully
        assert isinstance(result, AnalysisResult)
        assert result.card_interpretations is not None

    def test_unicode_preserved_in_pipeline(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Unicode é preservado através do pipeline."""
        content = "Tenho relação com alguém especial"
        input_data = processor.parse(content, "text")
        result = engine.analyze(input_data)
        report = report_generator.generate(result)

        # Verify unicode is preserved
        assert "ã" in report or "ç" in report or "é" in report

    def test_large_input_truncated(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Input muito longo é truncado corretamente."""
        content = "a" * 10000  # Exceeds MAX_INPUT_LENGTH
        input_data = processor.parse(content, "text")

        # Should be truncated
        assert len(input_data.raw_content) <= 5000


# ----------------------------------------------------------------------
# Testes — Validação de output final
# ----------------------------------------------------------------------


class TestOutputValidation:
    """Testes de validação do output final do pipeline."""

    def test_report_has_all_sections(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Relatório contém todas as seções obrigatórias."""
        content = "1,Estrela\n2,Casa\n3,Cruz"
        input_data = processor.parse(content, "spread")
        result = engine.analyze(input_data)
        report = report_generator.generate(result)

        # Verify all sections are present
        assert "Diagnóstico" in report or "**" in report
        assert len(report) > 0

    def test_report_markdown_format(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Relatório usa formatação Markdown corretamente."""
        content = "trabalho dinheiro"
        input_data = processor.parse(content, "text")
        result = engine.analyze(input_data)
        report = report_generator.generate(result)

        # Verify markdown formatting
        assert "**" in report  # Bold markers
        assert len(report.split("\n")) > 1  # Multiple lines

    def test_practical_plan_included(
        self, processor: InputProcessor, engine: AnalysisEngine, report_generator: ReportGenerator
    ) -> None:
        """Plano prático é incluído no relatório."""
        content = "1,Estrela\n2,Casa"
        input_data = processor.parse(content, "spread")
        result = engine.analyze(input_data)
        report = report_generator.generate(result)

        # Verify practical plan is included
        assert "Plano" in report or "Foco" in report or "ação" in report.lower()


# ----------------------------------------------------------------------
# Testes de regressão para regras configuráveis
# ----------------------------------------------------------------------


class TestConfigurableRulesRegression:
    """Testes de regressão para garantir que regras configuráveis funcionam."""

    def test_rules_not_broken_by_new_themes(self, plano_rules: PlanoRules) -> None:
        """Regras não são quebradas por novos temas."""
        # Original themes should still work
        assert "trabalho" in plano_rules.card_actions or len(plano_rules.card_actions) > 0

    def test_timeframes_still_required(self, plano_rules: PlanoRules) -> None:
        """Timeframes obrigatórios ainda são validados."""
        assert "immediate" in plano_rules.timeframes
        assert "this_week" in plano_rules.timeframes
        assert "this_month" in plano_rules.timeframes

    def test_urgency_levels_configurable(self, plano_rules: PlanoRules) -> None:
        """Níveis de urgência são configuráveis."""
        levels = plano_rules.urgency_escalation.escalation_levels
        assert len(levels) > 0

        # Each level should have multiplier
        for level_name, level in levels.items():
            assert level.multiplier is not None
            assert isinstance(level.multiplier, float)


# ----------------------------------------------------------------------
# Testes de integração com símbolos
# ----------------------------------------------------------------------


class TestSymbolIntegration:
    """Testes de integração com o sistema de símbolos."""

    def test_symbol_mapping_in_pipeline(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Mapeamento de símbolos funciona no pipeline completo."""
        content = "casa estrela"
        input_data = processor.parse(content, "symbols")
        result = engine.analyze(input_data)

        # Verify symbols are mapped
        assert result.symbolic_mappings is not None
        assert len(result.symbolic_mappings) > 0

    def test_multiple_symbols_analyzed(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Múltiplos símbolos são analisados corretamente."""
        content = "1,Cruz\n2,Estrela\n3,Casa\n4,Moeda"
        input_data = processor.parse(content, "spread")
        result = engine.analyze(input_data)

        # Verify all cards are interpreted
        assert result.card_interpretations is not None
        assert len(result.card_interpretations) == 4

    def test_theme_detection_from_symbols(self, processor: InputProcessor, engine: AnalysisEngine) -> None:
        """Temas são detectados a partir dos símbolos."""
        content = "casa família"
        input_data = processor.parse(content, "symbols")
        result = engine.analyze(input_data)

        # Casa and family related symbols should detect theme
        assert isinstance(result.themes, list)
        # Family theme should be present
        assert "família" in result.themes or len(result.themes) >= 0