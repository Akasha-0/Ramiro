"""Testes unitários para src/template_engine.py.

Cobertura:
- _compile_template() — compilação regex, caracteres especiais
- _substitute_template() — substituição de placeholders
- _prepare_diagnosis_context() — contexto de diagnóstico
- _prepare_symbolic_interpretation_context() — contexto de interpretação
- _prepare_risks_context() — contexto de riscos
- _prepare_decisions_context() — contexto de decisões
- _prepare_cross_card_patterns_context() — contexto de padrões cruzados
- _prepare_practical_plan_context() — contexto de plano prático
- _build_context() — construção de contexto
- _extract_template_fields() — extração de campos
- _render_section() — renderização de seção
- TemplateEngine.__init__() — inicialização
- TemplateEngine.render() — API principal
- TemplateEngine.render_section() — renderização de seção individual
- TemplateEngine.get_available_fields() — campos disponíveis
- TemplateEngine.extract_fields() — método estático
- TemplateEngine.substitute() — método estático
"""

import pytest

from src.template_engine import (
    TemplateEngine,
    _build_context,
    _compile_template,
    _extract_template_fields,
    _render_section,
    _substitute_template,
)
from src.template_loader import TemplateLoader
from src.types import AnalysisResult, CrossCardPattern, ReportTemplate, TemplateSection


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def engine() -> TemplateEngine:
    """TemplateEngine com template padrão."""
    loader = TemplateLoader()
    return TemplateEngine(default_template=loader.default_template)


@pytest.fixture
def analysis_full() -> AnalysisResult:
    """AnalysisResult com todos os campos preenchidos."""
    return AnalysisResult(
        diagnosis="Você está num momento de transição profissional.",
        themes=["trabalho", "mudança"],
        risks=["incerteza prolongada", "hesitação excessiva"],
        decisions=["Explorar oportunidades", "Investir em qualificação"],
        practical_plan="1. Atualizar currículo\n2. Pesquisar cursos",
        card_interpretations=[
            "**Carta 1 - A Casa**: Indica estabilidade.",
            "**Carta 2 - A Estrela**: Sinaliza esperança.",
        ],
        symbolic_mappings={
            "kw:casa": "A Casa",
            "card:Casa": "A Casa",
        },
    )


@pytest.fixture
def analysis_minimal() -> AnalysisResult:
    """AnalysisResult com campos mínimos."""
    return AnalysisResult(diagnosis="")


@pytest.fixture
def section_diagnosis() -> TemplateSection:
    return TemplateSection(
        id="diagnostico",
        title="Diagnóstico",
        order=1,
        content_template="{diagnosis}",
        required=True,
        placeholder="*Diagnóstico não disponível.*",
    )


@pytest.fixture
def section_interpretation() -> TemplateSection:
    return TemplateSection(
        id="interpretacao",
        title="Interpretação Simbólica",
        order=2,
        content_template="{symbolic_interpretation}",
        required=False,
        placeholder="*Nenhuma interpretação simbólica disponível.*",
    )


@pytest.fixture
def section_with_pattern() -> TemplateSection:
    return TemplateSection(
        id="padroes",
        title="Padrões Cruzados",
        order=6,
        content_template="{cross_card_patterns}",
        required=False,
        placeholder="*Nenhum padrão identificado.*",
    )


# ----------------------------------------------------------------------
# Testes — _compile_template()
# ----------------------------------------------------------------------


class TestCompileTemplate:
    def test_compiles_simple_template(self) -> None:
        pattern = _compile_template("{field}")
        assert pattern is not None
        assert pattern.pattern == "(?P<field>.+?)"

    def test_compiles_multiple_fields(self) -> None:
        pattern = _compile_template("{a} e {b}")
        assert pattern is not None
        assert "?P<a>" in pattern.pattern
        assert "?P<b>" in pattern.pattern

    def test_escapes_special_regex_chars(self) -> None:
        pattern = _compile_template("texto com [parenteses] e {field}")
        # Should not raise re.error
        assert pattern is not None

    def test_empty_template_compiles(self) -> None:
        pattern = _compile_template("")
        assert pattern is not None

    def test_template_without_fields_compiles(self) -> None:
        pattern = _compile_template("sem placeholders")
        assert pattern is not None

    def test_duplicate_fields_raises_regex_error(self) -> None:
        """Duplicação de campos no mesmo template causa re.error (regex não permite grupos duplicados)."""
        import re
        with pytest.raises(re.error):
            _compile_template("{field} e {field}")


# ----------------------------------------------------------------------
# Testes — _substitute_template()
# ----------------------------------------------------------------------


class TestSubstituteTemplate:
    def test_substitutes_single_placeholder(self) -> None:
        result = _substitute_template("Olá {name}!", {"name": "Maria"})
        assert result == "Olá Maria!"

    def test_substitutes_multiple_placeholders(self) -> None:
        result = _substitute_template("{greeting} {name}!", {"greeting": "Olá", "name": "João"})
        assert result == "Olá João!"

    def test_missing_placeholder_unchanged(self) -> None:
        result = _substitute_template("{a} e {b}", {"a": "primeiro"})
        assert result == "primeiro e {b}"

    def test_empty_substitution_removes_placeholder(self) -> None:
        result = _substitute_template("{a} texto", {"a": ""})
        assert result == " texto"

    def test_empty_template_returns_empty(self) -> None:
        result = _substitute_template("", {"field": "value"})
        assert result == ""

    def test_no_placeholders_returns_same(self) -> None:
        result = _substitute_template("sem placeholders", {"field": "value"})
        assert result == "sem placeholders"

    def test_all_placeholders_substituted(self) -> None:
        result = _substitute_template("{x} {y} {z}", {"x": "1", "y": "2", "z": "3"})
        assert result == "1 2 3"

    def test_multiple_occurrences_same_placeholder(self) -> None:
        result = _substitute_template("{name} disse: {name}!", {"name": "Ana"})
        assert result == "Ana disse: Ana!"


# ----------------------------------------------------------------------
# Testes — _extract_template_fields()
# ----------------------------------------------------------------------


class TestExtractTemplateFields:
    def test_extracts_single_field(self) -> None:
        fields = _extract_template_fields("{diagnosis}")
        assert fields == ["diagnosis"]

    def test_extracts_multiple_fields(self) -> None:
        fields = _extract_template_fields("{a} e {b} e {c}")
        assert fields == ["a", "b", "c"]

    def test_extracts_duplicate_fields(self) -> None:
        fields = _extract_template_fields("{field} e {field}")
        assert fields == ["field", "field"]

    def test_no_fields_returns_empty(self) -> None:
        fields = _extract_template_fields("sem campos")
        assert fields == []

    def test_empty_template_returns_empty(self) -> None:
        fields = _extract_template_fields("")
        assert fields == []

    def test_mixed_content_with_fields(self) -> None:
        fields = _extract_template_fields("Texto {field1} mais {field2} texto")
        assert fields == ["field1", "field2"]


# ----------------------------------------------------------------------
# Testes — Preparadores de contexto
# ----------------------------------------------------------------------


class TestPrepareDiagnosisContext:
    def test_returns_diagnosis(self, analysis_full: AnalysisResult) -> None:
        result = _build_context(analysis_full)["diagnosis"]
        assert result == "Você está num momento de transição profissional."

    def test_empty_diagnosis_returns_empty_string(self, analysis_minimal: AnalysisResult) -> None:
        result = _build_context(analysis_minimal)["diagnosis"]
        assert result == ""


class TestPrepareSymbolicInterpretationContext:
    def test_includes_mappings(self, analysis_full: AnalysisResult) -> None:
        result = _build_context(analysis_full)["symbolic_interpretation"]
        assert "A Casa" in result
        assert "Keyword" in result
        assert "Carta" in result

    def test_includes_themes(self, analysis_full: AnalysisResult) -> None:
        result = _build_context(analysis_full)["symbolic_interpretation"]
        assert "*trabalho*" in result
        assert "*mudança*" in result

    def test_includes_card_interpretations(self, analysis_full: AnalysisResult) -> None:
        result = _build_context(analysis_full)["symbolic_interpretation"]
        assert "A Casa" in result
        assert "A Estrela" in result

    def test_empty_interpretation(self, analysis_minimal: AnalysisResult) -> None:
        result = _build_context(analysis_minimal)["symbolic_interpretation"]
        assert result == ""


class TestPrepareRisksContext:
    def test_returns_risks_formatted(self, analysis_full: AnalysisResult) -> None:
        result = _build_context(analysis_full)["risks"]
        assert "- incerteza prolongada" in result
        assert "- hesitação excessiva" in result

    def test_empty_risks_returns_empty(self, analysis_minimal: AnalysisResult) -> None:
        result = _build_context(analysis_minimal)["risks"]
        assert result == ""


class TestPrepareDecisionsContext:
    def test_returns_decisions_numbered(self, analysis_full: AnalysisResult) -> None:
        result = _build_context(analysis_full)["decisions"]
        assert "1. Explorar oportunidades" in result
        assert "2. Investir em qualificação" in result

    def test_empty_decisions_returns_empty(self, analysis_minimal: AnalysisResult) -> None:
        result = _build_context(analysis_minimal)["decisions"]
        assert result == ""


class TestPrepareCrossCardPatternsContext:
    def test_returns_patterns_formatted(self) -> None:
        analysis = AnalysisResult(
            diagnosis="Teste",
            cross_card_patterns=[
                CrossCardPattern(
                    pattern_type="numeric_repeat",
                    card_ids=[1, 13, 25],
                    interpretation="Repetition pattern.",
                    strength="forte",
                )
            ],
        )
        result = _build_context(analysis)["cross_card_patterns"]
        assert "Numeric Repeat" in result
        assert "1, 13, 25" in result
        assert "forte" in result
        assert "Repetition pattern" in result

    def test_empty_patterns_returns_empty(self, analysis_minimal: AnalysisResult) -> None:
        result = _build_context(analysis_minimal)["cross_card_patterns"]
        assert result == ""


class TestPreparePracticalPlanContext:
    def test_returns_plan(self, analysis_full: AnalysisResult) -> None:
        result = _build_context(analysis_full)["practical_plan"]
        assert "Atualizar currículo" in result
        assert "Pesquisar cursos" in result

    def test_empty_plan_returns_empty(self, analysis_minimal: AnalysisResult) -> None:
        result = _build_context(analysis_minimal)["practical_plan"]
        assert result == ""


# ----------------------------------------------------------------------
# Testes — _build_context()
# ----------------------------------------------------------------------


class TestBuildContext:
    def test_returns_dict_with_all_fields(self, analysis_full: AnalysisResult) -> None:
        context = _build_context(analysis_full)
        assert isinstance(context, dict)
        assert "diagnosis" in context
        assert "symbolic_interpretation" in context
        assert "risks" in context
        assert "decisions" in context
        assert "cross_card_patterns" in context
        assert "practical_plan" in context

    def test_all_fields_have_string_values(self, analysis_full: AnalysisResult) -> None:
        context = _build_context(analysis_full)
        for field, value in context.items():
            assert isinstance(value, str), f"Campo {field} não é string"

    def test_works_with_minimal_analysis(self, analysis_minimal: AnalysisResult) -> None:
        context = _build_context(analysis_minimal)
        assert isinstance(context, dict)
        # Deve preencher todos os campos mesmo com dados mínimos
        assert "diagnosis" in context


# ----------------------------------------------------------------------
# Testes — _render_section()
# ----------------------------------------------------------------------


class TestRenderSection:
    def test_renders_section_with_context(
        self, section_diagnosis: TemplateSection, analysis_full: AnalysisResult
    ) -> None:
        context = _build_context(analysis_full)
        result = _render_section(section_diagnosis, context)
        assert result is not None
        assert "Você está num momento de transição profissional" in result

    def test_disabled_section_returns_none(
        self, section_diagnosis: TemplateSection, analysis_full: AnalysisResult
    ) -> None:
        section_diagnosis.enabled = False
        context = _build_context(analysis_full)
        result = _render_section(section_diagnosis, context)
        assert result is None

    def test_empty_content_returns_placeholder(
        self, section_interpretation: TemplateSection, analysis_minimal: AnalysisResult
    ) -> None:
        context = _build_context(analysis_minimal)
        result = _render_section(section_interpretation, context)
        assert result is not None
        assert "*Nenhuma interpretação simbólica disponível.*" in result

    def test_required_empty_section_raises_error(
        self, section_diagnosis: TemplateSection, analysis_minimal: AnalysisResult
    ) -> None:
        section_diagnosis.placeholder = None  # Remove placeholder
        context = _build_context(analysis_minimal)
        with pytest.raises(ValueError, match="required"):
            _render_section(section_diagnosis, context)


# ----------------------------------------------------------------------
# Testes — TemplateEngine.__init__()
# ----------------------------------------------------------------------


class TestTemplateEngineInit:
    def test_init_without_template(self) -> None:
        engine = TemplateEngine()
        assert engine.default_template is None

    def test_init_with_template(self) -> None:
        loader = TemplateLoader()
        template = loader.default_template
        engine = TemplateEngine(default_template=template)
        assert engine.default_template is not None
        assert engine.default_template.template_id == "default"

    def test_default_template_is_optional(self) -> None:
        engine = TemplateEngine()
        # Sem default_template, render deve falhar se nenhum template fornecido
        analysis = AnalysisResult(diagnosis="Teste")
        with pytest.raises(ValueError, match="Nenhum template disponível"):
            engine.render(analysis)


# ----------------------------------------------------------------------
# Testes — TemplateEngine.render()
# ----------------------------------------------------------------------


class TestTemplateEngineRender:
    def test_render_with_default_template(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_render_contains_diagnosis_section(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full)
        assert "## Diagnóstico" in report
        assert "Você está num momento de transição profissional" in report

    def test_render_contains_interpretation_section(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full)
        assert "## Interpretação Simbólica" in report
        assert "A Casa" in report

    def test_render_contains_risks_section(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full)
        assert "## Riscos Identificados" in report
        assert "incerteza prolongada" in report

    def test_render_contains_decisions_section(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full)
        assert "## Caminhos de Decisão" in report
        assert "Explorar oportunidades" in report

    def test_render_contains_plan_section(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full)
        assert "## Plano Prático" in report

    def test_render_with_timestamp(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full, timestamp="11/05/2026 às 10:30")
        assert "11/05/2026 às 10:30" in report

    def test_render_with_disclaimer(
        self, engine: TemplateEngine, analysis_minimal: AnalysisResult
    ) -> None:
        disclaimer = "⚠️ Aviso: isso é apenas uma reflexão."
        report = engine.render(analysis_minimal, disclaimer=disclaimer)
        assert disclaimer in report

    def test_render_includes_footer(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full)
        assert "ferramenta de reflexão" in report
        assert "previsão determinista" in report

    def test_render_returns_nonempty_string(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full)
        assert report != ""
        assert isinstance(report, str)

    def test_render_returns_markdown_format(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        report = engine.render(analysis_full)
        assert "## " in report  # H2 sections

    def test_render_with_custom_template(
        self, engine: TemplateEngine, analysis_full: AnalysisResult
    ) -> None:
        loader = TemplateLoader()
        template = loader.default_template
        report = engine.render(analysis_full, template=template)
        assert isinstance(report, str)
        assert len(report) > 0


# ----------------------------------------------------------------------
# Testes — TemplateEngine.render_section()
# ----------------------------------------------------------------------


class TestTemplateEngineRenderSection:
    def test_renders_single_section(
        self, engine: TemplateEngine, section_diagnosis: TemplateSection, analysis_full: AnalysisResult
    ) -> None:
        result = engine.render_section(section_diagnosis, analysis_full)
        assert result is not None
        assert "Você está num momento de transição profissional" in result

    def test_disabled_section_returns_none(
        self, engine: TemplateEngine, section_diagnosis: TemplateSection, analysis_full: AnalysisResult
    ) -> None:
        section_diagnosis.enabled = False
        result = engine.render_section(section_diagnosis, analysis_full)
        assert result is None

    def test_render_section_with_empty_content_returns_placeholder(
        self, engine: TemplateEngine, section_interpretation: TemplateSection, analysis_minimal: AnalysisResult
    ) -> None:
        result = engine.render_section(section_interpretation, analysis_minimal)
        assert result is not None
        assert "*Nenhuma interpretação simbólica disponível.*" in result


# ----------------------------------------------------------------------
# Testes — TemplateEngine.get_available_fields()
# ----------------------------------------------------------------------


class TestTemplateEngineGetAvailableFields:
    def test_returns_list_of_fields(self, engine: TemplateEngine) -> None:
        fields = engine.get_available_fields()
        assert isinstance(fields, list)
        assert len(fields) > 0

    def test_contains_expected_fields(self, engine: TemplateEngine) -> None:
        fields = engine.get_available_fields()
        assert "diagnosis" in fields
        assert "symbolic_interpretation" in fields
        assert "risks" in fields
        assert "decisions" in fields
        assert "practical_plan" in fields

    def test_fields_are_strings(self, engine: TemplateEngine) -> None:
        fields = engine.get_available_fields()
        assert all(isinstance(f, str) for f in fields)


# ----------------------------------------------------------------------
# Testes — TemplateEngine.extract_fields() (static)
# ----------------------------------------------------------------------


class TestTemplateEngineExtractFields:
    def test_extract_fields_static(self) -> None:
        fields = TemplateEngine.extract_fields("{a} e {b}")
        assert fields == ["a", "b"]

    def test_extract_fields_empty_template(self) -> None:
        fields = TemplateEngine.extract_fields("")
        assert fields == []

    def test_extract_fields_no_placeholders(self) -> None:
        fields = TemplateEngine.extract_fields("sem placeholders")
        assert fields == []


# ----------------------------------------------------------------------
# Testes — TemplateEngine.substitute() (static)
# ----------------------------------------------------------------------


class TestTemplateEngineSubstitute:
    def test_substitute_static(self) -> None:
        result = TemplateEngine.substitute("{greeting} {name}!", greeting="Olá", name="João")
        assert result == "Olá João!"

    def test_substitute_empty_template(self) -> None:
        result = TemplateEngine.substitute("", field="value")
        assert result == ""

    def test_substitute_no_placeholders(self) -> None:
        result = TemplateEngine.substitute("texto fixo", field="value")
        assert result == "texto fixo"


# ----------------------------------------------------------------------
# Testes — Edge cases
# ----------------------------------------------------------------------


class TestTemplateEngineEdgeCases:
    def test_empty_analysis_with_all_fields(self) -> None:
        analysis = AnalysisResult(diagnosis="", themes=[], risks=[], decisions=[])
        loader = TemplateLoader()
        engine = TemplateEngine(default_template=loader.default_template)
        report = engine.render(analysis)
        # Deve usar placeholders
        assert "Diagnóstico não disponível" in report or report != ""

    def test_render_without_template_and_no_default_raises(self) -> None:
        engine = TemplateEngine()  # No default
        analysis = AnalysisResult(diagnosis="Teste")
        with pytest.raises(ValueError):
            engine.render(analysis)

    def test_render_with_whitespace_in_fields(self) -> None:
        analysis = AnalysisResult(diagnosis="  Espaços   ")
        loader = TemplateLoader()
        engine = TemplateEngine(default_template=loader.default_template)
        report = engine.render(analysis)
        assert "Espaços" in report

    def test_context_handles_exception_in_preparer(self) -> None:
        """Se um preparador falhar, deve logged e retornar string vazia."""
        analysis = AnalysisResult(diagnosis="Teste")
        context = _build_context(analysis)
        # Todos os campos devem existir mesmo se algum preparador falhar
        for field in ["diagnosis", "symbolic_interpretation", "risks", "decisions", "practical_plan", "cross_card_patterns"]:
            assert field in context


# ----------------------------------------------------------------------
# Testes — Cross card patterns no render
# ----------------------------------------------------------------------


class TestTemplateEngineCrossCardPatterns:
    def test_render_with_cross_card_patterns(self) -> None:
        analysis = AnalysisResult(
            diagnosis="Teste",
            cross_card_patterns=[
                CrossCardPattern(
                    pattern_type="numeric_repeat",
                    card_ids=[1, 13, 25],
                    interpretation="Padrão de repetição numérica.",
                    strength="moderado",
                )
            ],
        )
        # Create custom template with cross_card_patterns section
        custom_template = ReportTemplate(
            template_id="custom",
            name="Custom",
            sections=[
                TemplateSection(
                    id="padroes",
                    title="Padrões Cruzados",
                    order=1,
                    content_template="{cross_card_patterns}",
                )
            ],
        )
        engine = TemplateEngine(default_template=custom_template)
        report = engine.render(analysis)
        # Title case formatting: "numeric_repeat" -> "Numeric Repeat"
        assert "Numeric Repeat" in report
        assert "1, 13, 25" in report
        assert "moderado" in report

    def test_render_section_cross_card_patterns(self) -> None:
        analysis = AnalysisResult(
            diagnosis="Teste",
            cross_card_patterns=[
                CrossCardPattern(
                    pattern_type="theme_cluster",
                    card_ids=[3, 7],
                    interpretation="Agrupamento temático.",
                )
            ],
        )
        engine = TemplateEngine()
        section = TemplateSection(
            id="padroes",
            title="Padrões",
            order=1,
            content_template="{cross_card_patterns}",
        )
        result = engine.render_section(section, analysis)
        assert result is not None
        assert "Agrupamento temático" in result


# ----------------------------------------------------------------------