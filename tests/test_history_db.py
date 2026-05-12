"""Testes unitários para src/history_db.py.

Cobertura:
- HistoryDB — inicialização, caminhos de arquivos
- save_session() — salvar sessão no banco de dados
- load_session() — carregar sessão pelo ID
- list_sessions() — listar sessões, com e sem filtro de tag
- add_annotation() — adicionar anotação a uma sessão
- delete_session() — remover sessão do banco
- SessionNotFoundError — erros quando sessão não existe
- HistoryDBError — erros genéricos do banco
"""

import tempfile
from pathlib import Path
from typing import Optional

import pytest

from src.history_db import (
    HistoryDB,
    HistoryDBError,
    SessionNotFoundError,
)
from src.types import (
    AnalysisResult,
    Arc,
    ChapterSummary,
    NarrativeThread,
    Session,
    SessionAnnotation,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def temp_data_dir():
    """Cria diretório temporário para dados e o remove ao final."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def db(temp_data_dir: Path) -> HistoryDB:
    """HistoryDB conectado a diretório temporário."""
    return HistoryDB(data_dir=temp_data_dir)


@pytest.fixture
def sample_session() -> Session:
    """Cria uma sessão de exemplo."""
    return Session(
        session_id="session-001",
        timestamp="2026-01-15T10:30:00",
        input_format="text",
        raw_content="Estou preocupado com meu trabalho",
        analysis_result=AnalysisResult(
            diagnosis="Preocupação com estabilidade profissional",
            themes=["trabalho", "insegurança"],
            risks=["burnout", "conflito com chefia"],
            decisions=["Buscar capacitação", "Conversar com gestor"],
            practical_plan="Agendar reunião com gestor para esclarecer expectativas",
        ),
        unresolved_threads=["trabalho-2026"],
        annotations=[],
    )


@pytest.fixture
def sample_session_2() -> Session:
    """Cria uma segunda sessão de exemplo."""
    return Session(
        session_id="session-002",
        timestamp="2026-01-20T14:00:00",
        input_format="symbols",
        raw_content="casa,estrela,coração",
        analysis_result=AnalysisResult(
            diagnosis="Análise simbólica positiva",
            themes=["lar", "esperança", "amor"],
            risks=[],
            decisions=["Decidir com calma"],
            practical_plan="Refletir sobre prioridades",
        ),
        unresolved_threads=["relacionamento"],
        annotations=[],
    )


@pytest.fixture
def sample_annotation() -> SessionAnnotation:
    """Cria uma anotação de exemplo."""
    return SessionAnnotation(
        annotation_id="ann-001",
        session_id="session-001",
        milestone_id="milestone-reflect-1",
        content="Após refletir, percebo que o problema é mais sobre controle do que trabalho.",
        timestamp="2026-01-15T11:00:00",
        theme_tags=["trabalho", "autoconhecimento"],
        linked_thread_ids=["trabalho-2026"],
        is_milestone_completed=True,
    )


# ----------------------------------------------------------------------
# Testes — Inicialização
# ----------------------------------------------------------------------


class TestHistoryDBInit:
    def test_default_data_dir_is_home_based(self) -> None:
        """Diretório padrão deve ser ~/.local/share/clareza/sessions."""
        db = HistoryDB()
        expected = Path.home() / ".local" / "share" / "clareza" / "sessions"
        assert db.data_dir == expected

    def test_custom_data_dir(self, temp_data_dir: Path) -> None:
        """Diretório customizado é usado quando especificado."""
        db = HistoryDB(data_dir=temp_data_dir)
        assert db.data_dir == temp_data_dir

    def test_data_dir_created_if_missing(self, temp_data_dir: Path) -> None:
        """Diretório é criado automaticamente se não existir."""
        nested = temp_data_dir / "nested" / "path"
        db = HistoryDB(data_dir=nested)
        assert nested.exists()
        assert nested.is_dir()


# ----------------------------------------------------------------------
# Testes — save_session() e load_session()
# ----------------------------------------------------------------------


class TestSaveAndLoadSession:
    def test_save_session_creates_file(self, db: HistoryDB, sample_session: Session) -> None:
        """Sessão salva deve criar arquivo JSON no diretório de dados."""
        db.save_session(sample_session)
        session_path = db.data_dir / f"{sample_session.session_id}.json"
        assert session_path.exists()
        assert session_path.is_file()

    def test_save_and_load_session_roundtrip(self, db: HistoryDB, sample_session: Session) -> None:
        """Sessão pode ser salva e carregada sem perda de dados."""
        db.save_session(sample_session)
        loaded = db.load_session(sample_session.session_id)

        assert loaded.session_id == sample_session.session_id
        assert loaded.timestamp == sample_session.timestamp
        assert loaded.input_format == sample_session.input_format
        assert loaded.raw_content == sample_session.raw_content
        assert loaded.unresolved_threads == sample_session.unresolved_threads

    def test_load_session_with_analysis_result(self, db: HistoryDB, sample_session: Session) -> None:
        """Sessão com analysis_result é carregada corretamente."""
        db.save_session(sample_session)
        loaded = db.load_session(sample_session.session_id)

        assert loaded.analysis_result is not None
        assert loaded.analysis_result.diagnosis == sample_session.analysis_result.diagnosis
        assert loaded.analysis_result.themes == sample_session.analysis_result.themes
        assert loaded.analysis_result.risks == sample_session.analysis_result.risks
        assert loaded.analysis_result.decisions == sample_session.analysis_result.decisions
        assert loaded.analysis_result.practical_plan == sample_session.analysis_result.practical_plan

    def test_load_nonexistent_session_raises(self, db: HistoryDB) -> None:
        """Carregar sessão inexistente levanta SessionNotFoundError."""
        with pytest.raises(SessionNotFoundError) as exc_info:
            db.load_session("nonexistent-id")
        assert exc_info.value.session_id == "nonexistent-id"

    def test_save_multiple_sessions(self, db: HistoryDB, sample_session: Session, sample_session_2: Session) -> None:
        """Múltiplas sessões podem ser salvas e carregadas independentemente."""
        db.save_session(sample_session)
        db.save_session(sample_session_2)

        loaded_1 = db.load_session(sample_session.session_id)
        loaded_2 = db.load_session(sample_session_2.session_id)

        assert loaded_1.session_id == sample_session.session_id
        assert loaded_2.session_id == sample_session_2.session_id
        assert loaded_1.raw_content != loaded_2.raw_content

    def test_update_existing_session(self, db: HistoryDB, sample_session: Session) -> None:
        """Sessão existente pode ser atualizada (sobrescreve dados)."""
        db.save_session(sample_session)

        # Modificar e salvar novamente
        sample_session.raw_content = "Conteúdo atualizado"
        sample_session.unresolved_threads.append("nova-thread")
        db.save_session(sample_session)

        loaded = db.load_session(sample_session.session_id)
        assert loaded.raw_content == "Conteúdo atualizado"
        assert "nova-thread" in loaded.unresolved_threads

    def test_get_session_returns_none_for_missing(self, db: HistoryDB) -> None:
        """get_session() retorna None para sessão inexistente."""
        result = db.get_session("missing-id")
        assert result is None


# ----------------------------------------------------------------------
# Testes — list_sessions()
# ----------------------------------------------------------------------


class TestListSessions:
    def test_list_empty_db_returns_empty_list(self, db: HistoryDB) -> None:
        """Banco vazio retorna lista vazia."""
        result = db.list_sessions()
        assert result == []

    def test_list_sessions_returns_all(self, db: HistoryDB, sample_session: Session, sample_session_2: Session) -> None:
        """list_sessions() retorna todas as sessões salvas."""
        db.save_session(sample_session)
        db.save_session(sample_session_2)

        result = db.list_sessions()

        assert len(result) == 2
        session_ids = [s["session_id"] for s in result]
        assert sample_session.session_id in session_ids
        assert sample_session_2.session_id in session_ids

    def test_list_sessions_includes_metadata(self, db: HistoryDB, sample_session: Session) -> None:
        """list_sessions() retorna metadados de cada sessão."""
        db.save_session(sample_session)

        result = db.list_sessions()

        assert len(result) == 1
        session_data = result[0]
        assert "session_id" in session_data
        assert "timestamp" in session_data
        assert "input_format" in session_data
        assert session_data["session_id"] == sample_session.session_id
        assert session_data["timestamp"] == sample_session.timestamp
        assert session_data["input_format"] == sample_session.input_format

    def test_list_sessions_sorted_by_timestamp(self, db: HistoryDB, sample_session: Session, sample_session_2: Session) -> None:
        """list_sessions() ordena por timestamp (mais recente primeiro)."""
        db.save_session(sample_session)  # 2026-01-15
        db.save_session(sample_session_2)  # 2026-01-20

        result = db.list_sessions()

        # session-002 é mais recente
        assert result[0]["session_id"] == sample_session_2.session_id
        assert result[1]["session_id"] == sample_session.session_id

    def test_list_sessions_filtered_by_tag_in_themes(self, db: HistoryDB, sample_session: Session, sample_session_2: Session) -> None:
        """list_sessions(tag) filtra por tag em themes do analysis_result."""
        db.save_session(sample_session)  # themes: trabalho, insegurança
        db.save_session(sample_session_2)  # themes: lar, esperança, amor

        result = db.list_sessions(tag="trabalho")

        assert len(result) == 1
        assert result[0]["session_id"] == sample_session.session_id

    def test_list_sessions_case_insensitive_tag(self, db: HistoryDB, sample_session: Session) -> None:
        """Filtragem por tag é case-insensitive."""
        db.save_session(sample_session)

        result_lower = db.list_sessions(tag="trabalho")
        result_upper = db.list_sessions(tag="TRABALHO")
        result_mixed = db.list_sessions(tag="TrAbAlHo")

        assert len(result_lower) == 1
        assert len(result_upper) == 1
        assert len(result_mixed) == 1
        assert result_lower[0]["session_id"] == result_upper[0]["session_id"]
        assert result_lower[0]["session_id"] == result_mixed[0]["session_id"]

    def test_list_sessions_filter_partial_tag_match(self, db: HistoryDB, sample_session: Session) -> None:
        """Tag pode fazer match parcial no theme."""
        db.save_session(sample_session)

        # "trab" faz match parcial com "trabalho"
        result = db.list_sessions(tag="inseg")
        assert len(result) == 1

    def test_list_sessions_no_match_returns_empty(self, db: HistoryDB, sample_session: Session) -> None:
        """Tag sem matches retorna lista vazia."""
        db.save_session(sample_session)

        result = db.list_sessions(tag="inexistente")
        assert result == []


# ----------------------------------------------------------------------
# Testes — add_annotation()
# ----------------------------------------------------------------------


class TestAddAnnotation:
    def test_add_annotation_to_session(self, db: HistoryDB, sample_session: Session) -> None:
        """Anotação pode ser adicionada a uma sessão existente."""
        db.save_session(sample_session)

        annotation = db.add_annotation(
            session_id=sample_session.session_id,
            content="Minha reflexão sobre o trabalho.",
            milestone_id="milestone-1",
            theme_tags=["trabalho"],
        )

        assert annotation.session_id == sample_session.session_id
        assert annotation.content == "Minha reflexão sobre o trabalho."
        assert annotation.milestone_id == "milestone-1"
        assert annotation.theme_tags == ["trabalho"]
        assert annotation.is_milestone_completed is False

    def test_add_annotation_creates_id(self, db: HistoryDB, sample_session: Session) -> None:
        """Anotação recebe ID único."""
        db.save_session(sample_session)

        annotation = db.add_annotation(
            session_id=sample_session.session_id,
            content="Reflexão",
        )

        assert annotation.annotation_id is not None
        assert len(annotation.annotation_id) > 0
        assert annotation.session_id in annotation.annotation_id

    def test_add_annotation_adds_timestamp(self, db: HistoryDB, sample_session: Session) -> None:
        """Anotação recebe timestamp ao ser criada."""
        db.save_session(sample_session)

        annotation = db.add_annotation(
            session_id=sample_session.session_id,
            content="Reflexão com timestamp",
        )

        assert annotation.timestamp is not None
        assert len(annotation.timestamp) > 0

    def test_add_annotation_to_nonexistent_session_raises(self, db: HistoryDB) -> None:
        """Anotar sessão inexistente levanta SessionNotFoundError."""
        with pytest.raises(SessionNotFoundError):
            db.add_annotation(
                session_id="inexistente",
                content="Reflexão",
            )

    def test_add_annotation_with_milestone_completed(self, db: HistoryDB, sample_session: Session) -> None:
        """Anotação pode indicar milestone como concluído."""
        db.save_session(sample_session)

        annotation = db.add_annotation(
            session_id=sample_session.session_id,
            content="Concluí o milestone",
            is_milestone_completed=True,
        )

        assert annotation.is_milestone_completed is True

    def test_add_multiple_annotations(self, db: HistoryDB, sample_session: Session) -> None:
        """Múltiplas anotações podem ser adicionadas à mesma sessão."""
        db.save_session(sample_session)

        ann1 = db.add_annotation(session_id=sample_session.session_id, content="Primeira reflexão")
        ann2 = db.add_annotation(session_id=sample_session.session_id, content="Segunda reflexão")

        assert ann1.annotation_id != ann2.annotation_id
        assert ann1.content != ann2.content

    def test_annotation_with_linked_threads(self, db: HistoryDB, sample_session: Session) -> None:
        """Anotação pode ter threads narrativas vinculadas."""
        db.save_session(sample_session)

        annotation = db.add_annotation(
            session_id=sample_session.session_id,
            content="Reflexão conectada",
            linked_thread_ids=["thread-1", "thread-2"],
        )

        assert annotation.linked_thread_ids == ["thread-1", "thread-2"]

    def test_get_annotations_for_session(self, db: HistoryDB, sample_session: Session, sample_session_2: Session) -> None:
        """get_annotations_for_session retorna anotações da sessão especificada."""
        db.save_session(sample_session)
        db.save_session(sample_session_2)

        db.add_annotation(session_id=sample_session.session_id, content="Anotação 1")
        db.add_annotation(session_id=sample_session.session_id, content="Anotação 2")
        db.add_annotation(session_id=sample_session_2.session_id, content="Anotação 3")

        annotations = db.get_annotations_for_session(sample_session.session_id)
        assert len(annotations) == 2

    def test_get_completed_milestones(self, db: HistoryDB, sample_session: Session) -> None:
        """get_completed_milestones retorna IDs de milestones concluídos."""
        db.save_session(sample_session)

        db.add_annotation(
            session_id=sample_session.session_id,
            content="Milestone 1",
            milestone_id="milestone-1",
            is_milestone_completed=True,
        )
        db.add_annotation(
            session_id=sample_session.session_id,
            content="Milestone 2",
            milestone_id="milestone-2",
            is_milestone_completed=False,
        )
        db.add_annotation(
            session_id=sample_session.session_id,
            content="Milestone 3",
            milestone_id="milestone-3",
            is_milestone_completed=True,
        )

        completed = db.get_completed_milestones()
        assert len(completed) == 2
        assert "milestone-1" in completed
        assert "milestone-3" in completed
        assert "milestone-2" not in completed


# ----------------------------------------------------------------------
# Testes — delete_session()
# ----------------------------------------------------------------------


class TestDeleteSession:
    def test_delete_session_removes_file(self, db: HistoryDB, sample_session: Session) -> None:
        """delete_session() remove o arquivo da sessão."""
        db.save_session(sample_session)
        session_path = db.data_dir / f"{sample_session.session_id}.json"

        assert session_path.exists()
        db.delete_session(sample_session.session_id)
        assert not session_path.exists()

    def test_delete_session_updates_index(self, db: HistoryDB, sample_session: Session) -> None:
        """delete_session() remove sessão do índice."""
        db.save_session(sample_session)
        assert db.get_session_count() == 1

        db.delete_session(sample_session.session_id)
        assert db.get_session_count() == 0

    def test_delete_nonexistent_session_raises(self, db: HistoryDB) -> None:
        """Remover sessão inexistente levanta SessionNotFoundError."""
        with pytest.raises(SessionNotFoundError):
            db.delete_session("inexistente")


# ----------------------------------------------------------------------
# Testes — get_session_count()
# ----------------------------------------------------------------------


class TestGetSessionCount:
    def test_empty_db_has_zero_sessions(self, db: HistoryDB) -> None:
        """Banco vazio retorna 0 sessões."""
        assert db.get_session_count() == 0

    def test_count_increases_with_sessions(self, db: HistoryDB, sample_session: Session, sample_session_2: Session) -> None:
        """Contagem aumenta ao adicionar sessões."""
        assert db.get_session_count() == 0

        db.save_session(sample_session)
        assert db.get_session_count() == 1

        db.save_session(sample_session_2)
        assert db.get_session_count() == 2

    def test_count_decreases_after_delete(self, db: HistoryDB, sample_session: Session, sample_session_2: Session) -> None:
        """Contagem diminui após remover sessão."""
        db.save_session(sample_session)
        db.save_session(sample_session_2)
        assert db.get_session_count() == 2

        db.delete_session(sample_session.session_id)
        assert db.get_session_count() == 1


# ----------------------------------------------------------------------
# Testes — clear_all()
# ----------------------------------------------------------------------


class TestClearAll:
    def test_clear_all_removes_all_files(self, db: HistoryDB, sample_session: Session, sample_session_2: Session) -> None:
        """clear_all() remove todos os arquivos JSON."""
        db.save_session(sample_session)
        db.save_session(sample_session_2)
        db.save_threads([NarrativeThread(thread_id="t1", name="Thread 1", theme="tema", session_ids=[])])
        db.save_annotations([])

        assert db.get_session_count() == 2

        db.clear_all()

        assert db.get_session_count() == 0
        assert db.load_threads() == []
        assert db.load_annotations() == []

    def test_clear_all_on_empty_db(self, db: HistoryDB) -> None:
        """clear_all() funciona em banco vazio."""
        db.clear_all()
        assert db.get_session_count() == 0


# ----------------------------------------------------------------------
# Testes — threads narrativas
# ----------------------------------------------------------------------


class TestNarrativeThreads:
    def test_save_and_load_threads(self, db: HistoryDB) -> None:
        """Threads podem ser salvas e carregadas."""
        threads = [
            NarrativeThread(
                thread_id="t1",
                name="Trabalho",
                theme="carreira",
                session_ids=["s1", "s2"],
                status="active",
                first_mention="2026-01-01",
                last_mention="2026-01-15",
                progression=["situação inicial", "ação tomada"],
            )
        ]

        db.save_threads(threads)
        loaded = db.load_threads()

        assert len(loaded) == 1
        assert loaded[0].thread_id == "t1"
        assert loaded[0].name == "Trabalho"
        assert loaded[0].theme == "carreira"
        assert loaded[0].session_ids == ["s1", "s2"]

    def test_load_threads_empty_db_returns_empty_list(self, db: HistoryDB) -> None:
        """Banco vazio retorna lista vazia de threads."""
        assert db.load_threads() == []

    def test_save_empty_threads(self, db: HistoryDB) -> None:
        """Lista vazia de threads pode ser salva."""
        db.save_threads([])
        assert db.load_threads() == []


# ----------------------------------------------------------------------
# Testes — arcos narrativos
# ----------------------------------------------------------------------


class TestArcs:
    def test_save_and_load_arcs(self, db: HistoryDB, sample_session: Session) -> None:
        """Arcos podem ser salvos e carregados."""
        db.save_session(sample_session)

        arcs = [
            Arc(
                arc_id="arc-1",
                name="Jornada de 2026",
                sessions=[sample_session],
                threads=[],
                start_date="2026-01-01",
                dominant_themes=["trabalho"],
            )
        ]

        db.save_arcs(arcs)
        loaded = db.load_arcs()

        assert len(loaded) == 1
        assert loaded[0].arc_id == "arc-1"
        assert loaded[0].name == "Jornada de 2026"
        assert len(loaded[0].sessions) == 1
        assert loaded[0].sessions[0].session_id == sample_session.session_id

    def test_load_arcs_empty_db_returns_empty_list(self, db: HistoryDB) -> None:
        """Banco vazio retorna lista vazia de arcos."""
        assert db.load_arcs() == []


# ----------------------------------------------------------------------
# Testes — capítulos
# ----------------------------------------------------------------------


class TestChapters:
    def test_save_and_load_chapters(self, db: HistoryDB) -> None:
        """Capítulos podem ser salvos e carregados."""
        chapters = [
            ChapterSummary(
                chapter_number=1,
                title="Primeiro Capítulo",
                arc_id="arc-1",
                sessions_covered=["s1", "s2"],
                narrative_summary="Resumo do capítulo",
                unresolved_threads=["thread-1"],
                escalation_detected=False,
                resolution_detected=True,
                key_insight="Insight principal",
            )
        ]

        db.save_chapters(chapters)
        loaded = db.load_chapters()

        assert len(loaded) == 1
        assert loaded[0].chapter_number == 1
        assert loaded[0].title == "Primeiro Capítulo"
        assert loaded[0].narrative_summary == "Resumo do capítulo"
        assert loaded[0].key_insight == "Insight principal"

    def test_load_chapters_empty_db_returns_empty_list(self, db: HistoryDB) -> None:
        """Banco vazio retorna lista vazia de capítulos."""
        assert db.load_chapters() == []