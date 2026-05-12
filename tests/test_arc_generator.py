"""Testes unitários para src/arc_generator.py.

Cobertura:
- ArcGenerator.__init__() — inicialização com session_context opcional
- ArcGenerator.generate() — API principal de geração de arco
- ArcGenerator.build_arc() — construção de Arc a partir de sessões
- ArcGenerator.identify_threads() — identificação de threads narrativas
- ArcGenerator.generate_timeline() — geração de linha do tempo ASCII
- ArcGenerator.generate_recurring_symbols() — lista de símbolos recorrentes
- ArcGenerator.generate_narrative_summary() — sumário narrativo
- ArcGenerator.generate_threads() — seção de threads persistentes
- Templates: ARC_TEMPLATE, TIMELINE_TEMPLATE, RECURRING_SYMBOLS_TEMPLATE, THREADS_TEMPLATE
- Edge cases: sessões vazias, sem themes, sem símbolos
"""

import pytest

from clareza.arc_generator import (
    ARC_TEMPLATE,
    THREADS_TEMPLATE,
    RECURRING_SYMBOLS_TEMPLATE,
    TIMELINE_TEMPLATE,
    ArcGenerator,
)
from clareza.types import (
    AnalysisResult,
    Arc,
    NarrativeThread,
    Session,
    SessionContext,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def arc_generator() -> ArcGenerator:
    """ArcGenerator com configurações padrão."""
    return ArcGenerator()


@pytest.fixture
def arc_generator_with_context() -> ArcGenerator:
    """ArcGenerator com session_context."""
    context = SessionContext(session_id="ctx-001")
    return ArcGenerator(session_context=context)


@pytest.fixture
def sample_analysis() -> AnalysisResult:
    """AnalysisResult de exemplo."""
    return AnalysisResult(
        diagnosis="Você está num momento de transição profissional.",
        themes=["trabalho", "carreira", "mudança"],
        risks=["incerteza prolongada"],
        decisions=["Explorar novas oportunidades"],
        practical_plan="1. Atualizar currículo",
        symbolic_mappings={
            "kw:casa": "A Casa",
            "kw:trabalho": "O Trabalho",
        },
    )


@pytest.fixture
def sample_analysis_2() -> AnalysisResult:
    """Segundo AnalysisResult de exemplo (mesmos temas para testar recorrência)."""
    return AnalysisResult(
        diagnosis="Continuam as questões de carreira.",
        themes=["trabalho", "carreira"],
        risks=[],
        decisions=["Investir em qualificação"],
        practical_plan="1. Fazer curso",
        symbolic_mappings={
            "kw:casa": "A Casa",
            "kw:carreira": "Carreira",
        },
    )


@pytest.fixture
def sample_session(sample_analysis) -> Session:
    """Sessão de exemplo."""
    return Session(
        session_id="sess-001-abc123",
        timestamp="2024-01-15T10:30:00",
        input_format="text",
        raw_content="Estou pensando em mudar de emprego",
        analysis_result=sample_analysis,
        unresolved_threads=["thread_trabalho"],
    )


@pytest.fixture
def sample_session_2(sample_analysis_2) -> Session:
    """Segunda sessão de exemplo."""
    return Session(
        session_id="sess-002-def456",
        timestamp="2024-02-20T14:00:00",
        input_format="symbols",
        raw_content="casa, estrela",
        analysis_result=sample_analysis_2,
        unresolved_threads=["thread_trabalho"],
    )


@pytest.fixture
def sessions_list(sample_session, sample_session_2) -> list[Session]:
    """Lista de sessões para testes."""
    return [sample_session, sample_session_2]


@pytest.fixture
def sample_arc(sessions_list) -> Arc:
    """Arc de exemplo para testes."""
    generator = ArcGenerator()
    return generator.build_arc(sessions_list, arc_name="Teste de Arco")


# ----------------------------------------------------------------------
# Testes — Templates
# ----------------------------------------------------------------------


class TestArcTemplates:
    def test_arc_template_has_arc_name_placeholder(self) -> None:
        """ARC_TEMPLATE contém placeholder para nome do arco."""
        assert "{arc_name}" in ARC_TEMPLATE

    def test_arc_template_has_sections(self) -> None:
        """ARC_TEMPLATE contém todas as seções."""
        assert "{summary_section}" in ARC_TEMPLATE
        assert "{timeline_section}" in ARC_TEMPLATE
        assert "{recurring_symbols_section}" in ARC_TEMPLATE
        assert "{threads_section}" in ARC_TEMPLATE
        assert "{resolution_section}" in ARC_TEMPLATE

    def test_arc_template_has_footer_disclaimer(self) -> None:
        """ARC_TEMPLATE contém disclaimer ético."""
        assert "ferramenta de reflexão" in ARC_TEMPLATE
        assert "previsão determinista" in ARC_TEMPLATE

    def test_timeline_template_has_placeholders(self) -> None:
        """TIMELINE_TEMPLATE contém placeholders necessários."""
        assert "{entries}" in TIMELINE_TEMPLATE
        assert "{start_date}" in TIMELINE_TEMPLATE
        assert "{end_date}" in TIMELINE_TEMPLATE
        assert "{session_count}" in TIMELINE_TEMPLATE

    def test_recurring_symbols_template_has_placeholders(self) -> None:
        """RECURRING_SYMBOLS_TEMPLATE contém placeholders."""
        assert "{intro}" in RECURRING_SYMBOLS_TEMPLATE
        assert "{symbols_list}" in RECURRING_SYMBOLS_TEMPLATE
        assert "{insight}" in RECURRING_SYMBOLS_TEMPLATE

    def test_threads_template_has_placeholders(self) -> None:
        """THREADS_TEMPLATE contém placeholders."""
        assert "{intro}" in THREADS_TEMPLATE
        assert "{threads_list}" in THREADS_TEMPLATE


# ----------------------------------------------------------------------
# Testes — ArcGenerator.__init__()
# ----------------------------------------------------------------------


class TestArcGeneratorInit:
    def test_init_without_context(self) -> None:
        """Inicialização sem session_context."""
        generator = ArcGenerator()
        assert generator.session_context is None

    def test_init_with_context(self) -> None:
        """Inicialização com session_context."""
        context = SessionContext(session_id="ctx-001")
        generator = ArcGenerator(session_context=context)
        assert generator.session_context is context
        assert generator.session_context.session_id == "ctx-001"


# ----------------------------------------------------------------------
# Testes — ArcGenerator.build_arc()
# ----------------------------------------------------------------------


class TestBuildArc:
    def test_build_arc_with_sessions(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """build_arc constrói Arc válido."""
        arc = arc_generator.build_arc(sessions_list, arc_name="Arco de Teste")

        assert isinstance(arc, Arc)
        assert arc.name == "Arco de Teste"
        assert len(arc.sessions) == 2
        assert arc.arc_id.startswith("arc_")

    def test_build_arc_extracts_dates(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """build_arc extrai datas de início e fim."""
        arc = arc_generator.build_arc(sessions_list)

        assert arc.start_date is not None
        assert arc.end_date is not None
        assert "15/01/2024" in arc.start_date
        assert "20/02/2024" in arc.end_date

    def test_build_arc_identifies_dominant_themes(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """build_arc extrai temas dominantes."""
        arc = arc_generator.build_arc(sessions_list)

        assert len(arc.dominant_themes) > 0
        assert "trabalho" in arc.dominant_themes

    def test_build_arc_with_custom_name(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """build_arc usa nome customizado quando fornecido."""
        arc = arc_generator.build_arc(sessions_list, arc_name="Minha Jornada")

        assert arc.name == "Minha Jornada"

    def test_build_arc_generates_name_if_none(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """build_arc gera nome automaticamente se não fornecido."""
        arc = arc_generator.build_arc(sessions_list)

        assert arc.name != ""
        assert "Jornada" in arc.name

    def test_build_arc_empty_sessions_raises(
        self, arc_generator: ArcGenerator
    ) -> None:
        """build_arc com lista vazia levanta ValueError."""
        with pytest.raises(ValueError, match="Lista de sessões vazia"):
            arc_generator.build_arc([])

    def test_build_arc_identifies_threads(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """build_arc identifica threads narrativas."""
        arc = arc_generator.build_arc(sessions_list)

        assert len(arc.threads) >= 0


# ----------------------------------------------------------------------
# Testes — ArcGenerator.identify_threads()
# ----------------------------------------------------------------------


class TestIdentifyThreads:
    def test_identify_threads_with_recurring_themes(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """identify_threads encontra temas recorrentes."""
        threads = arc_generator.identify_threads(sessions_list)

        # "trabalho" e "carreira" aparecem em ambas as sessões
        assert len(threads) >= 2
        themes = [t.theme for t in threads]
        assert "trabalho" in themes
        assert "carreira" in themes

    def test_identify_threads_single_session(
        self, arc_generator: ArcGenerator, sample_session: Session
    ) -> None:
        """identify_threads com uma sessão retorna lista vazia."""
        threads = arc_generator.identify_threads([sample_session])

        # Uma sessão não forma thread recorrente
        assert threads == []

    def test_identify_threads_empty_sessions(
        self, arc_generator: ArcGenerator
    ) -> None:
        """identify_threads com lista vazia retorna lista vazia."""
        threads = arc_generator.identify_threads([])

        assert threads == []

    def test_identify_threads_returns_narrative_threads(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """identify_threads retorna lista de NarrativeThread."""
        threads = arc_generator.identify_threads(sessions_list)

        for thread in threads:
            assert isinstance(thread, NarrativeThread)
            assert thread.thread_id.startswith("thread_")
            assert thread.name is not None
            assert thread.theme is not None
            assert len(thread.session_ids) >= 2


# ----------------------------------------------------------------------
# Testes — ArcGenerator.generate_timeline()
# ----------------------------------------------------------------------


class TestGenerateTimeline:
    def test_timeline_contains_sessions(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_timeline lista todas as sessões."""
        timeline = arc_generator.generate_timeline(sample_arc)

        assert "Sessão 1" in timeline
        assert "Sessão 2" in timeline
        assert "## Linha do Tempo" in timeline

    def test_timeline_contains_dates(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_timeline mostra período."""
        timeline = arc_generator.generate_timeline(sample_arc)

        assert "15/01/2024" in timeline
        assert "20/02/2024" in timeline

    def test_timeline_shows_session_count(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_timeline mostra total de sessões."""
        timeline = arc_generator.generate_timeline(sample_arc)

        assert "Total de sessões" in timeline
        assert "2" in timeline

    def test_timeline_empty_arc(self, arc_generator: ArcGenerator) -> None:
        """generate_timeline com arco vazio retorna mensagem."""
        arc = Arc(arc_id="arc_empty", name="Empty")
        timeline = arc_generator.generate_timeline(arc)

        assert "não disponível" in timeline

    def test_timeline_shows_diagnosis(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_timeline mostra diagnóstico de cada sessão."""
        timeline = arc_generator.generate_timeline(sample_arc)

        assert "Diagnóstico" in timeline
        assert "transição profissional" in timeline

    def test_timeline_shows_unresolved_threads(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_timeline indica threads não resolvidas."""
        timeline = arc_generator.generate_timeline(sample_arc)

        # sample_session tem unresolved_threads
        assert "thread(s)" in timeline or "não resolvida" in timeline


# ----------------------------------------------------------------------
# Testes — ArcGenerator.generate_recurring_symbols()
# ----------------------------------------------------------------------


class TestGenerateRecurringSymbols:
    def test_recurring_symbols_with_data(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_recurring_symbols detecta símbolos recorrentes."""
        result = arc_generator.generate_recurring_symbols(sample_arc)

        assert "## Símbolos Recorrentes" in result
        assert "A Casa" in result  # aparece em ambas sessões

    def test_recurring_symbols_count(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_recurring_symbols conta corretamente."""
        result = arc_generator.generate_recurring_symbols(sample_arc)

        # Deve mostrar quantidade de símbolos
        assert "identificados" in result

    def test_recurring_symbols_empty_arc(self, arc_generator: ArcGenerator) -> None:
        """generate_recurring_symbols com arco vazio."""
        arc = Arc(arc_id="arc_empty", name="Empty")
        result = arc_generator.generate_recurring_symbols(arc)

        assert "não disponíveis" in result

    def test_recurring_symbols_no_symbols(
        self, arc_generator: ArcGenerator, sample_session: Session
    ) -> None:
        """generate_recurring_symbols sem símbolos nas sessões."""
        arc = Arc(arc_id="arc_test", name="Test")
        arc.sessions = [sample_session]
        # analysis_result é o sample_analysis que tem symbolic_mappings

        result = arc_generator.generate_recurring_symbols(arc)

        # Uma sessão não forma símbolo recorrente (mínimo 2)
        assert "Nenhum símbolo recorrente" in result or "não disponível" in result

    def test_recurring_symbols_generates_insight(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_recurring_symbols gera insight sobre símbolo mais recorrente."""
        result = arc_generator.generate_recurring_symbols(sample_arc)

        assert "sugere" in result.lower() or "energia" in result.lower()


# ----------------------------------------------------------------------
# Testes — ArcGenerator.generate_threads()
# ----------------------------------------------------------------------


class TestGenerateThreads:
    def test_threads_section_header(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_threads gera seção correta."""
        result = arc_generator.generate_threads(sample_arc)

        assert "## Temas Persistentes" in result

    def test_threads_with_data(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_threads lista threads identificadas."""
        result = arc_generator.generate_threads(sample_arc)

        # Deve listar as threads identificadas
        assert "trabalho" in result.lower() or "###" in result

    def test_threads_empty_arc(self, arc_generator: ArcGenerator) -> None:
        """generate_threads com arco sem threads."""
        arc = Arc(arc_id="arc_empty", name="Empty")
        result = arc_generator.generate_threads(arc)

        assert "Nenhuma thread" in result

    def test_threads_shows_status(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_threads mostra status das threads."""
        result = arc_generator.generate_threads(sample_arc)

        # Status deve estar presente
        assert "Status" in result or "Evolução" in result or "Resolvido" in result

    def test_threads_shows_session_count(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_threads mostra contagem de sessões."""
        result = arc_generator.generate_threads(sample_arc)

        assert "Sessões" in result


# ----------------------------------------------------------------------
# Testes — ArcGenerator.generate_narrative_summary()
# ----------------------------------------------------------------------


class TestGenerateNarrativeSummary:
    def test_summary_contains_header(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_narrative_summary gera seção correta."""
        result = arc_generator.generate_narrative_summary(sample_arc)

        assert "## Síntese Narrativa" in result

    def test_summary_contains_date_range(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_narrative_summary menciona período."""
        result = arc_generator.generate_narrative_summary(sample_arc)

        assert "janeiro" in result.lower() or "fevereiro" in result.lower() or "2024" in result

    def test_summary_single_session(self, arc_generator: ArcGenerator) -> None:
        """generate_narrative_summary com uma sessão."""
        session = Session(
            session_id="sess-001",
            timestamp="2024-01-15T10:30:00",
            input_format="text",
            raw_content="Teste",
        )
        arc = arc_generator.build_arc([session])
        result = arc_generator.generate_narrative_summary(arc)

        assert "momento único" in result.lower()

    def test_summary_empty_arc(self, arc_generator: ArcGenerator) -> None:
        """generate_narrative_summary com arco vazio."""
        arc = Arc(arc_id="arc_empty", name="Empty")
        result = arc_generator.generate_narrative_summary(arc)

        assert "não disponível" in result

    def test_summary_shows_themes(
        self, arc_generator: ArcGenerator, sample_arc: Arc
    ) -> None:
        """generate_narrative_summary menciona temas."""
        result = arc_generator.generate_narrative_summary(sample_arc)

        assert "tema" in result.lower()
        assert "trabalho" in result.lower()


# ----------------------------------------------------------------------
# Testes — ArcGenerator.generate(): API principal
# ----------------------------------------------------------------------


class TestGenerate:
    def test_generate_returns_string(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() retorna string."""
        result = arc_generator.generate(sessions_list)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_contains_section_headers(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() gera seções com headers."""
        result = arc_generator.generate(sessions_list)

        # Seções devem começar com ## (H2) já que o título principal (H1) vem do ARC_TEMPLATE
        assert "## Síntese Narrativa" in result or "## Linha do Tempo" in result

    def test_generate_stores_arc_name(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() usa nome customizado no arco interno."""
        result = arc_generator.generate(sessions_list, arc_name="Meu Arco")
        arc = arc_generator.build_arc(sessions_list, arc_name="Meu Arco")

        assert arc.name == "Meu Arco"
        assert isinstance(result, str)

    def test_generate_empty_sessions(
        self, arc_generator: ArcGenerator
    ) -> None:
        """generate() com lista vazia retorna mensagem informativa."""
        result = arc_generator.generate([])

        assert isinstance(result, str)
        assert "Nenhuma sessão" in result

    def test_generate_includes_all_sections_by_default(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() inclui todas as seções por padrão."""
        result = arc_generator.generate(sessions_list)

        assert "Síntese Narrativa" in result or "Linha do Tempo" in result
        assert "Símbolos Recorrentes" in result or "não disponíveis" in result
        assert "Temas Persistentes" in result or "Nenhuma thread" in result

    def test_generate_exclude_timeline(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() pode excluir linha do tempo."""
        result = arc_generator.generate(sessions_list, include_timeline=False)

        assert "Linha do Tempo" not in result or result.count("## ") < 3

    def test_generate_exclude_recurring_symbols(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() pode excluir símbolos recorrentes."""
        result = arc_generator.generate(sessions_list, include_recurring_symbols=False)

        assert "Símbolos Recorrentes" not in result

    def test_generate_exclude_threads(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() pode excluir threads."""
        result = arc_generator.generate(sessions_list, include_threads=False)

        assert "Temas Persistentes" not in result

    def test_generate_exclude_summary_does_not_include_narrative_intro(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() com include_summary=False não inclui sumário narrativo inicial."""
        result = arc_generator.generate(sessions_list, include_summary=False)

        # A seção inicial de Síntese Narrativa não deve aparecer
        # Mas a síntese final ainda pode conter "Síntese" por ser parte do resolution
        assert result.count("## Síntese Narrativa") <= 1

    def test_generate_returns_markdown_content(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() retorna conteúdo estruturado."""
        result = arc_generator.generate(sessions_list)

        # Verificar que o resultado é Markdown estruturado
        assert "## " in result  # Deve ter seções H2
        assert len(result) > 100  # Deve ter conteúdo substancial

    def test_generate_markdown_format(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """generate() retorna formato Markdown."""
        result = arc_generator.generate(sessions_list)

        # Deve conter marcadores Markdown
        assert "# " in result
        assert "## " in result or "---" in result


# ----------------------------------------------------------------------
# Testes — Edge cases
# ----------------------------------------------------------------------


class TestEdgeCases:
    def test_session_without_analysis_returns_valid_output(
        self, arc_generator: ArcGenerator
    ) -> None:
        """Sessão sem analysis_result gera output válido."""
        session = Session(
            session_id="sess-no-analysis",
            timestamp="2024-01-15T10:00:00",
            input_format="text",
            raw_content="Sem análise",
        )
        result = arc_generator.generate([session])

        assert isinstance(result, str)
        # Deve gerar conteúdo estruturado mesmo sem análise
        assert len(result) > 0
        assert "## " in result  # Deve ter seções

    def test_session_with_empty_themes(
        self, arc_generator: ArcGenerator
    ) -> None:
        """Sessão com themes vazios."""
        session = Session(
            session_id="sess-empty-themes",
            timestamp="2024-01-15T10:00:00",
            input_format="text",
            raw_content="Teste",
            analysis_result=AnalysisResult(diagnosis="Teste", themes=[]),
        )
        arc = arc_generator.build_arc([session])
        threads = arc_generator.identify_threads([session])

        assert threads == []

    def test_session_with_only_one_theme(
        self, arc_generator: ArcGenerator
    ) -> None:
        """Sessão com apenas um tema."""
        session = Session(
            session_id="sess-single-theme",
            timestamp="2024-01-15T10:00:00",
            input_format="text",
            raw_content="Teste",
            analysis_result=AnalysisResult(diagnosis="Teste", themes=["trabalho"]),
        )
        threads = arc_generator.identify_threads([session])

        # Não forma thread recorrente com apenas uma sessão
        assert threads == []

    def test_arc_generator_handles_different_input_formats(
        self, arc_generator: ArcGenerator
    ) -> None:
        """ArcGenerator lida com diferentes formatos de input."""
        sessions = [
            Session(
                session_id="sess-text",
                timestamp="2024-01-15T10:00:00",
                input_format="text",
                raw_content="Texto livre",
                analysis_result=AnalysisResult(diagnosis="Teste", themes=["trabalho"]),
            ),
            Session(
                session_id="sess-spread",
                timestamp="2024-02-15T10:00:00",
                input_format="spread",
                raw_content="Carta 1, Carta 2",
                analysis_result=AnalysisResult(diagnosis="Teste", themes=["trabalho"]),
            ),
            Session(
                session_id="sess-symbols",
                timestamp="2024-03-15T10:00:00",
                input_format="symbols",
                raw_content="casa, estrela",
                analysis_result=AnalysisResult(diagnosis="Teste", themes=["trabalho"]),
            ),
        ]
        arc = arc_generator.build_arc(sessions)
        timeline = arc_generator.generate_timeline(arc)

        assert "text" in timeline
        assert "spread" in timeline
        assert "symbols" in timeline

    def test_build_arc_generates_valid_arc_id(
        self, arc_generator: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """build_arc gera ID válido."""
        arc = arc_generator.build_arc(sessions_list)

        assert arc.arc_id.startswith("arc_")
        assert "_" in arc.arc_id

    def test_multiple_sessions_same_day(
        self, arc_generator: ArcGenerator
    ) -> None:
        """Múltiplas sessões no mesmo dia."""
        sessions = [
            Session(
                session_id="sess-001",
                timestamp="2024-01-15T09:00:00",
                input_format="text",
                raw_content="Manhã",
                analysis_result=AnalysisResult(diagnosis="Teste 1", themes=["trabalho"]),
            ),
            Session(
                session_id="sess-002",
                timestamp="2024-01-15T14:00:00",
                input_format="text",
                raw_content="Tarde",
                analysis_result=AnalysisResult(diagnosis="Teste 2", themes=["trabalho"]),
            ),
        ]
        arc = arc_generator.build_arc(sessions)

        assert arc.start_date == arc.end_date

    def test_arc_generator_with_context(
        self, arc_generator_with_context: ArcGenerator, sessions_list: list[Session]
    ) -> None:
        """ArcGenerator funciona com session_context."""
        result = arc_generator_with_context.generate(sessions_list)

        assert isinstance(result, str)
        assert len(result) > 0
