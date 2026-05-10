"""Testes unitários para src/arc_summary.py.

Cobertura:
- ArcSummaryGenerator.generate() — geração de sumário completo
- ArcSummaryGenerator._analyze_themes() — análise de frequência de temas
- ArcSummaryGenerator._analyze_cards() — análise de frequência de cartas
- ArcSummaryGenerator._calculate_date_range() — cálculo de range de datas
- ArcSummaryGenerator.get_session_summary() — sumário de sessão individual
- ArcSummaryGenerator.format_themes_summary() — formatação de temas
- ArcSummaryGenerator.format_cards_summary() — formatação de cartas
- Edge cases: lista vazia, sessões sem dados
"""

import pytest
from datetime import datetime

from src.arc_summary import ArcSummaryGenerator
from src.types import ArcSummary, SessionRecord


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def generator() -> ArcSummaryGenerator:
    """Gerador com configurações padrão."""
    return ArcSummaryGenerator()


@pytest.fixture
def generator_custom_top_n() -> ArcSummaryGenerator:
    """Gerador com top_n customizado."""
    return ArcSummaryGenerator(top_n=5)


@pytest.fixture
def sample_session() -> SessionRecord:
    """Sessão de exemplo."""
    return SessionRecord(
        session_id="session-001",
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        arc_name="arco-trabalho",
        input_content="Tenho dúvida sobre trabalho",
        format="text",
        keywords=["trabalho"],
        themes=["trabalho", "carreira"],
        cards=["Estrela", "Cruz"],
        diagnosis="Diagnóstico example",
        risks=["⚠️ Risco: incerteza"],
        decisions=["Decisão: explorar opções"],
    )


@pytest.fixture
def sample_sessions() -> list[SessionRecord]:
    """Lista de sessões de exemplo."""
    return [
        SessionRecord(
            session_id="session-001",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            arc_name="arco-trabalho",
            input_content="Dúvida sobre trabalho",
            format="text",
            keywords=["trabalho"],
            themes=["trabalho", "carreira"],
            cards=["Estrela"],
            diagnosis="Diagnóstico 1",
            risks=[],
            decisions=[],
        ),
        SessionRecord(
            session_id="session-002",
            timestamp=datetime(2024, 1, 22, 14, 0, 0),
            arc_name="arco-trabalho",
            input_content="Preocupação com dinheiro",
            format="text",
            keywords=["dinheiro"],
            themes=["trabalho", "financeiro"],
            cards=["Estrela", "Moeda"],
            diagnosis="Diagnóstico 2",
            risks=["⚠️ Risco financeiro"],
            decisions=["Decisão sobre investimento"],
        ),
        SessionRecord(
            session_id="session-003",
            timestamp=datetime(2024, 2, 1, 9, 0, 0),
            arc_name="arco-trabalho",
            input_content="Escolher entre propostas",
            format="symbols",
            keywords=["escolha"],
            themes=["trabalho"],
            cards=["Cruz", "Estrela", "Casa"],
            diagnosis="Diagnóstico 3",
            risks=[],
            decisions=["Escolher melhor opção"],
        ),
    ]


# ----------------------------------------------------------------------
# Testes — ArcSummaryGenerator.__init__()
# ----------------------------------------------------------------------


class TestArcSummaryGeneratorInit:
    def test_default_top_n(self) -> None:
        """Por padrão top_n é 3."""
        gen = ArcSummaryGenerator()
        assert gen.top_n == 3

    def test_custom_top_n(self) -> None:
        """top_n pode ser configurado."""
        gen = ArcSummaryGenerator(top_n=5)
        assert gen.top_n == 5


# ----------------------------------------------------------------------
# Testes — generate()
# ----------------------------------------------------------------------


class TestGenerate:
    def test_generate_returns_arc_summary(self, generator: ArcSummaryGenerator) -> None:
        """generate retorna ArcSummary completo."""
        sessions = [
            SessionRecord(
                session_id="s1",
                timestamp=datetime(2024, 1, 1),
                arc_name="teste",
                themes=["trabalho"],
                cards=["Estrela"],
            )
        ]
        result = generator.generate(sessions)
        assert isinstance(result, ArcSummary)

    def test_generate_empty_sessions(self, generator: ArcSummaryGenerator) -> None:
        """Lista vazia retorna ArcSummary com valores padrão."""
        result = generator.generate([])
        assert result.arc_name == ""
        assert result.total_sessions == 0
        assert result.top_themes == []
        assert result.top_cards == []
        assert result.session_ids == []
        assert result.date_range is None

    def test_generate_extracts_arc_name(self, generator: ArcSummaryGenerator) -> None:
        """Nome do arco é extraído da primeira sessão."""
        sessions = [
            SessionRecord(
                session_id="s1",
                timestamp=datetime(2024, 1, 1),
                arc_name="meu-arco",
                themes=[],
                cards=[],
            )
        ]
        result = generator.generate(sessions)
        assert result.arc_name == "meu-arco"

    def test_generate_counts_total_sessions(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """total_sessions refleja o número de sessões."""
        result = generator.generate(sample_sessions)
        assert result.total_sessions == 3

    def test_generate_collects_session_ids(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """session_ids contém IDs de todas as sessões."""
        result = generator.generate(sample_sessions)
        assert result.session_ids == ["session-001", "session-002", "session-003"]


# ----------------------------------------------------------------------
# Testes — _analyze_themes()
# ----------------------------------------------------------------------


class TestAnalyzeThemes:
    def test_analyze_themes_returns_dict(self, generator: ArcSummaryGenerator) -> None:
        """Retorna dicionário com estrutura esperada."""
        sessions = [
            SessionRecord(
                session_id="s1",
                timestamp=datetime(2024, 1, 1),
                themes=["trabalho"],
                cards=[],
            )
        ]
        result = generator._analyze_themes(sessions)
        assert isinstance(result, dict)
        assert "top_themes" in result
        assert "theme_counts" in result
        assert "total_themes" in result

    def test_analyze_themes_empty_sessions(self, generator: ArcSummaryGenerator) -> None:
        """Sessões vazias retorna estrutura vazia."""
        result = generator._analyze_themes([])
        assert result["top_themes"] == []
        assert result["theme_counts"] == {}
        assert result["total_themes"] == 0

    def test_analyze_themes_counts_frequency(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Temas são contados corretamente por frequência."""
        result = generator._analyze_themes(sample_sessions)
        # "trabalho" aparece 3 vezes (em todas as sessões)
        assert result["theme_counts"]["trabalho"] == 3
        # "carreira" aparece 1 vez
        assert result["theme_counts"]["carreira"] == 1
        # "financeiro" aparece 1 vez
        assert result["theme_counts"]["financeiro"] == 1

    def test_analyze_themes_returns_top_n(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Retorna apenas top_n temas mais frequentes."""
        result = generator._analyze_themes(sample_sessions)
        assert len(result["top_themes"]) <= generator.top_n
        # "trabalho" é o mais frequente
        assert result["top_themes"][0] == "trabalho"

    def test_analyze_themes_orders_by_frequency(self, generator: ArcSummaryGenerator) -> None:
        """Temas são ordenados por frequência decrescente."""
        sessions = [
            SessionRecord(session_id="s1", timestamp=datetime(2024, 1, 1), themes=["a", "b"], cards=[]),
            SessionRecord(session_id="s2", timestamp=datetime(2024, 1, 2), themes=["a", "c"], cards=[]),
            SessionRecord(session_id="s3", timestamp=datetime(2024, 1, 3), themes=["a"], cards=[]),
        ]
        result = generator._analyze_themes(sessions)
        assert result["top_themes"] == ["a", "b", "c"]

    def test_analyze_themes_total_unique(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """total_themes contém o número de temas únicos."""
        result = generator._analyze_themes(sample_sessions)
        assert result["total_themes"] == 3  # trabalho, carreira, financeiro


# ----------------------------------------------------------------------
# Testes — _analyze_cards()
# ----------------------------------------------------------------------


class TestAnalyzeCards:
    def test_analyze_cards_returns_dict(self, generator: ArcSummaryGenerator) -> None:
        """Retorna dicionário com estrutura esperada."""
        sessions = [
            SessionRecord(
                session_id="s1",
                timestamp=datetime(2024, 1, 1),
                themes=[],
                cards=["Estrela"],
            )
        ]
        result = generator._analyze_cards(sessions)
        assert isinstance(result, dict)
        assert "top_cards" in result
        assert "card_counts" in result
        assert "total_cards" in result

    def test_analyze_cards_empty_sessions(self, generator: ArcSummaryGenerator) -> None:
        """Sessões vazias retorna estrutura vazia."""
        result = generator._analyze_cards([])
        assert result["top_cards"] == []
        assert result["card_counts"] == {}
        assert result["total_cards"] == 0

    def test_analyze_cards_counts_frequency(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Cartas são contadas corretamente por frequência."""
        result = generator._analyze_cards(sample_sessions)
        # "Estrela" aparece 3 vezes (em todas as sessões)
        assert result["card_counts"]["Estrela"] == 3
        # "Cruz" aparece 1 vez
        assert result["card_counts"]["Cruz"] == 1
        # "Moeda" aparece 1 vez
        assert result["card_counts"]["Moeda"] == 1

    def test_analyze_cards_returns_top_n(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Retorna apenas top_n cartas mais frequentes."""
        result = generator._analyze_cards(sample_sessions)
        assert len(result["top_cards"]) <= generator.top_n
        # "Estrela" é a mais frequente
        assert result["top_cards"][0] == "Estrela"

    def test_analyze_cards_orders_by_frequency(self, generator: ArcSummaryGenerator) -> None:
        """Cartas são ordenadas por frequência decrescente."""
        sessions = [
            SessionRecord(session_id="s1", timestamp=datetime(2024, 1, 1), themes=[], cards=["a", "b"]),
            SessionRecord(session_id="s2", timestamp=datetime(2024, 1, 2), themes=[], cards=["a", "c"]),
            SessionRecord(session_id="s3", timestamp=datetime(2024, 1, 3), themes=[], cards=["a"]),
        ]
        result = generator._analyze_cards(sessions)
        assert result["top_cards"] == ["a", "b", "c"]

    def test_analyze_cards_total_unique(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """total_cards contém o número de cartas únicas."""
        result = generator._analyze_cards(sample_sessions)
        assert result["total_cards"] == 4  # Estrela, Cruz, Moeda, Casa


# ----------------------------------------------------------------------
# Testes — _calculate_date_range()
# ----------------------------------------------------------------------


class TestCalculateDateRange:
    def test_calculate_date_range_returns_tuple(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Retorna tupla (início, fim)."""
        result = generator._calculate_date_range(sample_sessions)
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_calculate_date_range_min_max(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Tupla contém data mínima e máxima."""
        result = generator._calculate_date_range(sample_sessions)
        assert result is not None
        start, end = result
        assert start == datetime(2024, 1, 15, 10, 0, 0)
        assert end == datetime(2024, 2, 1, 9, 0, 0)

    def test_calculate_date_range_empty_sessions(self, generator: ArcSummaryGenerator) -> None:
        """Sessões vazias retorna None."""
        result = generator._calculate_date_range([])
        assert result is None

    def test_calculate_date_range_single_session(self, generator: ArcSummaryGenerator) -> None:
        """Sessão única retorna data como início e fim."""
        sessions = [
            SessionRecord(
                session_id="s1",
                timestamp=datetime(2024, 6, 15),
                themes=[],
                cards=[],
            )
        ]
        result = generator._calculate_date_range(sessions)
        assert result is not None
        start, end = result
        assert start == datetime(2024, 6, 15)
        assert end == datetime(2024, 6, 15)

    def test_calculate_date_range_ignores_none_timestamp(self, generator: ArcSummaryGenerator) -> None:
        """Sessões sem timestamp são ignoradas."""
        sessions = [
            SessionRecord(session_id="s1", timestamp=datetime(2024, 1, 1), themes=[], cards=[]),
            SessionRecord(session_id="s2", timestamp=None, themes=[], cards=[]),
        ]
        result = generator._calculate_date_range(sessions)
        assert result is not None
        start, end = result
        assert start == datetime(2024, 1, 1)
        assert end == datetime(2024, 1, 1)


# ----------------------------------------------------------------------
# Testes — get_session_summary()
# ----------------------------------------------------------------------


class TestGetSessionSummary:
    def test_get_session_summary_returns_dict(self, generator: ArcSummaryGenerator, sample_session: SessionRecord) -> None:
        """Retorna dicionário com informações da sessão."""
        result = generator.get_session_summary(sample_session)
        assert isinstance(result, dict)

    def test_get_session_summary_contains_session_id(self, generator: ArcSummaryGenerator, sample_session: SessionRecord) -> None:
        """Dicionário contém session_id."""
        result = generator.get_session_summary(sample_session)
        assert result["session_id"] == "session-001"

    def test_get_session_summary_contains_themes(self, generator: ArcSummaryGenerator, sample_session: SessionRecord) -> None:
        """Dicionário contém themes."""
        result = generator.get_session_summary(sample_session)
        assert result["themes"] == ["trabalho", "carreira"]

    def test_get_session_summary_contains_cards(self, generator: ArcSummaryGenerator, sample_session: SessionRecord) -> None:
        """Dicionário contém cards."""
        result = generator.get_session_summary(sample_session)
        assert result["cards"] == ["Estrela", "Cruz"]

    def test_get_session_summary_has_risks_true(self, generator: ArcSummaryGenerator, sample_session: SessionRecord) -> None:
        """has_risks é True quando há riscos."""
        result = generator.get_session_summary(sample_session)
        assert result["has_risks"] is True
        assert result["risk_count"] == 1

    def test_get_session_summary_has_risks_false(self, generator: ArcSummaryGenerator) -> None:
        """has_risks é False quando não há riscos."""
        session = SessionRecord(
            session_id="s1",
            timestamp=datetime(2024, 1, 1),
            themes=[],
            cards=[],
            risks=[],
        )
        result = generator.get_session_summary(session)
        assert result["has_risks"] is False
        assert result["risk_count"] == 0

    def test_get_session_summary_timestamp_isoformat(self, generator: ArcSummaryGenerator, sample_session: SessionRecord) -> None:
        """timestamp é formatado em ISO."""
        result = generator.get_session_summary(sample_session)
        assert result["timestamp"] == "2024-01-15T10:00:00"

    def test_get_session_summary_none_timestamp(self, generator: ArcSummaryGenerator) -> None:
        """timestamp None resulta em None no resultado."""
        session = SessionRecord(
            session_id="s1",
            timestamp=None,
            themes=[],
            cards=[],
        )
        result = generator.get_session_summary(session)
        assert result["timestamp"] is None


# ----------------------------------------------------------------------
# Testes — format_themes_summary()
# ----------------------------------------------------------------------


class TestFormatThemesSummary:
    def test_format_themes_summary_returns_string(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Retorna string formatada."""
        result = generator.format_themes_summary(sample_sessions)
        assert isinstance(result, str)

    def test_format_themes_summary_contains_header(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Contém header markdown."""
        result = generator.format_themes_summary(sample_sessions)
        assert "### Temas Predominantes" in result

    def test_format_themes_summary_contains_top_theme(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Contém tema mais frequente."""
        result = generator.format_themes_summary(sample_sessions)
        assert "trabalho" in result

    def test_format_themes_summary_empty_sessions(self, generator: ArcSummaryGenerator) -> None:
        """Sessões sem temas retorna mensagem apropriada."""
        result = generator.format_themes_summary([])
        assert "Nenhum tema detectado" in result


# ----------------------------------------------------------------------
# Testes — format_cards_summary()
# ----------------------------------------------------------------------


class TestFormatCardsSummary:
    def test_format_cards_summary_returns_string(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Retorna string formatada."""
        result = generator.format_cards_summary(sample_sessions)
        assert isinstance(result, str)

    def test_format_cards_summary_contains_header(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Contém header markdown."""
        result = generator.format_cards_summary(sample_sessions)
        assert "### Cartas Mais Recorrentes" in result

    def test_format_cards_summary_contains_top_card(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Contém carta mais frequente."""
        result = generator.format_cards_summary(sample_sessions)
        assert "Estrela" in result

    def test_format_cards_summary_empty_sessions(self, generator: ArcSummaryGenerator) -> None:
        """Sessões sem cartas retorna mensagem apropriada."""
        result = generator.format_cards_summary([])
        assert "Nenhuma carta detectada" in result


# ----------------------------------------------------------------------
# Testes de edge cases
# ----------------------------------------------------------------------


class TestEdgeCases:
    def test_generate_with_sessions_no_themes(self, generator: ArcSummaryGenerator) -> None:
        """Sessões sem temas gera sumário válido."""
        sessions = [
            SessionRecord(
                session_id="s1",
                timestamp=datetime(2024, 1, 1),
                arc_name="teste",
                themes=[],
                cards=["Estrela"],
            )
        ]
        result = generator.generate(sessions)
        assert isinstance(result, ArcSummary)
        assert result.top_themes == []

    def test_generate_with_sessions_no_cards(self, generator: ArcSummaryGenerator) -> None:
        """Sessões sem cartas gera sumário válido."""
        sessions = [
            SessionRecord(
                session_id="s1",
                timestamp=datetime(2024, 1, 1),
                arc_name="teste",
                themes=["trabalho"],
                cards=[],
            )
        ]
        result = generator.generate(sessions)
        assert isinstance(result, ArcSummary)
        assert result.top_cards == []

    def test_generate_with_none_arc_name(self, generator: ArcSummaryGenerator) -> None:
        """arc_name None é tratado como string vazia."""
        sessions = [
            SessionRecord(
                session_id="s1",
                timestamp=datetime(2024, 1, 1),
                arc_name=None,
                themes=[],
                cards=[],
            )
        ]
        result = generator.generate(sessions)
        assert result.arc_name == ""

    def test_generate_custom_top_n(self, generator_custom_top_n: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """top_n customizado limita resultados."""
        result = generator_custom_top_n._analyze_themes(sample_sessions)
        assert len(result["top_themes"]) <= 5

    def test_format_themes_with_counts(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Formato inclui contagem de ocorrências."""
        result = generator.format_themes_summary(sample_sessions)
        # trabalho aparece 3 vezes
        assert "3 ocorrência" in result

    def test_format_cards_with_counts(self, generator: ArcSummaryGenerator, sample_sessions: list[SessionRecord]) -> None:
        """Formato inclui contagem de ocorrências."""
        result = generator.format_cards_summary(sample_sessions)
        # Estrela aparece 3 vezes
        assert "3 ocorrência" in result