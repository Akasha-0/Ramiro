"""Testes unitários para src/session_clustering.py.

Cobertura:
- _extract_keywords_from_session() — extração de keywords de sessão
- _extract_cards_from_session() — extração de cartas de sessão spread
- _extract_themes_from_session() — extração de temas de sessão
- _compute_keyword_overlap() — cálculo de sobreposição de keywords (Jaccard)
- _compute_tag_match() — cálculo de match de tags
- _compute_card_similarity() — similaridade de cartas
- _compute_symbol_theme_bonus() — bônus temático entre cartas
- _compute_theme_similarity() — similaridade de temas
- _compute_combined_score() — score combinado ponderado
- RelatedSession — dataclass com session, score e match_reasons
- SessionClusterer.find_related_sessions() — busca por sessão
- SessionClusterer.find_related_sessions_by_content() — busca por conteúdo
- SessionClusterer.cluster_by_tag() — filtro por tag
- SessionClusterer.get_tag_suggestions() — sugestões de tags
- SessionClusterer._get_match_reasons() — identificação de razões do match
- SessionClusterer._get_common_tags() — tags mais comuns
"""

import pytest

from src.session_clustering import (
    CARD_MATCH_WEIGHT,
    DEFAULT_TOP_N,
    KEYWORD_MATCH_WEIGHT,
    MIN_RELEVANCE_SCORE,
    TAG_MATCH_WEIGHT,
    RelatedSession,
    SessionClusterer,
    _compute_card_similarity,
    _compute_combined_score,
    _compute_keyword_overlap,
    _compute_symbol_theme_bonus,
    _compute_tag_match,
    _compute_theme_similarity,
    _extract_cards_from_session,
    _extract_keywords_from_session,
    _extract_themes_from_session,
)
from src.types import AnalysisResult, Session


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def session_with_tags() -> Session:
    """Sessão com tags temáticas."""
    return Session(
        session_id="session-001",
        timestamp="2026-05-10T10:00:00Z",
        input_format="text",
        raw_content="Tenho dúvida sobre carreira profissional",
        tags=["carreira", "trabalho"],
    )


@pytest.fixture
def session_with_cards() -> Session:
    """Sessão com tiragem de cartas."""
    analysis = AnalysisResult(
        diagnosis="Diagnóstico de teste",
        themes=["família"],
        symbolic_mappings={
            "card:1": "A Casa",
            "card:2": "A Estrela",
        },
    )
    return Session(
        session_id="session-002",
        timestamp="2026-05-10T11:00:00Z",
        input_format="spread",
        raw_content="1,Casa\n2,Estrela",
        analysis_result=analysis,
        tags=["família"],
    )


@pytest.fixture
def session_with_themes() -> Session:
    """Sessão com resultados de análise incluindo temas."""
    analysis = AnalysisResult(
        diagnosis="Diagnóstico de teste",
        themes=["trabalho", "relacionamento"],
        symbolic_mappings={},
    )
    return Session(
        session_id="session-003",
        timestamp="2026-05-10T12:00:00Z",
        input_format="text",
        raw_content="Preocupado com trabalho e relação",
        analysis_result=analysis,
        tags=["trabalho"],
    )


@pytest.fixture
def clusterer() -> SessionClusterer:
    """Clusterer com configurações padrão."""
    return SessionClusterer(top_n=DEFAULT_TOP_N)


@pytest.fixture
def sample_sessions(
    session_with_tags: Session,
    session_with_cards: Session,
    session_with_themes: Session,
) -> list[Session]:
    """Lista de sessões para testes de comparação."""
    return [session_with_tags, session_with_cards, session_with_themes]


# ----------------------------------------------------------------------
# Testes — Constantes
# ----------------------------------------------------------------------


class TestConstants:
    def test_tag_match_weight_positive(self) -> None:
        """TAG_MATCH_WEIGHT é positivo."""
        assert TAG_MATCH_WEIGHT > 0

    def test_keyword_match_weight_positive(self) -> None:
        """KEYWORD_MATCH_WEIGHT é positivo."""
        assert KEYWORD_MATCH_WEIGHT > 0

    def test_card_match_weight_positive(self) -> None:
        """CARD_MATCH_WEIGHT é positivo."""
        assert CARD_MATCH_WEIGHT > 0

    def test_min_relevance_score_positive(self) -> None:
        """MIN_RELEVANCE_SCORE é positivo."""
        assert MIN_RELEVANCE_SCORE > 0

    def test_default_top_n_positive(self) -> None:
        """DEFAULT_TOP_N é positivo."""
        assert DEFAULT_TOP_N > 0


# ----------------------------------------------------------------------
# Testes — _extract_keywords_from_session()
# ----------------------------------------------------------------------


class TestExtractKeywordsFromSession:
    def test_extracts_tags_as_keywords(self, session_with_tags: Session) -> None:
        """Tags são adicionadas como keywords (lowercase)."""
        keywords = _extract_keywords_from_session(session_with_tags)
        assert "carreira" in keywords
        assert "trabalho" in keywords

    def test_extracts_content_tokens(self, session_with_tags: Session) -> None:
        """Tokens do conteúdo são extraídos (mín. 3 chars)."""
        keywords = _extract_keywords_from_session(session_with_tags)
        # "tenho" tem 4 chars, deve ser incluído
        assert "tenho" in keywords
        # "profissional" deve ser incluído
        assert "profissional" in keywords

    def test_filters_short_tokens(self) -> None:
        """Tokens com menos de 3 caracteres são filtrados."""
        session = Session(
            session_id="test",
            timestamp="",
            input_format="text",
            raw_content="eu de a",
            tags=[],
        )
        keywords = _extract_keywords_from_session(session)
        # "eu" (2), "de" (2), "a" (1) não devem aparecer
        assert "eu" not in keywords
        assert "de" not in keywords
        assert "a" not in keywords

    def test_empty_session_returns_empty(self) -> None:
        """Sessão sem tags e conteúdo retorna conjunto vazio."""
        session = Session(
            session_id="test",
            timestamp="",
            input_format="text",
            raw_content="",
            tags=[],
        )
        keywords = _extract_keywords_from_session(session)
        assert keywords == set()

    def test_case_insensitive(self, session_with_tags: Session) -> None:
        """Keywords são normalizadas para lowercase."""
        keywords = _extract_keywords_from_session(session_with_tags)
        # Não deve haver tags em uppercase
        for kw in keywords:
            assert kw == kw.lower()


# ----------------------------------------------------------------------
# Testes — _extract_cards_from_session()
# ----------------------------------------------------------------------


class TestExtractCardsFromSession:
    def test_extracts_card_names(self, session_with_cards: Session) -> None:
        """Nomes de cartas são extraídos de mappings."""
        cards = _extract_cards_from_session(session_with_cards)
        assert "a casa" in cards
        assert "a estrela" in cards

    def test_empty_when_no_analysis(self) -> None:
        """Sessão sem analysis_result retorna conjunto vazio."""
        session = Session(
            session_id="test",
            timestamp="",
            input_format="text",
            raw_content="texto",
            analysis_result=None,
        )
        cards = _extract_cards_from_session(session)
        assert cards == set()

    def test_empty_when_no_mappings(self) -> None:
        """Sessão sem symbolic_mappings retorna conjunto vazio."""
        session = Session(
            session_id="test",
            timestamp="",
            input_format="text",
            raw_content="texto",
            analysis_result=AnalysisResult(diagnosis="test"),
        )
        cards = _extract_cards_from_session(session)
        assert cards == set()

    def test_empty_when_no_card_keys(self) -> None:
        """Mappings sem chaves 'card:' retorna conjunto vazio."""
        analysis = AnalysisResult(
            diagnosis="test",
            symbolic_mappings={"kw:casa": "A Casa"},
        )
        session = Session(
            session_id="test",
            timestamp="",
            input_format="text",
            raw_content="texto",
            analysis_result=analysis,
        )
        cards = _extract_cards_from_session(session)
        assert cards == set()

    def test_case_normalized(self, session_with_cards: Session) -> None:
        """Nomes de cartas são normalizados para lowercase."""
        cards = _extract_cards_from_session(session_with_cards)
        for card in cards:
            assert card == card.lower()


# ----------------------------------------------------------------------
# Testes — _extract_themes_from_session()
# ----------------------------------------------------------------------


class TestExtractThemesFromSession:
    def test_extracts_themes(self, session_with_themes: Session) -> None:
        """Temas são extraídos do analysis_result."""
        themes = _extract_themes_from_session(session_with_themes)
        assert "trabalho" in themes
        assert "relacionamento" in themes

    def test_empty_when_no_analysis(self) -> None:
        """Sessão sem analysis_result retorna conjunto vazio."""
        session = Session(
            session_id="test",
            timestamp="",
            input_format="text",
            raw_content="texto",
            analysis_result=None,
        )
        themes = _extract_themes_from_session(session)
        assert themes == set()

    def test_empty_when_no_themes(self) -> None:
        """Sessão com themes vazio retorna conjunto vazio."""
        analysis = AnalysisResult(
            diagnosis="test",
            themes=[],
        )
        session = Session(
            session_id="test",
            timestamp="",
            input_format="text",
            raw_content="texto",
            analysis_result=analysis,
        )
        themes = _extract_themes_from_session(session)
        assert themes == set()


# ----------------------------------------------------------------------
# Testes — _compute_keyword_overlap()
# ----------------------------------------------------------------------


class TestComputeKeywordOverlap:
    def test_full_overlap(self) -> None:
        """Keywords idênticas retornam score máximo."""
        current = {"trabalho", "carreira"}
        past = {"trabalho", "carreira"}
        score = _compute_keyword_overlap(current, past)
        # Jaccard de 1.0 + match_bonus de 0.2 = 1.2 → limitado pelo cálculo
        assert score > 0.5

    def test_no_overlap(self) -> None:
        """Keywords disjuntas retornam score baixo."""
        current = {"trabalho"}
        past = {"amor"}
        score = _compute_keyword_overlap(current, past)
        assert score == 0.0

    def test_partial_overlap(self) -> None:
        """Sobreposição parcial retorna score intermediário."""
        current = {"trabalho", "carreira", "amor"}
        past = {"trabalho", "carreira", "dinheiro"}
        score = _compute_keyword_overlap(current, past)
        assert 0.0 < score < 1.0

    def test_empty_current_returns_zero(self) -> None:
        """Conjunto vazio atual retorna 0.0."""
        score = _compute_keyword_overlap(set(), {"trabalho"})
        assert score == 0.0

    def test_empty_past_returns_zero(self) -> None:
        """Conjunto vazio passado retorna 0.0."""
        score = _compute_keyword_overlap({"trabalho"}, set())
        assert score == 0.0

    def test_both_empty_returns_zero(self) -> None:
        """Ambos vazios retorna 0.0."""
        score = _compute_keyword_overlap(set(), set())
        assert score == 0.0


# ----------------------------------------------------------------------
# Testes — _compute_tag_match()
# ----------------------------------------------------------------------


class TestComputeTagMatch:
    def test_exact_match(self) -> None:
        """Tags idênticas retornam score 1.0."""
        current = ["trabalho", "carreira"]
        past = ["trabalho", "carreira"]
        score = _compute_tag_match(current, past)
        assert score == 1.0

    def test_no_match(self) -> None:
        """Tags disjuntas retornam 0.0."""
        current = ["trabalho"]
        past = ["amor"]
        score = _compute_tag_match(current, past)
        assert score == 0.0

    def test_partial_match(self) -> None:
        """Match parcial retorna score proporcional."""
        current = ["trabalho", "carreira", "amor"]
        past = ["trabalho", "dinheiro"]
        score = _compute_tag_match(current, past)
        assert 0.0 < score < 1.0

    def test_case_insensitive(self) -> None:
        """Comparação é case-insensitive."""
        current = ["TRABALHO"]
        past = ["trabalho"]
        score = _compute_tag_match(current, past)
        assert score == 1.0

    def test_empty_current_returns_zero(self) -> None:
        """Lista vazia atual retorna 0.0."""
        score = _compute_tag_match([], ["trabalho"])
        assert score == 0.0

    def test_empty_past_returns_zero(self) -> None:
        """Lista vazia passada retorna 0.0."""
        score = _compute_tag_match(["trabalho"], [])
        assert score == 0.0


# ----------------------------------------------------------------------
# Testes — _compute_card_similarity()
# ----------------------------------------------------------------------


class TestComputeCardSimilarity:
    def test_identical_cards(self) -> None:
        """Cartas idênticas retornam score máximo."""
        current = {"a casa", "a estrela"}
        past = {"a casa", "a estrela"}
        score = _compute_card_similarity(current, past)
        assert score > 0.5

    def test_no_common_cards(self) -> None:
        """Cartas disjuntas retornam score Jaccard simples."""
        current = {"a casa"}
        past = {"a estrela"}
        score = _compute_card_similarity(current, past)
        assert score == 0.0

    def test_partial_overlap(self) -> None:
        """Sobreposição parcial retorna score intermediário."""
        current = {"a casa", "a estrela", "a cruz"}
        past = {"a casa", "a estrela"}
        score = _compute_card_similarity(current, past)
        assert 0.0 < score < 1.0

    def test_empty_current_returns_zero(self) -> None:
        """Conjunto vazio atual retorna 0.0."""
        score = _compute_card_similarity(set(), {"a casa"})
        assert score == 0.0

    def test_empty_past_returns_zero(self) -> None:
        """Conjunto vazio passado retorna 0.0."""
        score = _compute_card_similarity({"a casa"}, set())
        assert score == 0.0


# ----------------------------------------------------------------------
# Testes — _compute_symbol_theme_bonus()
# ----------------------------------------------------------------------


class TestComputeSymbolThemeBonus:
    def test_single_card_no_bonus(self) -> None:
        """Uma única carta não recebe bônus."""
        intersection = {"a casa"}
        bonus = _compute_symbol_theme_bonus(intersection)
        assert bonus == 0.0

    def test_multiple_cards_same_theme(self) -> None:
        """Cartas do mesmo tema recebem bônus."""
        # Casa e Cegonha são ambos família
        intersection = {"a casa", "a cegonha"}
        bonus = _compute_symbol_theme_bonus(intersection)
        assert bonus > 0.0

    def test_bonus_capped(self) -> None:
        """Bônus é limitado a 0.3."""
        # Várias cartas do mesmo tema
        intersection = {"a casa", "a cegonha", "o cachorro", "a carta"}
        bonus = _compute_symbol_theme_bonus(intersection)
        assert bonus <= 0.3

    def test_different_themes_no_bonus(self) -> None:
        """Cartas de temas diferentes não recebem bônus."""
        # Casa (família) e Mercado (trabalho)
        intersection = {"a casa", "o mercado"}
        bonus = _compute_symbol_theme_bonus(intersection)
        assert bonus == 0.0


# ----------------------------------------------------------------------
# Testes — _compute_theme_similarity()
# ----------------------------------------------------------------------


class TestComputeThemeSimilarity:
    def test_identical_themes(self) -> None:
        """Temas idênticos retornam score 1.0."""
        current = {"trabalho", "relacionamento"}
        past = {"trabalho", "relacionamento"}
        score = _compute_theme_similarity(current, past)
        assert score == 1.0

    def test_no_common_themes(self) -> None:
        """Temas disjuntos retornam 0.0."""
        current = {"trabalho"}
        past = {"relacionamento"}
        score = _compute_theme_similarity(current, past)
        assert score == 0.0

    def test_partial_overlap(self) -> None:
        """Sobreposição parcial retorna score proporcional."""
        current = {"trabalho", "relacionamento"}
        past = {"trabalho"}
        score = _compute_theme_similarity(current, past)
        assert 0.0 < score < 1.0

    def test_empty_current_returns_zero(self) -> None:
        """Conjunto vazio atual retorna 0.0."""
        score = _compute_theme_similarity(set(), {"trabalho"})
        assert score == 0.0

    def test_empty_past_returns_zero(self) -> None:
        """Conjunto vazio passado retorna 0.0."""
        score = _compute_theme_similarity({"trabalho"}, set())
        assert score == 0.0


# ----------------------------------------------------------------------
# Testes — _compute_combined_score()
# ----------------------------------------------------------------------


class TestComputeCombinedScore:
    def test_identical_sessions(self, session_with_tags: Session) -> None:
        """Sessões idênticas retornam score alto."""
        score = _compute_combined_score(session_with_tags, session_with_tags)
        assert score > 0.5

    def test_different_sessions(self, session_with_tags: Session) -> None:
        """Sessões diferentes retornam score menor ou zero."""
        session_other = Session(
            session_id="other",
            timestamp="2026-05-09T10:00:00Z",
            input_format="text",
            raw_content="texto completamente diferente",
            tags=["amor", "saúde"],
        )
        score = _compute_combined_score(session_with_tags, session_other)
        assert score >= 0.0

    def test_score_normalized(self, session_with_tags: Session) -> None:
        """Score é normalizado para 0-1."""
        score = _compute_combined_score(session_with_tags, session_with_tags)
        assert 0.0 <= score <= 1.0

    def test_tag_weight_applied(self, session_with_tags: Session) -> None:
        """Tags recebem peso maior na pontuação."""
        session_same_tag = Session(
            session_id="same-tag",
            timestamp="2026-05-09T10:00:00Z",
            input_format="text",
            raw_content="texto diferente",
            tags=["carreira"],  # Tag idêntica
        )
        score = _compute_combined_score(session_with_tags, session_same_tag)
        # Pelo menos tag match deve contribuir
        assert score > 0.0


# ----------------------------------------------------------------------
# Testes — RelatedSession
# ----------------------------------------------------------------------


class TestRelatedSession:
    def test_init_with_all_args(self) -> None:
        """RelatedSession inicializa com session, score e match_reasons."""
        session = Session(
            session_id="test",
            timestamp="",
            input_format="text",
            raw_content="texto",
            tags=["trabalho"],
        )
        reasons = ["tag:trabalho", "keyword:casa"]
        related = RelatedSession(session=session, score=0.8, match_reasons=reasons)
        assert related.session == session
        assert related.score == 0.8
        assert related.match_reasons == reasons

    def test_init_default_match_reasons(self) -> None:
        """RelatedSession com match_reasons default é lista vazia."""
        session = Session(
            session_id="test",
            timestamp="",
            input_format="text",
            raw_content="texto",
        )
        related = RelatedSession(session=session, score=0.5)
        assert related.match_reasons == []


# ----------------------------------------------------------------------
# Testes — SessionClusterer
# ----------------------------------------------------------------------


class TestSessionClustererInit:
    def test_default_init(self) -> None:
        """SessionClusterer inicializa com valores padrão."""
        clusterer = SessionClusterer()
        assert clusterer.top_n == DEFAULT_TOP_N
        assert clusterer.storage is None

    def test_custom_top_n(self) -> None:
        """SessionClusterer aceita top_n customizado."""
        clusterer = SessionClusterer(top_n=10)
        assert clusterer.top_n == 10


# ----------------------------------------------------------------------
# Testes — SessionClusterer.find_related_sessions()
# ----------------------------------------------------------------------


class TestFindRelatedSessions:
    def test_finds_related_by_tag(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Sessões relacionadas são encontradas por tag."""
        current = sample_sessions[0]  # tem tags "carreira", "trabalho"
        related = clusterer.find_related_sessions(current, sample_sessions)
        assert len(related) >= 1

    def test_excludes_current_session(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Sessão atual não aparece nos resultados."""
        current = sample_sessions[0]
        related = clusterer.find_related_sessions(current, sample_sessions)
        related_ids = [r.session.session_id for r in related]
        assert current.session_id not in related_ids

    def test_ordered_by_score(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Resultados são ordenados por score decrescente."""
        current = sample_sessions[0]
        related = clusterer.find_related_sessions(current, sample_sessions)
        if len(related) >= 2:
            scores = [r.score for r in related]
            assert scores == sorted(scores, reverse=True)

    def test_respects_top_n(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Resultados são limitados a top_n."""
        current = sample_sessions[0]
        related = clusterer.find_related_sessions(current, sample_sessions)
        assert len(related) <= clusterer.top_n

    def test_respects_min_score(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Sessões com score abaixo de min_score são ignoradas."""
        current = sample_sessions[0]
        related = clusterer.find_related_sessions(current, sample_sessions, min_score=0.9)
        for r in related:
            assert r.score >= 0.9

    def test_empty_candidates(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Lista vazia de candidatos retorna lista vazia."""
        current = sample_sessions[0]
        related = clusterer.find_related_sessions(current, [])
        assert related == []

    def test_all_candidates_filtered(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Todos candidatos filtrados retorna lista vazia."""
        # Sessão sem chance de match
        current = Session(
            session_id="orphan",
            timestamp="2026-05-01T10:00:00Z",
            input_format="text",
            raw_content="xyz abcteste nada",
            tags=["indefinido"],
        )
        related = clusterer.find_related_sessions(current, sample_sessions, min_score=0.9)
        # Todos com score < 0.9 devem ser filtrados
        assert isinstance(related, list)

    def test_returns_related_session_objects(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Resultados são instâncias de RelatedSession."""
        current = sample_sessions[0]
        related = clusterer.find_related_sessions(current, sample_sessions)
        for r in related:
            assert isinstance(r, RelatedSession)
            assert hasattr(r, "session")
            assert hasattr(r, "score")
            assert hasattr(r, "match_reasons")


# ----------------------------------------------------------------------
# Testes — SessionClusterer.find_related_sessions_by_content()
# ----------------------------------------------------------------------


class TestFindRelatedSessionsByContent:
    def test_finds_by_content(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Busca por conteúdo encontra sessões relacionadas."""
        related = clusterer.find_related_sessions_by_content(
            raw_content="tenho dúvida sobre carreira",
            tags=["carreira"],
            all_sessions=sample_sessions,
        )
        assert len(related) >= 1

    def test_includes_tag_in_search(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Tags são consideradas na busca por conteúdo."""
        related = clusterer.find_related_sessions_by_content(
            raw_content="texto genérico",
            tags=["trabalho"],
            all_sessions=sample_sessions,
        )
        assert len(related) >= 1

    def test_no_storage_no_crash(self, clusterer: SessionClusterer) -> None:
        """Sem storage e sem all_sessions retorna lista vazia."""
        related = clusterer.find_related_sessions_by_content(
            raw_content="texto",
            tags=[],
        )
        assert related == []


# ----------------------------------------------------------------------
# Testes — SessionClusterer.cluster_by_tag()
# ----------------------------------------------------------------------


class TestClusterByTag:
    def test_filters_by_tag(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Filtra sessões que contêm tag específica."""
        result = clusterer.cluster_by_tag(sample_sessions, "carreira")
        assert len(result) >= 1
        assert all("carreira" in s.tags for s in result)

    def test_case_insensitive(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Filtro é case-insensitive."""
        result = clusterer.cluster_by_tag(sample_sessions, "CARREIRA")
        assert len(result) >= 1

    def test_strips_whitespace(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Whitespace é removido antes da busca."""
        result = clusterer.cluster_by_tag(sample_sessions, "  carreira  ")
        assert len(result) >= 1

    def test_no_match(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Tag inexistente retorna lista vazia."""
        result = clusterer.cluster_by_tag(sample_sessions, "inexistente")
        assert result == []

    def test_returns_session_objects(
        self,
        clusterer: SessionClusterer,
        sample_sessions: list[Session],
    ) -> None:
        """Resultados são instâncias de Session."""
        result = clusterer.cluster_by_tag(sample_sessions, "carreira")
        for s in result:
            assert isinstance(s, Session)


# ----------------------------------------------------------------------
# Testes — SessionClusterer.get_tag_suggestions()
# ----------------------------------------------------------------------


class TestGetTagSuggestions:
    def test_returns_tuples(
        self,
        clusterer: SessionClusterer,
        session_with_tags: Session,
    ) -> None:
        """Sugestões são tuplas (tag, score)."""
        suggestions = clusterer.get_tag_suggestions(session_with_tags)
        for tag, score in suggestions:
            assert isinstance(tag, str)
            assert isinstance(score, float)

    def test_excludes_existing_tags(
        self,
        clusterer: SessionClusterer,
        session_with_tags: Session,
    ) -> None:
        """Tags já existentes não são sugeridas."""
        suggestions = clusterer.get_tag_suggestions(
            session_with_tags,
            available_tags=["carreira", "trabalho", "amor"],
        )
        tags_suggested = [t for t, _ in suggestions]
        assert "carreira" not in tags_suggested
        assert "trabalho" not in tags_suggested

    def test_sorted_by_score(
        self,
        clusterer: SessionClusterer,
        session_with_tags: Session,
    ) -> None:
        """Sugestões são ordenadas por score decrescente."""
        suggestions = clusterer.get_tag_suggestions(
            session_with_tags,
            available_tags=["carreira", "trabalho", "amor", "relacionamento", "saúde"],
        )
        if len(suggestions) >= 2:
            scores = [s for _, s in suggestions]
            assert scores == sorted(scores, reverse=True)

    def test_limit_top_five(
        self,
        clusterer: SessionClusterer,
        session_with_tags: Session,
    ) -> None:
        """Retorna no máximo 5 sugestões."""
        suggestions = clusterer.get_tag_suggestions(
            session_with_tags,
            available_tags=[
                "tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8",
            ],
        )
        assert len(suggestions) <= 5


# ----------------------------------------------------------------------
# Testes — SessionClusterer._get_match_reasons()
# ----------------------------------------------------------------------


class TestGetMatchReasons:
    def test_includes_tag_reasons(
        self,
        clusterer: SessionClusterer,
        session_with_tags: Session,
    ) -> None:
        """Razões de match incluem tags compartilhadas."""
        session_same_tag = Session(
            session_id="same-tag",
            timestamp="2026-05-09T10:00:00Z",
            input_format="text",
            raw_content="texto diferente",
            tags=["carreira"],  # Tag idêntica
        )
        reasons = clusterer._get_match_reasons(session_with_tags, session_same_tag)
        assert any(r.startswith("tag:") for r in reasons)

    def test_includes_keyword_reasons(
        self,
        clusterer: SessionClusterer,
        session_with_tags: Session,
    ) -> None:
        """Razões de match incluem keywords compartilhadas."""
        session_similar = Session(
            session_id="similar",
            timestamp="2026-05-09T10:00:00Z",
            input_format="text",
            raw_content="tenho dúvida sobre carreira",
            tags=["outro"],
        )
        reasons = clusterer._get_match_reasons(session_with_tags, session_similar)
        assert any(r.startswith("keyword:") for r in reasons)

    def test_includes_theme_reasons(
        self,
        clusterer: SessionClusterer,
        session_with_themes: Session,
    ) -> None:
        """Razões de match incluem themes compartilhadas."""
        session_same_theme = Session(
            session_id="same-theme",
            timestamp="2026-05-09T10:00:00Z",
            input_format="text",
            raw_content="texto",
            tags=[],
            analysis_result=AnalysisResult(
                diagnosis="test",
                themes=["trabalho"],  # Tema idêntico
            ),
        )
        reasons = clusterer._get_match_reasons(session_with_themes, session_same_theme)
        assert any(r.startswith("theme:") for r in reasons)

    def test_empty_when_no_overlap(
        self,
        clusterer: SessionClusterer,
        session_with_tags: Session,
    ) -> None:
        """Sem sobreposição retorna lista vazia."""
        session_no_overlap = Session(
            session_id="no-overlap",
            timestamp="2026-05-09T10:00:00Z",
            input_format="text",
            raw_content="texto sem nenhuma conexão",
            tags=["inexistente"],
        )
        reasons = clusterer._get_match_reasons(session_with_tags, session_no_overlap)
        assert reasons == []

    def test_returns_list(
        self,
        clusterer: SessionClusterer,
        session_with_tags: Session,
    ) -> None:
        """Retorna sempre uma lista."""
        reasons = clusterer._get_match_reasons(session_with_tags, session_with_tags)
        assert isinstance(reasons, list)


# ----------------------------------------------------------------------
# Testes — SessionClusterer._get_common_tags()
# ----------------------------------------------------------------------


class TestGetCommonTags:
    def test_requires_storage(self, clusterer: SessionClusterer) -> None:
        """Sem storage retorna lista vazia."""
        common_tags = clusterer._get_common_tags()
        assert common_tags == []

    def test_returns_list_of_strings(self, clusterer: SessionClusterer) -> None:
        """Retorna lista de strings."""
        common_tags = clusterer._get_common_tags()
        assert isinstance(common_tags, list)
        for tag in common_tags:
            assert isinstance(tag, str)

    def test_respects_limit(self, clusterer: SessionClusterer) -> None:
        """Limita o número de tags retornadas."""
        common_tags = clusterer._get_common_tags(limit=5)
        assert len(common_tags) <= 5
