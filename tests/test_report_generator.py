"""Testes unitários para src/report_generator.py.

Cobertura:
- REPORT_TEMPLATE — contém 5 seções fixas
- ReportGenerator.__init__() — configuração de timestamp
- ReportGenerator.generate() — API principal
- _get_timestamp() — formatação de timestamp
- _format_diagnosis() — seção de Diagnóstico
- _format_symbolic_interpretation() — seção de Interpretação Simbólica com mapeamentos, cartas e temas
- _format_risks() — seção de Riscos Identificados
- _format_decisions() — seção de Caminhos de Decisão
- _format_practical_plan() — seção de Plano Prático
- format_list() — utilitário estático de formatação de lista
- bold() — utilitário estático de negrito Markdown
- italic() — utilitário estático de itálico Markdown
- Edge cases: campos vazios, injeção de disclaimer, timestamp desabilitado
"""

import pytest

from src.report_generator import REPORT_TEMPLATE, ReportGenerator
from src.types import AnalysisResult, CardPosition


def bold(text: str) -> str:
    return ReportGenerator.bold(text)


def italic(text: str) -> str:
    return ReportGenerator.italic(text)


def format_list(items: list[str], bullet: str = "-") -> str:
    """Wrapper que delega para o método estático da classe."""
    return ReportGenerator.format_list(items, bullet)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def generator() -> ReportGenerator:
    """Gerador com configurações padrão (timestamp ativo)."""
    return ReportGenerator(include_timestamp=True)


@pytest.fixture
def generator_no_timestamp() -> ReportGenerator:
    """Gerador sem timestamp."""
    return ReportGenerator(include_timestamp=False)


@pytest.fixture
def analysis_full() -> AnalysisResult:
    """AnalysisResult com todos os campos preenchidos."""
    return AnalysisResult(
        diagnosis="Você está num momento de transição profissional.",
        themes=["trabalho", "mudança", "decisão"],
        risks=["incerteza prolongada", "hesitação excessiva"],
        decisions=[
            "Explorar oportunidades de recolocação",
            "Investir em qualificação profissional",
        ],
        practical_plan="1. Atualizar o currículo esta semana.\n2. Pesquisar cursos relevantes.\n3. Agendar entrevistas.",
        card_interpretations=[
            "**Carta 1 - A Casa**: Indica estabilidade e proteção.",
            "**Carta 2 - A Estrela**: Sinaliza esperança e direcionamento.",
        ],
        symbolic_mappings={
            "kw:casa": "A Casa",
            "kw:trabalho": "O Trabalho",
            "card:Casa": "A Casa",
        },
    )


@pytest.fixture
def analysis_minimal() -> AnalysisResult:
    """AnalysisResult com campos mínimos (empty diagnosis)."""
    return AnalysisResult(diagnosis="", themes=[], risks=[], decisions=[], practical_plan="")


# ----------------------------------------------------------------------
# Testes — REPORT_TEMPLATE
# ----------------------------------------------------------------------


class TestReportTemplate:
    def test_template_contains_five_sections(self) -> None:
        """Template contém as 5 seções obrigatórias."""
        assert "## Diagnóstico" in REPORT_TEMPLATE
        assert "## Interpretação Simbólica" in REPORT_TEMPLATE
        assert "## Riscos Identificados" in REPORT_TEMPLATE
        assert "## Caminhos de Decisão" in REPORT_TEMPLATE
        assert "## Plano Prático" in REPORT_TEMPLATE

    def test_template_has_timestamp_placeholder(self) -> None:
        """Template contém placeholder de timestamp."""
        assert "{timestamp}" in REPORT_TEMPLATE

    def test_template_has_footer_disclaimer(self) -> None:
        """Template contém disclaimer ético no rodapé."""
        assert "ferramenta de reflexão" in REPORT_TEMPLATE
        assert "previsão determinista" in REPORT_TEMPLATE

    def test_template_has_h1_title(self) -> None:
        """Template começa com título H1."""
        assert REPORT_TEMPLATE.startswith("# Relatório de Análise — {timestamp}")


# ----------------------------------------------------------------------
# Testes — ReportGenerator.__init__()
# ----------------------------------------------------------------------


class TestReportGeneratorInit:
    def test_init_default_timestamp_true(self) -> None:
        """Default: include_timestamp=True."""
        g = ReportGenerator()
        assert g.include_timestamp is True

    def test_init_explicit_timestamp_true(self) -> None:
        """Explicit include_timestamp=True."""
        g = ReportGenerator(include_timestamp=True)
        assert g.include_timestamp is True

    def test_init_timestamp_false(self) -> None:
        """Explicit include_timestamp=False."""
        g = ReportGenerator(include_timestamp=False)
        assert g.include_timestamp is False


# ----------------------------------------------------------------------
# Testes — ReportGenerator.generate(): estrutura do relatório
# ----------------------------------------------------------------------


class TestGenerateStructure:
    def test_generates_all_five_sections(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório contém todas as 5 seções."""
        report = generator.generate(analysis_full)
        assert "## Diagnóstico" in report
        assert "## Interpretação Simbólica" in report
        assert "## Riscos Identificados" in report
        assert "## Caminhos de Decisão" in report
        assert "## Plano Prático" in report

    def test_generates_h1_title(self, generator: ReportGenerator, analysis_full: AnalysisResult) -> None:
        """Relatório começa com título H1."""
        report = generator.generate(analysis_full)
        assert report.startswith("# Relatório de Análise")

    def test_generates_footer_disclaimer(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Rodapé contém disclaimer ético."""
        report = generator.generate(analysis_full)
        assert "ferramenta de reflexão" in report
        assert "previsão determinista" in report

    def test_timestamp_included_by_default(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Timestamp presente quando include_timestamp=True."""
        report = generator.generate(analysis_full)
        # Timestamp formatado: dd/mm/yyyy às HH:MM
        import re

        assert re.search(r"\d{2}/\d{2}/\d{4}", report) is not None

    def test_timestamp_excluded_when_disabled(
        self, generator_no_timestamp: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Timestamp ausente quando include_timestamp=False."""
        report = generator_no_timestamp.generate(analysis_full)
        # Título preserva o em-dash mas sem conteúdo de timestamp após
        assert report.startswith("# Relatório de Análise — \n\n## Diagnóstico")


# ----------------------------------------------------------------------
# Testes — _format_diagnosis()
# ----------------------------------------------------------------------


class TestFormatDiagnosis:
    def test_diagnosis_appears_in_report(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Diagnóstico aparece na seção correta."""
        report = generator.generate(analysis_full)
        assert "Você está num momento de transição profissional." in report

    def test_empty_diagnosis_fallback(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """Diagnóstico vazio usa texto de fallback."""
        report = generator.generate(analysis_minimal)
        assert "Diagnóstico não disponível" in report


# ----------------------------------------------------------------------
# Testes — _format_symbolic_interpretation()
# ----------------------------------------------------------------------


class TestFormatSymbolicInterpretation:
    def test_keyword_mappings_section(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Mapeamentos de keywords aparecem na seção."""
        report = generator.generate(analysis_full)
        assert "### Mapeamentos Identificados" in report
        assert "A Casa" in report

    def test_card_interpretations_section(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Interpretações das cartas aparecem na seção."""
        report = generator.generate(analysis_full)
        assert "### Interpretação das Cartas" in report
        assert "A Casa" in report
        assert "A Estrela" in report

    def test_themes_section(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Temas predominantes aparecem na seção."""
        report = generator.generate(analysis_full)
        assert "### Temas Predominantes" in report
        assert "*trabalho*" in report
        assert "*mudança*" in report

    def test_no_data_fallback(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """Seção vazia usa texto de fallback."""
        report = generator.generate(analysis_minimal)
        assert "Nenhuma interpretação simbólica disponível" in report


# ----------------------------------------------------------------------
# Testes — _format_risks()
# ----------------------------------------------------------------------


class TestFormatRisks:
    def test_risks_listed(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Riscos são listados com marcadores."""
        report = generator.generate(analysis_full)
        assert "incerteza prolongada" in report
        assert "hesitação excessiva" in report

    def test_empty_risks_fallback(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """Riscos vazios usam texto de fallback."""
        report = generator.generate(analysis_minimal)
        assert "Nenhum risco específico identificado" in report


# ----------------------------------------------------------------------
# Testes — _format_decisions()
# ----------------------------------------------------------------------


class TestFormatDecisions:
    def test_decisions_numbered(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Decisões são numeradas."""
        report = generator.generate(analysis_full)
        assert "1. Explorar oportunidades de recolocação" in report
        assert "2. Investir em qualificação profissional" in report

    def test_empty_decisions_fallback(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """Decisões vazias usam texto de fallback."""
        report = generator.generate(analysis_minimal)
        assert "Nenhum caminho de decisão específico identificado" in report


# ----------------------------------------------------------------------
# Testes — _format_practical_plan()
# ----------------------------------------------------------------------


class TestFormatPracticalPlan:
    def test_plan_content(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Plano prático aparece na seção."""
        report = generator.generate(analysis_full)
        assert "Atualizar o currículo esta semana" in report
        assert "Pesquisar cursos relevantes" in report

    def test_empty_plan_fallback(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """Plano vazio usa texto de fallback."""
        report = generator.generate(analysis_minimal)
        assert "Plano prático não disponível" in report


# ----------------------------------------------------------------------
# Testes — Injeção de disclaimer
# ----------------------------------------------------------------------


class TestGenerateDisclaimerInjection:
    def test_disclaimer_appended(self, generator: ReportGenerator, analysis_minimal: AnalysisResult) -> None:
        """Disclaimer adicional é inserido antes do rodapé."""
        disclaimer = "⚠️ Aviso: isso é apenas uma reflexão orientadora."
        report = generator.generate(analysis_minimal, disclaimer=disclaimer)
        assert disclaimer in report

    def test_disclaimer_not_injected_when_none(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """Sem disclaimer, nada é inserido além do template."""
        report = generator.generate(analysis_minimal, disclaimer=None)
        # Não deve conter marcadores extras fora do template
        lines = report.split("\n")
        assert all(line.count("⚠️") == 0 for line in lines)


# ----------------------------------------------------------------------
# Testes — Utilitários estáticos
# ----------------------------------------------------------------------


class TestFormatList:
    def test_format_list_items(self) -> None:
        """format_list formata itens com marcador."""
        result = format_list(["item um", "item dois"])
        assert "- item um" in result
        assert "- item dois" in result

    def test_format_list_custom_bullet(self) -> None:
        """format_list aceita marcador customizado."""
        result = format_list(["item"], bullet="*")
        assert "* item" in result

    def test_format_list_empty_returns_fallback(self) -> None:
        """format_list com lista vazia retorna fallback."""
        result = format_list([])
        assert "Nenhum item disponível" in result


class TestBold:
    def test_bold_wraps_text(self) -> None:
        """bold envolve texto em **."""
        assert bold("teste") == "**teste**"

    def test_bold_empty_string(self) -> None:
        """bold com string vazia."""
        assert bold("") == "****"


class TestItalic:
    def test_italic_wraps_text(self) -> None:
        """italic envolve texto em _."""
        assert italic("teste") == "_teste_"

    def test_italic_empty_string(self) -> None:
        """italic com string vazia."""
        assert italic("") == "__"


# ----------------------------------------------------------------------
# Testes — Edge cases
# ----------------------------------------------------------------------


class TestEdgeCases:
    def test_analysis_with_only_diagnosis(
        self, generator: ReportGenerator
    ) -> None:
        """Análise com apenas diagnóstico preenche Diagnóstico."""
        analysis = AnalysisResult(diagnosis="Diagnóstico simples.")
        report = generator.generate(analysis)
        assert "Diagnóstico simples" in report
        assert "Nenhuma interpretação simbólica disponível" in report
        assert "Nenhum risco específico identificado" in report

    def test_analysis_with_themes_only(
        self, generator: ReportGenerator
    ) -> None:
        """Análise com apenas temas preenche Interpretação Simbólica."""
        analysis = AnalysisResult(diagnosis="", themes=["amor", "relacionamento"])
        report = generator.generate(analysis)
        assert "### Temas Predominantes" in report
        assert "*amor*" in report

    def test_analysis_with_only_risks(
        self, generator: ReportGenerator
    ) -> None:
        """Análise com apenas riscos."""
        analysis = AnalysisResult(diagnosis="", risks=["risco alto"])
        report = generator.generate(analysis)
        assert "risco alto" in report
        assert "Nenhum risco específico identificado" not in report

    def test_analysis_with_only_decisions(
        self, generator: ReportGenerator
    ) -> None:
        """Análise com apenas decisões."""
        analysis = AnalysisResult(diagnosis="", decisions=["decisão única"])
        report = generator.generate(analysis)
        assert "1. decisão única" in report
        assert "Nenhum caminho de decisão específico identificado" not in report

    def test_symbolic_mappings_keyword_prefix(
        self, generator: ReportGenerator
    ) -> None:
        """Mapeamentos com prefixo kw: usam label 'Keyword'."""
        analysis = AnalysisResult(
            diagnosis="",
            symbolic_mappings={"kw:casa": "A Casa"},
        )
        report = generator.generate(analysis)
        assert "Keyword" in report
        assert "casa" in report

    def test_symbolic_mappings_card_prefix(
        self, generator: ReportGenerator
    ) -> None:
        """Mapeamentos com prefixo card: usam label 'Carta'."""
        analysis = AnalysisResult(
            diagnosis="",
            symbolic_mappings={"card:Casa": "A Casa"},
        )
        report = generator.generate(analysis)
        assert "Carta" in report
        assert "Casa" in report

    def test_generate_returns_nonempty_string(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """generate() retorna string não-vazia."""
        report = generator.generate(analysis_full)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_generate_returns_markdown_format(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """generate() retorna formato Markdown válido."""
        report = generator.generate(analysis_full)
        # Deve conter pelo menos um H2 para cada seção
        assert report.count("## ") >= 5


# ----------------------------------------------------------------------
# Testes — output_format: compact
# ----------------------------------------------------------------------


class TestCompactOutput:
    def test_generate_compact_format(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """output_format='compact' gera relatório compacto."""
        report = generator.generate(analysis_full, output_format="compact")
        assert "# Análise" in report
        assert "## Diagnóstico" in report
        assert "## Interpretação Simbólica" in report
        assert "## Riscos Identificados" in report
        assert "## Caminhos de Decisão" in report
        assert "## Plano Prático" in report

    def test_compact_title_differs_from_default(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Título compacto '# Análise' difere do padrão '# Relatório de Análise'."""
        default_report = generator.generate(analysis_full, output_format="default")
        compact_report = generator.generate(analysis_full, output_format="compact")
        assert default_report.startswith("# Relatório de Análise")
        assert compact_report.startswith("# Análise —")

    def test_compact_contains_all_five_sections(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório compacto contém todas as 5 seções."""
        report = generator.generate(analysis_full, output_format="compact")
        assert "## Diagnóstico" in report
        assert "## Interpretação Simbólica" in report
        assert "## Riscos Identificados" in report
        assert "## Caminhos de Decisão" in report
        assert "## Plano Prático" in report

    def test_compact_includes_timestamp_by_default(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório compacto inclui timestamp quando include_timestamp=True."""
        import re

        report = generator.generate(analysis_full, output_format="compact")
        assert re.search(r"\d{2}/\d{2}/\d{4}", report) is not None

    def test_compact_excludes_timestamp_when_disabled(
        self, generator_no_timestamp: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório compacto sem timestamp."""
        report = generator_no_timestamp.generate(analysis_full, output_format="compact")
        assert report.startswith("# Análise — \n\n## Diagnóstico")

    def test_compact_has_footer_disclaimer(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Rodapé de relatório compacto contém disclaimer ético."""
        report = generator.generate(analysis_full, output_format="compact")
        assert "ferramenta de reflexão" in report
        assert "previsão determinista" in report

    def test_compact_with_disclaimer(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """Compact com disclaimer injetado."""
        disclaimer = "⚠️ Aviso: isso é apenas uma reflexão orientadora."
        report = generator.generate(analysis_minimal, output_format="compact", disclaimer=disclaimer)
        assert disclaimer in report

    def test_compact_generates_nonempty_string(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """generate() com output_format='compact' retorna string não-vazia."""
        report = generator.generate(analysis_full, output_format="compact")
        assert isinstance(report, str)
        assert len(report) > 0


# ----------------------------------------------------------------------
# Testes — output_format: json
# ----------------------------------------------------------------------


class TestJsonOutput:
    def test_generate_json_format(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """output_format='json' gera JSON válido."""
        import json

        report = generator.generate(analysis_full, output_format="json")
        data = json.loads(report)
        assert "timestamp" in data
        assert "diagnosis" in data
        assert "symbolic_interpretation" in data
        assert "risks" in data
        assert "decisions" in data
        assert "practical_plan" in data

    def test_json_contains_analysis_data(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """JSON contém dados da análise."""
        import json

        report = generator.generate(analysis_full, output_format="json")
        data = json.loads(report)
        assert "Você está num momento de transição profissional" in data["diagnosis"]
        assert "trabalho" in data["symbolic_interpretation"]
        assert "incerteza prolongada" in data["risks"]
        assert "Explorar oportunidades" in data["decisions"]

    def test_json_has_timestamp_when_enabled(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """JSON inclui timestamp quando include_timestamp=True."""
        import json

        report = generator.generate(analysis_full, output_format="json")
        data = json.loads(report)
        assert data["timestamp"] != ""
        assert "/" in data["timestamp"]  # formato dd/mm/yyyy

    def test_json_excludes_timestamp_when_disabled(
        self, generator_no_timestamp: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """JSON sem timestamp quando include_timestamp=False."""
        import json

        report = generator_no_timestamp.generate(analysis_full, output_format="json")
        data = json.loads(report)
        assert data["timestamp"] == ""

    def test_json_with_disclaimer(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """JSON inclui disclaimer quando fornecido."""
        import json

        disclaimer = "⚠️ Aviso: isso é apenas uma reflexão orientadora."
        report = generator.generate(analysis_full, output_format="json", disclaimer=disclaimer)
        data = json.loads(report)
        assert data["disclaimer"] == disclaimer

    def test_json_without_disclaimer(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """JSON não inclui campo disclaimer quando não fornecido."""
        import json

        report = generator.generate(analysis_full, output_format="json")
        data = json.loads(report)
        assert "disclaimer" not in data

    def test_json_minimal_analysis(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """JSON funciona com análise mínima."""
        import json

        report = generator.generate(analysis_minimal, output_format="json")
        data = json.loads(report)
        assert "timestamp" in data
        assert "diagnosis" in data
        assert "symbolic_interpretation" in data
        assert "risks" in data
        assert "decisions" in data
        assert "practical_plan" in data

    def test_json_returns_valid_json_string(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """generate() com output_format='json' retorna JSON válido."""
        import json

        report = generator.generate(analysis_full, output_format="json")
        # Deve ser possível fazer parse do JSON sem erros
        data = json.loads(report)
        assert isinstance(data, dict)
        assert len(data) > 0


# ----------------------------------------------------------------------
# Testes — output_format: verbose
# ----------------------------------------------------------------------


class TestVerboseOutput:
    def test_generate_verbose_format(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """output_format='verbose' gera relatório verboso."""
        report = generator.generate(analysis_full, output_format="verbose")
        assert "# Relatório Detalhado de Análise" in report
        assert "## Seção 1: Diagnóstico" in report
        assert "## Seção 2: Interpretação Simbólica" in report
        assert "## Seção 3: Riscos Identificados" in report
        assert "## Seção 4: Caminhos de Decisão" in report
        assert "## Seção 5: Padrões Cruzados" in report
        assert "## Seção 6: Plano Prático" in report

    def test_verbose_title_differs_from_default(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Título verboso difere do padrão e do compacto."""
        default_report = generator.generate(analysis_full, output_format="default")
        verbose_report = generator.generate(analysis_full, output_format="verbose")
        assert default_report.startswith("# Relatório de Análise")
        assert verbose_report.startswith("# Relatório Detalhado de Análise")

    def test_verbose_contains_all_six_sections(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório verboso contém todas as 6 seções numeradas."""
        report = generator.generate(analysis_full, output_format="verbose")
        assert "## Seção 1: Diagnóstico" in report
        assert "## Seção 2: Interpretação Simbólica" in report
        assert "## Seção 3: Riscos Identificados" in report
        assert "## Seção 4: Caminhos de Decisão" in report
        assert "## Seção 5: Padrões Cruzados" in report
        assert "## Seção 6: Plano Prático" in report

    def test_verbose_contains_explanatory_blockquotes(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório verboso contém blockquotes explicativos para cada seção."""
        report = generator.generate(analysis_full, output_format="verbose")
        # Cada seção tem um blockquote explicativo
        assert "> **Sobre esta seção:**" in report
        # Deve haver 6 blockquotes (uma por seção)
        assert report.count("> **Sobre esta seção:**") >= 6

    def test_verbose_includes_timestamp_by_default(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório verboso inclui timestamp quando include_timestamp=True."""
        import re

        report = generator.generate(analysis_full, output_format="verbose")
        assert re.search(r"\d{2}/\d{2}/\d{4}", report) is not None

    def test_verbose_excludes_timestamp_when_disabled(
        self, generator_no_timestamp: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório verboso sem timestamp."""
        report = generator_no_timestamp.generate(analysis_full, output_format="verbose")
        assert report.startswith("# Relatório Detalhado de Análise — \n\n## Seção 1: Diagnóstico")

    def test_verbose_has_footer_disclaimer(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Rodapé de relatório verboso contém disclaimer ético."""
        report = generator.generate(analysis_full, output_format="verbose")
        assert "ferramenta de reflexão" in report
        assert "previsão determinista" in report

    def test_verbose_with_disclaimer(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """Verbose com disclaimer injetado."""
        disclaimer = "⚠️ Aviso: isso é apenas uma reflexão orientadora."
        report = generator.generate(analysis_minimal, output_format="verbose", disclaimer=disclaimer)
        assert disclaimer in report

    def test_verbose_generates_nonempty_string(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """generate() com output_format='verbose' retorna string não-vazia."""
        report = generator.generate(analysis_full, output_format="verbose")
        assert isinstance(report, str)
        assert len(report) > 0

    def test_verbose_contains_diagnosis_content(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório verboso contém conteúdo do diagnóstico."""
        report = generator.generate(analysis_full, output_format="verbose")
        assert "Você está num momento de transição profissional" in report

    def test_verbose_contains_symbolic_interpretation(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório verboso contém interpretação simbólica."""
        report = generator.generate(analysis_full, output_format="verbose")
        assert "A Casa" in report
        assert "A Estrela" in report

    def test_verbose_contains_risks(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório verboso contém riscos identificados."""
        report = generator.generate(analysis_full, output_format="verbose")
        assert "incerteza prolongada" in report
        assert "hesitação excessiva" in report

    def test_verbose_contains_decisions(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório verboso contém caminhos de decisão."""
        report = generator.generate(analysis_full, output_format="verbose")
        assert "Explorar oportunidades de recolocação" in report
        assert "Investir em qualificação profissional" in report

    def test_verbose_contains_practical_plan(
        self, generator: ReportGenerator, analysis_full: AnalysisResult
    ) -> None:
        """Relatório verboso contém plano prático."""
        report = generator.generate(analysis_full, output_format="verbose")
        assert "Atualizar o currículo" in report

    def test_verbose_minimal_analysis(
        self, generator: ReportGenerator, analysis_minimal: AnalysisResult
    ) -> None:
        """Verbose funciona com análise mínima."""
        report = generator.generate(analysis_minimal, output_format="verbose")
        assert "# Relatório Detalhado de Análise" in report
        assert "## Seção 1: Diagnóstico" in report
        assert "## Seção 2: Interpretação Simbólica" in report
        assert "## Seção 3: Riscos Identificados" in report
        assert "## Seção 4: Caminhos de Decisão" in report
        assert "## Seção 5: Padrões Cruzados" in report
        assert "## Seção 6: Plano Prático" in report
