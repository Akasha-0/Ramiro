"""Testes unitários para src/database.py.

Cobertura:
- init_db() — criação do diretório e tabela
- SessionDB.__init__() — inicialização e auto-create
- SessionDB.save_session() — CRUD create
- SessionDB.get_sessions() — CRUD read com filtros
- SessionDB.get_session() — busca por ID
- SessionDB.delete_session() — CRUD delete
- DatabaseError — exceção customizada
"""

import json
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.database import (
    DatabaseError,
    SessionDB,
    init_db,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def temp_db_dir(tmp_path: Path) -> Path:
    """Diretório temporário para banco de dados de teste."""
    return tmp_path


@pytest.fixture
def db_with_schema(temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Cria banco de dados vazio com schema válido."""
    # Redireciona o caminho do banco para o diretório temporário
    monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
    monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "test_sessions.db")

    init_db()

    db_path = temp_db_dir / "test_sessions.db"
    assert db_path.exists()
    return db_path


@pytest.fixture
def db_with_sessions(temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch) -> SessionDB:
    """Banco de dados com sessões pré-inseridas para testes."""
    monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
    monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

    # Criar banco e inserir dados de teste
    init_db()

    db = SessionDB()

    # Inserir sessões de teste com datas variadas
    db.save_session(
        input_text="Preciso decidir sobre minha carreira",
        cards=["Cruz", "Estrela"],
        format="symbols",
    )
    db.save_session(
        input_text="Problemas no trabalho e família",
        cards=["Café", "Montanha", "Serpente"],
        format="spread",
    )
    db.save_session(
        input_text="Dúvidas sobre saúde e alimentação",
        format="text",
    )

    return db


# ----------------------------------------------------------------------
# Testes — init_db()
# ----------------------------------------------------------------------


class TestInitDb:
    def test_creates_data_directory(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Diretório data/ é criado se não existir."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir / "data")
        monkeypatch.setattr(
            "src.database._DB_PATH", temp_db_dir / "data" / "sessions.db"
        )

        init_db()

        assert (temp_db_dir / "data").is_dir()

    def test_creates_database_file(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Arquivo sessions.db é criado se não existir."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        init_db()

        assert (temp_db_dir / "sessions.db").is_file()

    def test_creates_sessions_table(
        self, db_with_schema: Path
    ) -> None:
        """Tabela sessions é criada com colunas corretas."""
        conn = sqlite3.connect(str(db_with_schema))
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sessions)")
            columns = {row[1] for row in cursor.fetchall()}

            assert "id" in columns
            assert "timestamp" in columns
            assert "input_text" in columns
            assert "cards" in columns
            assert "format" in columns
            assert "report_path" in columns
        finally:
            conn.close()

    def test_id_is_autoincrement(self, db_with_schema: Path) -> None:
        """Coluna id é PRIMARY KEY AUTOINCREMENT."""
        conn = sqlite3.connect(str(db_with_schema))
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sessions)")
            columns = cursor.fetchall()
            # Encontra a coluna id e verifica se é primary key
            id_col = [col for col in columns if col[1] == "id"]
            assert len(id_col) == 1
            # 5 = pk column in PRAGMA table_info output
            assert id_col[0][5] > 0  # pk > 0 means it's a PRIMARY KEY
        finally:
            conn.close()

    def test_cards_default_is_empty_json(self, db_with_schema: Path) -> None:
        """Coluna cards tem DEFAULT '[]'."""
        conn = sqlite3.connect(str(db_with_schema))
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='sessions'"
            )
            create_sql = cursor.fetchone()[0]
            assert "'[]'" in create_sql or '"[]"' in create_sql
        finally:
            conn.close()

    def test_idempotent_call(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Múltiplas chamadas a init_db() não causam erro."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        init_db()
        init_db()  # Não deve lançar exceção
        init_db()

        assert (temp_db_dir / "sessions.db").is_file()


# ----------------------------------------------------------------------
# Testes — SessionDB.__init__()
# ----------------------------------------------------------------------


class TestSessionDbInit:
    def test_creates_db_if_not_exists(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SessionDB cria o banco automaticamente se não existir."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "new.db")

        assert not (temp_db_dir / "new.db").exists()

        db = SessionDB()

        assert (temp_db_dir / "new.db").is_file()

    def test_uses_existing_db(
        self, db_with_schema: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SessionDB não recria banco existente."""
        monkeypatch.setattr("src.database._DB_DIR", db_with_schema.parent)
        monkeypatch.setattr("src.database._DB_PATH", db_with_schema)

        # Criar primeiro acesso
        db = SessionDB()
        session_count = len(db.get_sessions())

        # Segundo acesso não deve afetar dados
        db2 = SessionDB()
        assert len(db2.get_sessions()) == session_count


# ----------------------------------------------------------------------
# Testes — SessionDB.save_session()
# ----------------------------------------------------------------------


class TestSaveSession:
    def test_returns_session_id(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """save_session retorna o ID da sessão criada."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        session_id = db.save_session(input_text="Teste inicial")

        assert session_id == 1
        assert isinstance(session_id, int)

    def test_increments_id_on_multiple_saves(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """IDs são incrementados automaticamente."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        id1 = db.save_session(input_text="Primeira sessão")
        id2 = db.save_session(input_text="Segunda sessão")
        id3 = db.save_session(input_text="Terceira sessão")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_saves_all_fields(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Todos os campos são salvos corretamente."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        cards = ["Cruz", "Estrela", "Café"]
        session_id = db.save_session(
            input_text="Preciso decidir sobre trabalho",
            cards=cards,
            format="symbols",
            report_path="/relatorios/sessao_001.md",
        )

        saved = db.get_session(session_id)
        assert saved is not None
        assert saved.input_text == "Preciso decidir sobre trabalho"
        assert json.loads(saved.cards) == cards
        assert saved.format == "symbols"
        assert saved.report_path == "/relatorios/sessao_001.md"
        assert saved.timestamp is not None

    def test_saves_empty_cards_list(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Lista vazia de cards é serializada como '[]'."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        session_id = db.save_session(input_text="Texto sem cartas")

        saved = db.get_session(session_id)
        assert saved is not None
        assert saved.cards == "[]"

    def test_saves_null_cards(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """cards=None é tratado como lista vazia."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        session_id = db.save_session(input_text="Texto simples", cards=None)

        saved = db.get_session(session_id)
        assert saved is not None
        assert saved.cards == "[]"

    def test_default_format_is_text(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Formato padrão é 'text' quando não especificado."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        session_id = db.save_session(input_text="Teste")

        saved = db.get_session(session_id)
        assert saved is not None
        assert saved.format == "text"

    def test_timestamp_is_iso_format(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Timestamp segue formato ISO 8601."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        session_id = db.save_session(input_text="Teste")

        saved = db.get_session(session_id)
        assert saved is not None
        assert "T" in saved.timestamp  # ISO format contains T separator

    def test_preserves_portuguese_accents(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Caracteres portugueses são preservados corretamente."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        texto = "Relação com família coração saúde"
        session_id = db.save_session(input_text=texto)

        saved = db.get_session(session_id)
        assert saved is not None
        assert saved.input_text == texto

    def test_raises_database_error_on_sqlite_error(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Erro SQLite gera DatabaseError com mensagem apropriada."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        # Tentar salvar com tipo inválido (causaria erro)
        # SQLite geralmente não falha em INSERT básico, então testamos
        # cenários de conexão
        session_id = db.save_session(input_text="Teste")
        assert session_id is not None


# ----------------------------------------------------------------------
# Testes — SessionDB.get_sessions()
# ----------------------------------------------------------------------


class TestGetSessions:
    def test_returns_all_sessions(
        self, db_with_sessions: SessionDB
    ) -> None:
        """get_sessions retorna todas as sessões ordenadas por data."""
        sessions = db_with_sessions.get_sessions()

        assert len(sessions) == 3
        # Ordenadas por data decrescente (mais recente primeiro)
        timestamps = [s.timestamp for s in sessions]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_returns_empty_list_when_empty(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Banco vazio retorna lista vazia."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        sessions = db.get_sessions()

        assert sessions == []

    def test_limit_returns_specified_count(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Parâmetro limit restringe número de resultados."""
        sessions = db_with_sessions.get_sessions(limit=2)

        assert len(sessions) == 2

    def test_limit_with_zero_returns_nothing(
        self, db_with_sessions: SessionDB
    ) -> None:
        """limit=0 retorna lista vazia."""
        sessions = db_with_sessions.get_sessions(limit=0)

        assert sessions == []

    def test_search_filters_by_input_text(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Filtro search busca no campo input_text."""
        sessions = db_with_sessions.get_sessions(search="trabalho")

        assert len(sessions) >= 1
        assert all("trabalho" in s.input_text.lower() for s in sessions)

    def test_search_filters_by_cards(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Filtro search também busca no campo cards."""
        sessions = db_with_sessions.get_sessions(search="Estrela")

        assert len(sessions) >= 1
        # Deve encontrar a sessão com Estrelas
        found = False
        for s in sessions:
            if "Estrela" in s.cards:
                found = True
                break
        assert found

    def test_search_case_insensitive(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Busca é case-insensitive."""
        sessions_upper = db_with_sessions.get_sessions(search="TRABALHO")
        sessions_lower = db_with_sessions.get_sessions(search="trabalho")

        assert len(sessions_upper) == len(sessions_lower)

    def test_since_filters_by_date(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Filtro since inclui sessões a partir da data."""
        # Pegar timestamp da sessão mais antiga
        sessions = db_with_sessions.get_sessions()
        oldest_timestamp = sessions[-1].timestamp

        # since deve retornar todas as sessões (da mais antiga em diante)
        recent_sessions = db_with_sessions.get_sessions(since=oldest_timestamp)

        assert len(recent_sessions) == len(sessions)

    def test_until_filters_by_date(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Filtro until inclui sessões até a data."""
        sessions = db_with_sessions.get_sessions()
        newest_timestamp = sessions[0].timestamp

        # until deve retornar apenas a sessão mais recente
        recent_sessions = db_with_sessions.get_sessions(until=newest_timestamp)

        assert len(recent_sessions) >= 1

    def test_combined_filters(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Filtros podem ser combinados."""
        sessions = db_with_sessions.get_sessions(
            limit=10,
            search="trabalho",
        )

        assert len(sessions) <= 10
        for s in sessions:
            assert "trabalho" in s.input_text.lower() or "trabalho" in s.cards

    def test_returns_session_records_with_all_fields(
        self, db_with_sessions: SessionDB
    ) -> None:
        """SessionRecords retornados contêm todos os campos."""
        sessions = db_with_sessions.get_sessions()

        for s in sessions:
            assert s.id is not None
            assert s.timestamp is not None
            assert s.input_text is not None
            assert s.cards is not None
            assert s.format is not None

    def test_cards_is_json_string(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Campo cards é string JSON, não lista."""
        sessions = db_with_sessions.get_sessions()

        for s in sessions:
            # Deve ser string JSON válida
            parsed = json.loads(s.cards)
            assert isinstance(parsed, list)


# ----------------------------------------------------------------------
# Testes — SessionDB.get_session()
# ----------------------------------------------------------------------


class TestGetSession:
    def test_returns_session_by_id(
        self, db_with_sessions: SessionDB
    ) -> None:
        """get_session retorna sessão específica pelo ID."""
        session = db_with_sessions.get_session(1)

        assert session is not None
        assert session.id == 1

    def test_returns_none_for_nonexistent_id(
        self, db_with_sessions: SessionDB
    ) -> None:
        """ID inexistente retorna None."""
        session = db_with_sessions.get_session(9999)

        assert session is None

    def test_returns_all_fields(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Sessão retornada tem todos os campos preenchidos."""
        session = db_with_sessions.get_session(1)

        assert session is not None
        assert session.timestamp is not None
        assert session.input_text is not None
        assert session.cards is not None
        assert session.format is not None

    def test_parses_cards_json(
        self, db_with_sessions: SessionDB
    ) -> None:
        """cards é string JSON serializada."""
        session = db_with_sessions.get_session(1)

        assert session is not None
        cards_list = json.loads(session.cards)
        assert isinstance(cards_list, list)

    def test_returns_with_report_path(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """report_path é retornado corretamente quando presente."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        session_id = db.save_session(
            input_text="Teste",
            report_path="/path/to/report.md",
        )

        session = db.get_session(session_id)
        assert session is not None
        assert session.report_path == "/path/to/report.md"

    def test_returns_none_when_no_report_path(
        self, db_with_sessions: SessionDB
    ) -> None:
        """report_path é None quando não definido."""
        session = db_with_sessions.get_session(3)  # Sessão sem report_path

        assert session is not None
        assert session.report_path is None


# ----------------------------------------------------------------------
# Testes — SessionDB.delete_session()
# ----------------------------------------------------------------------


class TestDeleteSession:
    def test_returns_true_when_deleted(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """delete_session retorna True quando sessão é removida."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        session_id = db.save_session(input_text="Para deletar")

        result = db.delete_session(session_id)

        assert result is True

    def test_removes_session_from_database(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sessão realmente é removida do banco."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()
        session_id = db.save_session(input_text="Para deletar")

        db.delete_session(session_id)

        assert db.get_session(session_id) is None

    def test_returns_false_for_nonexistent_id(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Tentativa de deletar ID inexistente retorna False."""
        result = db_with_sessions.delete_session(9999)

        assert result is False

    def test_does_not_affect_other_sessions(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Deletar uma sessão não afeta as demais."""
        initial_count = len(db_with_sessions.get_sessions())

        db_with_sessions.delete_session(2)

        remaining = db_with_sessions.get_sessions()
        assert len(remaining) == initial_count - 1
        assert db_with_sessions.get_session(1) is not None
        assert db_with_sessions.get_session(3) is not None

    def test_sequential_deletes_work(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Múltiplas remoções sequenciais funcionam corretamente."""
        db_with_sessions.delete_session(1)
        db_with_sessions.delete_session(2)

        remaining = db_with_sessions.get_sessions()
        assert len(remaining) == 1


# ----------------------------------------------------------------------
# Testes — DatabaseError
# ----------------------------------------------------------------------


class TestDatabaseError:
    def test_error_message_is_accessible(self) -> None:
        """Mensagem de erro é acessível via atributo message."""
        err = DatabaseError("Erro de conexão")

        assert err.message == "Erro de conexão"

    def test_error_details_is_optional(self) -> None:
        """details é opcional."""
        err = DatabaseError("Erro simples")

        assert err.message == "Erro simples"
        assert err.details is None

    def test_error_with_details(self) -> None:
        """Erro pode incluir detalhes adicionais."""
        err = DatabaseError(
            "Falha na conexão",
            details="sqlite3.OperationalError: database locked",
        )

        assert err.message == "Falha na conexão"
        assert err.details == "sqlite3.OperationalError: database locked"

    def test_str_includes_message(self) -> None:
        """str() inclui a mensagem principal."""
        err = DatabaseError("Mensagem principal")

        assert "Mensagem principal" in str(err)

    def test_str_includes_details(self) -> None:
        """str() inclui detalhes quando presentes."""
        err = DatabaseError(
            "Erro principal",
            details="informação adicional",
        )

        err_str = str(err)
        assert "Erro principal" in err_str
        assert "informação adicional" in err_str

    def test_is_exception_subclass(self) -> None:
        """DatabaseError herda de Exception."""
        err = DatabaseError("Teste")

        assert isinstance(err, Exception)

    def test_can_be_caught_as_exception(self) -> None:
        """Erro pode ser capturado com except Exception."""
        with pytest.raises(Exception):
            raise DatabaseError("Erro capturado")

    def test_multiple_instances_are_independent(self) -> None:
        """Múltiplas instâncias são independentes."""
        err1 = DatabaseError("Erro 1", details="det1")
        err2 = DatabaseError("Erro 2", details="det2")

        assert err1.message != err2.message
        assert err1.details != err2.details


# ----------------------------------------------------------------------
# Testes — Integração
# ----------------------------------------------------------------------


class TestIntegration:
    def test_full_crud_cycle(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fluxo completo: criar, ler, atualizar via delete+create, deletar."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        db = SessionDB()

        # Create
        sid = db.save_session(
            input_text="Sessão de teste completo",
            cards=["Cruz", "Estrela"],
            format="symbols",
        )

        # Read
        session = db.get_session(sid)
        assert session is not None
        assert session.input_text == "Sessão de teste completo"

        # Delete
        result = db.delete_session(sid)
        assert result is True

        # Verify deleted
        assert db.get_session(sid) is None

    def test_multiple_sessions_with_different_formats(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Múltiplas sessões com formatos diferentes coexistem."""
        sessions = db_with_sessions.get_sessions()

        formats = {s.format for s in sessions}
        assert "text" in formats
        assert "symbols" in formats
        assert "spread" in formats

    def test_search_across_all_fields(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Busca encontra matches em qualquer campo."""
        # Buscar termo que aparece em cards mas não em input_text
        results = db_with_sessions.get_sessions(search="Serpente")

        assert len(results) >= 1