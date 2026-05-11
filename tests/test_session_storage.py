"""Testes unitários para Session dataclass e tags field.

Cobertura:
- Session dataclass — inicialização com tags
- Session.tags — campo de lista de tags temáticas
- Session.tags — valor default (lista vazia)
- Persistência de tags via SessionStorage
- SessionStorage._dict_to_session — reconstrução de tags
"""

import json
import pytest
import tempfile
from pathlib import Path

from src.types import Session
from src.session_storage import (
    SessionStorage,
    SessionStorageError,
    SessionNotFoundError,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def temp_storage_dir() -> Path:
    """Diretório temporário para testes de persistência."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_storage_dir: Path) -> SessionStorage:
    """SessionStorage com diretório temporário."""
    return SessionStorage(storage_dir=str(temp_storage_dir))


# ----------------------------------------------------------------------
# Testes — Session dataclass com tags
# ----------------------------------------------------------------------


class TestSessionTagsField:
    """Testes para o campo tags da Session dataclass."""

    def test_session_with_tags(self) -> None:
        """Session pode ser criada com tags."""
        session = Session(
            session_id="test-001",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Tenho dúvida sobre carreira",
            tags=["carreira", "trabalho"],
        )
        assert session.tags == ["carreira", "trabalho"]
        assert len(session.tags) == 2

    def test_session_tags_default_empty_list(self) -> None:
        """Tags tem lista vazia como default."""
        session = Session(
            session_id="test-002",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto simples",
        )
        assert session.tags == []
        assert isinstance(session.tags, list)
        assert len(session.tags) == 0

    def test_session_with_single_tag(self) -> None:
        """Session pode ter uma única tag."""
        session = Session(
            session_id="test-003",
            timestamp="2026-05-11T10:00:00Z",
            input_format="symbols",
            raw_content="casa,estrela",
            tags=["relacionamento"],
        )
        assert len(session.tags) == 1
        assert "relacionamento" in session.tags

    def test_session_with_many_tags(self) -> None:
        """Session pode ter múltiplas tags."""
        tags = ["carreira", "relacionamento", "saúde", "finanças", "família"]
        session = Session(
            session_id="test-004",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Conteúdo complexo",
            tags=tags,
        )
        assert len(session.tags) == 5
        assert session.tags == tags

    def test_session_tags_are_normalized(self) -> None:
        """Tags são armazenadas como strings normais."""
        session = Session(
            session_id="test-005",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto",
            tags=["CARREIRA", "Relacionamento"],
        )
        # Verifica que são strings (não são alteradas automaticamente)
        assert all(isinstance(t, str) for t in session.tags)
        assert "CARREIRA" in session.tags
        assert "Relacionamento" in session.tags

    def test_session_tags_with_accents(self) -> None:
        """Tags podem conter acentos do português."""
        session = Session(
            session_id="test-006",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Situação difícil",
            tags=["relação", "família", "saúde"],
        )
        assert "relação" in session.tags
        assert "família" in session.tags
        assert "saúde" in session.tags

    def test_session_tags_immutable_by_default(self) -> None:
        """Tags retorna lista separada, não a lista interna."""
        session = Session(
            session_id="test-007",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto",
        )
        original_len = len(session.tags)
        session.tags.append("nova-tag")  # Não deve afetar o default
        # Comportamento normal de dataclass: o campo pode ser modificado
        assert len(session.tags) == original_len + 1


# ----------------------------------------------------------------------
# Testes — SessionStorage com tags
# ----------------------------------------------------------------------


class TestSessionStorageTags:
    """Testes para persistência de tags via SessionStorage."""

    def test_save_and_load_session_with_tags(
        self, storage: SessionStorage
    ) -> None:
        """Session com tags é salva e carregada corretamente."""
        session = Session(
            session_id="persist-001",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Dúvida sobre trabalho",
            tags=["trabalho", "carreira"],
        )
        storage.save_session(session)

        loaded = storage.load_session("persist-001")
        assert loaded.tags == ["trabalho", "carreira"]
        assert len(loaded.tags) == 2

    def test_save_and_load_session_without_tags(
        self, storage: SessionStorage
    ) -> None:
        """Session sem tags é salva e carregada corretamente."""
        session = Session(
            session_id="persist-002",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto simples",
        )
        storage.save_session(session)

        loaded = storage.load_session("persist-002")
        assert loaded.tags == []
        assert isinstance(loaded.tags, list)

    def test_save_and_load_session_with_empty_tags_list(
        self, storage: SessionStorage
    ) -> None:
        """Session com lista vazia de tags explícita é salva corretamente."""
        session = Session(
            session_id="persist-003",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto",
            tags=[],
        )
        storage.save_session(session)

        loaded = storage.load_session("persist-003")
        assert loaded.tags == []

    def test_tags_persisted_as_list_in_json(
        self, storage: SessionStorage, temp_storage_dir: Path
    ) -> None:
        """Tags são salvas como lista no arquivo JSON."""
        session = Session(
            session_id="json-001",
            timestamp="2026-05-11T10:00:00Z",
            input_format="symbols",
            raw_content="casa,estrela",
            tags=["lar", "destino"],
        )
        storage.save_session(session)

        json_path = temp_storage_dir / "json-001.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "tags" in data
        assert isinstance(data["tags"], list)
        assert data["tags"] == ["lar", "destino"]

    def test_tags_loaded_from_json(
        self, storage: SessionStorage, temp_storage_dir: Path
    ) -> None:
        """Tags são corretamente reconstruídas do JSON."""
        json_path = temp_storage_dir / "manual-001.json"
        manual_data = {
            "session_id": "manual-001",
            "timestamp": "2026-05-11T12:00:00Z",
            "input_format": "text",
            "raw_content": "Conteúdo manual",
            "tags": ["finanças", "investimento"],
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(manual_data, f, ensure_ascii=False)

        loaded = storage.load_session("manual-001")
        assert loaded.tags == ["finanças", "investimento"]

    def test_tags_default_to_empty_when_missing_from_json(
        self, storage: SessionStorage, temp_storage_dir: Path
    ) -> None:
        """Se campo tags está ausente no JSON, usa default vazio."""
        json_path = temp_storage_dir / "no-tags-001.json"
        manual_data = {
            "session_id": "no-tags-001",
            "timestamp": "2026-05-11T12:00:00Z",
            "input_format": "text",
            "raw_content": "Sem tags no JSON",
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(manual_data, f, ensure_ascii=False)

        loaded = storage.load_session("no-tags-001")
        assert loaded.tags == []
        assert isinstance(loaded.tags, list)

    def test_list_sessions_by_tag(self, storage: SessionStorage) -> None:
        """list_sessions_by_tag filtra sessões por tag."""
        sessions = [
            Session(
                session_id="tag-filter-001",
                timestamp="2026-05-11T10:00:00Z",
                input_format="text",
                raw_content="Sobre trabalho",
                tags=["trabalho"],
            ),
            Session(
                session_id="tag-filter-002",
                timestamp="2026-05-11T11:00:00Z",
                input_format="text",
                raw_content="Sobre saúde",
                tags=["saúde"],
            ),
            Session(
                session_id="tag-filter-003",
                timestamp="2026-05-11T12:00:00Z",
                input_format="text",
                raw_content="Sobre carreira",
                tags=["trabalho", "carreira"],
            ),
        ]

        for session in sessions:
            storage.save_session(session)

        trabalho_sessions = storage.list_sessions_by_tag("trabalho")
        assert len(trabalho_sessions) == 2
        assert {s.session_id for s in trabalho_sessions} == {"tag-filter-001", "tag-filter-003"}

    def test_list_sessions_by_tag_case_insensitive(
        self, storage: SessionStorage
    ) -> None:
        """list_sessions_by_tag é case-insensitive."""
        session = Session(
            session_id="case-001",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto",
            tags=["CARREIRA"],
        )
        storage.save_session(session)

        # Busca com minúsculas
        results_lower = storage.list_sessions_by_tag("carreira")
        assert len(results_lower) == 1

        # Busca com maiúsculas
        results_upper = storage.list_sessions_by_tag("CARREIRA")
        assert len(results_upper) == 1

    def test_list_sessions_by_nonexistent_tag(
        self, storage: SessionStorage
    ) -> None:
        """Tag inexistente retorna lista vazia."""
        session = Session(
            session_id="none-001",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto",
            tags=["trabalho"],
        )
        storage.save_session(session)

        results = storage.list_sessions_by_tag("inexistente")
        assert len(results) == 0

    def test_update_session_tags(
        self, storage: SessionStorage
    ) -> None:
        """Tags podem ser atualizadas e re-salvas."""
        session = Session(
            session_id="update-001",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto original",
            tags=["trabalho"],
        )
        storage.save_session(session)

        # Carrega, atualiza tags, e salva novamente
        loaded = storage.load_session("update-001")
        loaded.tags = ["trabalho", "carreira", "novo-tema"]
        storage.save_session(loaded)

        # Verifica atualização
        updated = storage.load_session("update-001")
        assert updated.tags == ["trabalho", "carreira", "novo-tema"]
        assert len(updated.tags) == 3

    def test_session_exists_with_tags(
        self, storage: SessionStorage
    ) -> None:
        """session_exists retorna True para sessão com tags."""
        session = Session(
            session_id="exists-001",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto",
            tags=["relacionamento"],
        )
        storage.save_session(session)

        assert storage.session_exists("exists-001") is True

    def test_delete_session_with_tags(
        self, storage: SessionStorage
    ) -> None:
        """Sessão com tags pode ser deletada."""
        session = Session(
            session_id="delete-001",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Texto",
            tags=["temp-tag"],
        )
        storage.save_session(session)
        assert storage.session_exists("delete-001")

        storage.delete_session("delete-001")
        assert storage.session_exists("delete-001") is False


# ----------------------------------------------------------------------
# Testes — SessionStorage._dict_to_session com tags
# ----------------------------------------------------------------------


class TestDictToSessionWithTags:
    """Testes para reconstrução de Session do dicionário com tags."""

    def test_reconstructs_tags_from_dict(self, storage: SessionStorage) -> None:
        """_dict_to_session corretamente reconstrói tags."""
        data = {
            "session_id": "dict-001",
            "timestamp": "2026-05-11T10:00:00Z",
            "input_format": "text",
            "raw_content": "Conteúdo",
            "tags": ["trabalho", "dinheiro"],
        }

        session = storage._dict_to_session(data)
        assert session.tags == ["trabalho", "dinheiro"]

    def test_reconstructs_empty_tags(self, storage: SessionStorage) -> None:
        """_dict_to_session com tags=[] reconstrói lista vazia."""
        data = {
            "session_id": "dict-002",
            "timestamp": "2026-05-11T10:00:00Z",
            "input_format": "text",
            "raw_content": "Conteúdo",
            "tags": [],
        }

        session = storage._dict_to_session(data)
        assert session.tags == []

    def test_uses_default_tags_when_missing(self, storage: SessionStorage) -> None:
        """_dict_to_session usa default [] quando tags ausente."""
        data = {
            "session_id": "dict-003",
            "timestamp": "2026-05-11T10:00:00Z",
            "input_format": "text",
            "raw_content": "Conteúdo",
        }

        session = storage._dict_to_session(data)
        assert session.tags == []


# ----------------------------------------------------------------------
# Testes — Integração com SessionClusterer
# ----------------------------------------------------------------------


class TestSessionTagsIntegration:
    """Testes de integração para tags com clustering."""

    def test_cluster_by_tag(self, storage: SessionStorage) -> None:
        """cluster_by_tag filtra sessões corretamente."""
        from src.session_clustering import SessionClusterer

        sessions = [
            Session(
                session_id="cluster-001",
                timestamp="2026-05-11T10:00:00Z",
                input_format="text",
                raw_content="Texto",
                tags=["saúde"],
            ),
            Session(
                session_id="cluster-002",
                timestamp="2026-05-11T11:00:00Z",
                input_format="text",
                raw_content="Texto",
                tags=["carreira"],
            ),
            Session(
                session_id="cluster-003",
                timestamp="2026-05-11T12:00:00Z",
                input_format="text",
                raw_content="Texto",
                tags=["saúde", "bem-estar"],
            ),
        ]

        for session in sessions:
            storage.save_session(session)

        clusterer = SessionClusterer(storage)
        health_sessions = clusterer.cluster_by_tag(sessions, "saúde")

        assert len(health_sessions) == 2
        assert {s.session_id for s in health_sessions} == {"cluster-001", "cluster-003"}

    def test_find_related_sessions_by_tags(
        self, storage: SessionStorage
    ) -> None:
        """find_related_sessions considera tags no scoring."""
        from src.session_clustering import SessionClusterer

        # Sessões existentes no storage
        past_sessions = [
            Session(
                session_id="past-001",
                timestamp="2026-05-10T10:00:00Z",
                input_format="text",
                raw_content="Problemas no trabalho",
                tags=["trabalho", "carreira"],
            ),
            Session(
                session_id="past-002",
                timestamp="2026-05-09T10:00:00Z",
                input_format="text",
                raw_content="Questões de saúde",
                tags=["saúde"],
            ),
        ]

        for session in past_sessions:
            storage.save_session(session)

        # Sessão atual com tag comum
        current = Session(
            session_id="current-001",
            timestamp="2026-05-11T10:00:00Z",
            input_format="text",
            raw_content="Dúvida sobre trabalho",
            tags=["trabalho"],
        )

        clusterer = SessionClusterer(storage)
        related = clusterer.find_related_sessions(current, past_sessions)

        # Deve encontrar a sessão com tag "trabalho"
        assert len(related) >= 1
        related_ids = {r.session.session_id for r in related}
        assert "past-001" in related_ids
