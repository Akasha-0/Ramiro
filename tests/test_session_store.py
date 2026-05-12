"""Testes unitários para src/session_store.py.

Cobertura:
- SessionStore.__init__() — inicialização, caminhos de storage
- SessionStore.create_session() — criação com/sem ID, validação
- SessionStore.save_session() — persistência de sessão
- SessionStore.get_session() — recuperação por ID
- SessionStore.list_sessions() — ordenação por timestamp
- SessionStore.delete_session() — remoção de sessão
- SessionStore.session_exists() — verificação de existência
- SessionStore.get_session_count() — contagem de sessões
- SessionStore._load() — carregamento de JSON, tratamento de erros
- SessionStore._save() — salvamento de JSON, tratamento de erros
- SessionStore._serialize_sessions() — serialização
- SessionStore._deserialize_sessions() — desserialização com忽略 de sessões inválidas
- SessionStore._session_to_dict() — conversão para dict
- SessionStore._dict_to_session() — conversão de dict para sessão
- StorageError — exceções customizadas
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from clareza.session_store import (
    SessionStore,
    StorageError,
)
from clareza.types import Session


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def temp_storage_dir(tmp_path) -> Path:
    """Diretório temporário para testes de storage."""
    return tmp_path


@pytest.fixture
def session_store(temp_storage_dir) -> SessionStore:
    """SessionStore com storage em diretório temporário."""
    storage_path = temp_storage_dir / "sessions.json"
    return SessionStore(storage_path=str(storage_path), auto_save=True)


@pytest.fixture
def session_store_no_auto(temp_storage_dir) -> SessionStore:
    """SessionStore sem auto_save para testes de persistência manual."""
    storage_path = temp_storage_dir / "sessions_manual.json"
    return SessionStore(storage_path=str(storage_path), auto_save=False)


@pytest.fixture
def sample_session() -> Session:
    """Sessão de exemplo para testes."""
    return Session(
        session_id="test-123",
        timestamp="2024-01-15T10:30:00",
        input_format="text",
        raw_content="Teste de conteúdo",
        analysis_result=None,
        unresolved_threads=[],
        tags=["teste"],
    )


# ----------------------------------------------------------------------
# Testes — StorageError
# ----------------------------------------------------------------------


class TestStorageError:
    def test_storage_error_basic(self) -> None:
        err = StorageError("Erro de teste")
        assert "Erro de teste" in str(err)
        assert err.message == "Erro de teste"
        assert err.operation is None
        assert err.details is None
        assert err.recovery is None

    def test_storage_error_with_operation(self) -> None:
        err = StorageError("Falhou", operation="save")
        err_str = str(err)
        assert "Falhou" in err_str
        assert "save" in err_str

    def test_storage_error_with_details(self) -> None:
        err = StorageError("Erro", details="info adicional")
        assert "info adicional" in str(err)

    def test_storage_error_with_recovery(self) -> None:
        err = StorageError("Erro", recovery="Tente novamente")
        assert "Tente novamente" in str(err)

    def test_storage_error_full(self) -> None:
        err = StorageError("Falhou", operation="load", details="arquivo.json", recovery="Recupere o backup")
        err_str = str(err)
        assert "Falhou" in err_str
        assert "load" in err_str
        assert "arquivo.json" in err_str
        assert "Recupere" in err_str


# ----------------------------------------------------------------------
# Testes — __init__()
# ----------------------------------------------------------------------


class TestInit:
    def test_init_with_custom_path(self, temp_storage_dir) -> None:
        custom_path = temp_storage_dir / "custom_sessions.json"
        store = SessionStore(storage_path=str(custom_path))
        assert store.storage_path == custom_path

    def test_init_creates_parent_directory(self, temp_storage_dir) -> None:
        nested_path = temp_storage_dir / "nested" / "deep" / "sessions.json"
        store = SessionStore(storage_path=str(nested_path))
        assert nested_path.parent.exists()

    def test_init_loads_existing_file(self, temp_storage_dir) -> None:
        # Criar arquivo com dados existentes
        storage_path = temp_storage_dir / "existing.json"
        existing_data = {
            "session-1": {
                "session_id": "session-1",
                "timestamp": "2024-01-01T00:00:00",
                "input_format": "text",
                "raw_content": "Existing content",
                "unresolved_threads": [],
            }
        }
        with open(storage_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        store = SessionStore(storage_path=str(storage_path))
        assert store.get_session_count() == 1

    def test_init_handles_corrupted_json(self, temp_storage_dir) -> None:
        storage_path = temp_storage_dir / "corrupted.json"
        with open(storage_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        # Não deve lançar exceção, inicia storage vazio
        store = SessionStore(storage_path=str(storage_path))
        assert store.get_session_count() == 0


# ----------------------------------------------------------------------
# Testes — create_session()
# ----------------------------------------------------------------------


class TestCreateSession:
    def test_create_session_generates_uuid(self, session_store: SessionStore) -> None:
        session = session_store.create_session("conteúdo", "text")
        assert session.session_id is not None
        assert len(session.session_id) == 36  # UUID format

    def test_create_session_with_custom_id(self, session_store: SessionStore) -> None:
        session = session_store.create_session("conteúdo", "text", session_id="custom-id")
        assert session.session_id == "custom-id"

    def test_create_session_preserves_content(self, session_store: SessionStore) -> None:
        content = "Meu texto de teste"
        session = session_store.create_session(content, "text")
        assert session.raw_content == content

    def test_create_session_sets_format(self, session_store: SessionStore) -> None:
        session = session_store.create_session("texto", "symbols")
        assert session.input_format == "symbols"

    def test_create_session_has_timestamp(self, session_store: SessionStore) -> None:
        session = session_store.create_session("texto", "text")
        assert session.timestamp is not None
        # ISO format check
        assert "T" in session.timestamp

    def test_create_session_initializes_empty_threads(self, session_store: SessionStore) -> None:
        session = session_store.create_session("texto", "text")
        assert session.unresolved_threads == []

    def test_create_session_saved_to_store(self, session_store: SessionStore) -> None:
        session = session_store.create_session("texto", "text")
        assert session_store.session_exists(session.session_id)

    def test_create_multiple_sessions_unique_ids(self, session_store: SessionStore) -> None:
        session1 = session_store.create_session("texto1", "text")
        session2 = session_store.create_session("texto2", "text")
        assert session1.session_id != session2.session_id

    def test_create_session_format_types(self, session_store: SessionStore) -> None:
        for fmt in ["text", "symbols", "spread"]:
            session = session_store.create_session("teste", fmt)
            assert session.input_format == fmt


# ----------------------------------------------------------------------
# Testes — save_session()
# ----------------------------------------------------------------------


class TestSaveSession:
    def test_save_new_session(self, session_store: SessionStore) -> None:
        session = Session(
            session_id="new-session",
            timestamp="2024-01-01T00:00:00",
            input_format="text",
            raw_content="Novo conteúdo",
            analysis_result=None,
            unresolved_threads=[],
            tags=[],
        )
        session_store.save_session(session)
        assert session_store.session_exists("new-session")

    def test_save_updates_existing_session(self, session_store: SessionStore) -> None:
        session = session_store.create_session("original", "text")
        session.raw_content = "modificado"
        session_store.save_session(session)

        retrieved = session_store.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.raw_content == "modificado"

    def test_save_adds_unresolved_threads(self, session_store_no_auto: SessionStore) -> None:
        session = session_store_no_auto.create_session("texto", "text")
        session.unresolved_threads = ["thread-1", "thread-2"]
        session_store_no_auto.save_session(session)

        # Sem auto_save, precisa explicitamente salvar
        session_store_no_auto._save()

        retrieved = session_store_no_auto.get_session(session.session_id)
        assert retrieved is not None
        assert "thread-1" in retrieved.unresolved_threads


# ----------------------------------------------------------------------
# Testes — get_session()
# ----------------------------------------------------------------------


class TestGetSession:
    def test_get_existing_session(self, session_store: SessionStore) -> None:
        created = session_store.create_session("teste", "text")
        retrieved = session_store.get_session(created.session_id)
        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    def test_get_nonexistent_returns_none(self, session_store: SessionStore) -> None:
        result = session_store.get_session("inexistente-id")
        assert result is None

    def test_get_returns_correct_content(self, session_store: SessionStore) -> None:
        content = "Conteúdo específico"
        session = session_store.create_session(content, "symbols")
        retrieved = session_store.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.raw_content == content

    def test_get_returns_correct_format(self, session_store: SessionStore) -> None:
        session = session_store.create_session("texto", "spread")
        retrieved = session_store.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.input_format == "spread"


# ----------------------------------------------------------------------
# Testes — list_sessions()
# ----------------------------------------------------------------------


class TestListSessions:
    def test_list_empty_store(self, session_store: SessionStore) -> None:
        sessions = session_store.list_sessions()
        assert sessions == []

    def test_list_single_session(self, session_store: SessionStore) -> None:
        session_store.create_session("um", "text")
        sessions = session_store.list_sessions()
        assert len(sessions) == 1

    def test_list_multiple_sessions(self, session_store: SessionStore) -> None:
        session_store.create_session("um", "text")
        session_store.create_session("dois", "text")
        session_store.create_session("três", "text")
        sessions = session_store.list_sessions()
        assert len(sessions) == 3

    def test_list_sorted_by_timestamp(self, session_store: SessionStore) -> None:
        session_store.create_session("primeiro", "text")  # timestamp mais antigo
        session_store.create_session("segundo", "text")
        session_store.create_session("terceiro", "text")

        sessions = session_store.list_sessions()
        timestamps = [s.timestamp for s in sessions]
        assert timestamps == sorted(timestamps)

    def test_list_returns_list_not_reference(self, session_store: SessionStore) -> None:
        """list_sessions() retorna lista nova, mas objetos são os mesmos do storage."""
        session_store.create_session("teste", "text")
        sessions1 = session_store.list_sessions()
        sessions2 = session_store.list_sessions()
        # A lista retornada é nova (não a mesma referência)
        assert sessions1 is not sessions2
        # Os objetos Session são os mesmos do storage
        assert sessions1[0] is sessions2[0]


# ----------------------------------------------------------------------
# Testes — delete_session()
# ----------------------------------------------------------------------


class TestDeleteSession:
    def test_delete_existing_session(self, session_store: SessionStore) -> None:
        session = session_store.create_session("teste", "text")
        result = session_store.delete_session(session.session_id)
        assert result is True
        assert not session_store.session_exists(session.session_id)

    def test_delete_nonexistent_returns_false(self, session_store: SessionStore) -> None:
        result = session_store.delete_session("inexistente-id")
        assert result is False

    def test_delete_decreases_count(self, session_store: SessionStore) -> None:
        session1 = session_store.create_session("um", "text")
        session_store.create_session("dois", "text")
        session_store.delete_session(session1.session_id)
        assert session_store.get_session_count() == 1

    def test_delete_nonexistent_does_not_affect_count(self, session_store: SessionStore) -> None:
        session_store.create_session("um", "text")
        count_before = session_store.get_session_count()
        session_store.delete_session("inexistente")
        assert session_store.get_session_count() == count_before


# ----------------------------------------------------------------------
# Testes — session_exists()
# ----------------------------------------------------------------------


class TestSessionExists:
    def test_exists_returns_true(self, session_store: SessionStore) -> None:
        session = session_store.create_session("teste", "text")
        assert session_store.session_exists(session.session_id) is True

    def test_nonexistent_returns_false(self, session_store: SessionStore) -> None:
        assert session_store.session_exists("nao-existe") is False

    def test_exists_after_delete(self, session_store: SessionStore) -> None:
        session = session_store.create_session("teste", "text")
        session_store.delete_session(session.session_id)
        assert session_store.session_exists(session.session_id) is False


# ----------------------------------------------------------------------
# Testes — get_session_count()
# ----------------------------------------------------------------------


class TestGetSessionCount:
    def test_empty_store_count(self, session_store: SessionStore) -> None:
        assert session_store.get_session_count() == 0

    def test_count_after_create(self, session_store: SessionStore) -> None:
        session_store.create_session("um", "text")
        session_store.create_session("dois", "text")
        assert session_store.get_session_count() == 2

    def test_count_after_delete(self, session_store: SessionStore) -> None:
        s1 = session_store.create_session("um", "text")
        session_store.create_session("dois", "text")
        session_store.delete_session(s1.session_id)
        assert session_store.get_session_count() == 1


# ----------------------------------------------------------------------
# Testes — persistência JSON
# ----------------------------------------------------------------------


class TestPersistence:
    def test_data_persists_to_file(self, temp_storage_dir: Path) -> None:
        storage_path = temp_storage_dir / "persist.json"
        store = SessionStore(storage_path=str(storage_path))
        store.create_session("conteúdo persistido", "text")
        store._save()

        assert storage_path.exists()
        with open(storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 1

    def test_auto_save_enabled(self, temp_storage_dir: Path) -> None:
        storage_path = temp_storage_dir / "auto_save.json"
        store = SessionStore(storage_path=str(storage_path), auto_save=True)
        store.create_session("teste", "text")
        assert storage_path.exists()

    def test_auto_save_disabled_no_auto_write_on_create(self, temp_storage_dir: Path) -> None:
        """Com auto_save=False, create_session() não escreve automaticamente."""
        storage_path = temp_storage_dir / "no_auto.json"
        store = SessionStore(storage_path=str(storage_path), auto_save=False)
        # _load() já criou o arquivo ao iniciar, então limpa para testar create_session
        if storage_path.exists():
            storage_path.unlink()

        store.create_session("teste", "text")
        # Arquivo não existe até _save() ser chamado manualmente
        assert not storage_path.exists()

    def test_reload_preserves_sessions(self, temp_storage_dir: Path) -> None:
        storage_path = temp_storage_dir / "reload.json"

        # Criar e salvar sessões
        store1 = SessionStore(storage_path=str(storage_path))
        store1.create_session("sessão 1", "text")
        store1.create_session("sessão 2", "text")

        # Recriar store (simula reinicialização)
        store2 = SessionStore(storage_path=str(storage_path))
        assert store2.get_session_count() == 2

    def test_corrupted_file_initializes_empty(self, temp_storage_dir: Path) -> None:
        storage_path = temp_storage_dir / "corrupted.json"
        with open(storage_path, "w", encoding="utf-8") as f:
            f.write("{ malformed")

        store = SessionStore(storage_path=str(storage_path))
        # Deve inicializar vazio, não lançar exceção
        assert store.get_session_count() == 0


# ----------------------------------------------------------------------
# Testes — serialização e desserialização
# ----------------------------------------------------------------------


class TestSerialization:
    def test_serialize_sessions(self, session_store: SessionStore) -> None:
        session_store.create_session("um", "text")
        session_store.create_session("dois", "text")
        data = session_store._serialize_sessions(session_store._sessions)
        assert len(data) == 2
        assert all(isinstance(k, str) for k in data.keys())

    def test_deserialize_sessions(self, session_store: SessionStore) -> None:
        raw_data = {
            "s1": {
                "session_id": "s1",
                "timestamp": "2024-01-01T00:00:00",
                "input_format": "text",
                "raw_content": "Conteúdo",
                "unresolved_threads": [],
            },
            "s2": {
                "session_id": "s2",
                "timestamp": "2024-01-02T00:00:00",
                "input_format": "symbols",
                "raw_content": "Mais conteúdo",
                "unresolved_threads": ["t1"],
            },
        }
        sessions = session_store._deserialize_sessions(raw_data)
        assert len(sessions) == 2
        assert sessions["s1"].raw_content == "Conteúdo"
        assert sessions["s2"].unresolved_threads == ["t1"]

    def test_deserialize_ignores_invalid(self, session_store: SessionStore) -> None:
        raw_data = {
            "valid-session": {
                "session_id": "valid-session",
                "timestamp": "2024-01-01T00:00:00",
                "input_format": "text",
                "raw_content": "Válido",
                "unresolved_threads": [],
            },
            "invalid-session": {
                "session_id": "invalid-session",
                "timestamp": "2024-01-01T00:00:00",
                # missing required fields
            },
        }
        sessions = session_store._deserialize_sessions(raw_data)
        # Apenas sessão válida é restaurada
        assert len(sessions) == 1
        assert "valid-session" in sessions

    def test_session_to_dict(self, session_store: SessionStore) -> None:
        session = session_store.create_session("teste", "text")
        data = session_store._session_to_dict(session)
        assert data["session_id"] == session.session_id
        assert data["raw_content"] == "teste"
        assert data["input_format"] == "text"
        assert "unresolved_threads" in data
        assert "tags" in data

    def test_session_to_dict_includes_tags(self, session_store: SessionStore) -> None:
        from clareza.types import Session
        session = Session(
            session_id="with-tags",
            timestamp="2024-01-01T00:00:00",
            input_format="text",
            raw_content="Teste",
            analysis_result=None,
            unresolved_threads=[],
            tags=["carreira", "trabalho"],
        )
        data = session_store._session_to_dict(session)
        assert data["tags"] == ["carreira", "trabalho"]

    def test_dict_to_session(self, session_store: SessionStore) -> None:
        raw_data = {
            "session_id": "dict-test",
            "timestamp": "2024-06-15T12:00:00",
            "input_format": "spread",
            "raw_content": "Teste de conversão",
            "unresolved_threads": ["t1", "t2"],
        }
        session = session_store._dict_to_session(raw_data)
        assert session.session_id == "dict-test"
        assert session.timestamp == "2024-06-15T12:00:00"
        assert session.input_format == "spread"
        assert session.unresolved_threads == ["t1", "t2"]
        # analysis_result é None por padrão
        assert session.analysis_result is None

    def test_dict_to_session_defaults_unresolved_threads(self, session_store: SessionStore) -> None:
        raw_data = {
            "session_id": "no-threads",
            "timestamp": "2024-01-01T00:00:00",
            "input_format": "text",
            "raw_content": "Sem threads",
        }
        session = session_store._dict_to_session(raw_data)
        assert session.unresolved_threads == []

    def test_dict_to_session_defaults_unresolved_threads(self, session_store: SessionStore) -> None:
        raw_data = {
            "session_id": "no-threads",
            "timestamp": "2024-01-01T00:00:00",
            "input_format": "text",
            "raw_content": "Sem threads",
        }
        session = session_store._dict_to_session(raw_data)
        assert session.unresolved_threads == []

    def test_dict_to_session_includes_tags(self, session_store: SessionStore) -> None:
        raw_data = {
            "session_id": "with-tags",
            "timestamp": "2024-01-01T00:00:00",
            "input_format": "text",
            "raw_content": "Com tags",
            "unresolved_threads": [],
            "tags": ["carreira", "trabalho"],
        }
        session = session_store._dict_to_session(raw_data)
        assert session.tags == ["carreira", "trabalho"]

    def test_dict_to_session_defaults_tags_to_empty(self, session_store: SessionStore) -> None:
        raw_data = {
            "session_id": "no-tags",
            "timestamp": "2024-01-01T00:00:00",
            "input_format": "text",
            "raw_content": "Sem tags",
        }
        session = session_store._dict_to_session(raw_data)
        assert session.tags == []


# ----------------------------------------------------------------------
# Testes — get_sessions_by_tag()
# ----------------------------------------------------------------------


class TestGetSessionsByTag:
    def test_get_sessions_by_tag_empty_store(self, session_store: SessionStore) -> None:
        result = session_store.get_sessions_by_tag("carreira")
        assert result == []

    def test_get_sessions_by_tag_finds_matching(self, session_store: SessionStore) -> None:
        session_store.create_session("texto1", "text")
        # Adicionar tag manualmente
        s2 = session_store.create_session("texto2", "text")
        from clareza.types import Session
        updated = Session(
            session_id=s2.session_id,
            timestamp=s2.timestamp,
            input_format=s2.input_format,
            raw_content=s2.raw_content,
            analysis_result=None,
            unresolved_threads=[],
            tags=["carreira"],
        )
        session_store.save_session(updated)

        result = session_store.get_sessions_by_tag("carreira")
        assert len(result) == 1
        assert result[0].session_id == s2.session_id

    def test_get_sessions_by_tag_case_insensitive(self, session_store: SessionStore) -> None:
        s1 = session_store.create_session("texto1", "text")
        from clareza.types import Session
        updated = Session(
            session_id=s1.session_id,
            timestamp=s1.timestamp,
            input_format=s1.input_format,
            raw_content=s1.raw_content,
            analysis_result=None,
            unresolved_threads=[],
            tags=["Carreira"],
        )
        session_store.save_session(updated)

        result = session_store.get_sessions_by_tag("CARREIRA")
        assert len(result) == 1

    def test_get_sessions_by_tag_sorted_by_timestamp(self, session_store: SessionStore) -> None:
        from datetime import timedelta
        from clareza.types import Session

        base_time = "2024-01-01T00:00:00"
        for i, tag in enumerate(["carreira", "relacionamento", "carreira"]):
            s = session_store.create_session(f"texto{i}", "text")
            # Ajustar timestamp para simular diferentes horas
            timestamp_parts = base_time.split("T")
            hour = 10 + i
            timestamp = f"{timestamp_parts[0]}T{hour:02d}:00:00"
            updated = Session(
                session_id=s.session_id,
                timestamp=timestamp,
                input_format=s.input_format,
                raw_content=s.raw_content,
                analysis_result=None,
                unresolved_threads=[],
                tags=[tag],
            )
            session_store.save_session(updated)

        result = session_store.get_sessions_by_tag("carreira")
        assert len(result) == 2
        # Deve estar ordenado por timestamp
        assert result[0].timestamp < result[1].timestamp


class TestIOPermissions:
    def test_load_nonexistent_file_creates_new(self, temp_storage_dir: Path) -> None:
        storage_path = temp_storage_dir / "new_file.json"
        store = SessionStore(storage_path=str(storage_path))
        assert storage_path.exists()
        assert store.get_session_count() == 0

    def test_create_directory_structure(self, temp_storage_dir: Path) -> None:
        storage_path = temp_storage_dir / "deep" / "dir" / "sessions.json"
        SessionStore(storage_path=str(storage_path))
        assert storage_path.parent.exists()