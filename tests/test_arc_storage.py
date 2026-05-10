"""Testes unitários para src/arc_storage.py.

Cobertura:
- ArcStorage.__init__() — inicialização com path customizado
- ArcStorage.save_arc() — criação e atualização de arcos
- ArcStorage.get_arc() — recuperação por nome
- ArcStorage.list_arcs() — listagem ordenada por updated_at
- ArcStorage.delete_arc() — remoção de arcos
- ArcStorage.add_session() — adição de sessões
- ArcStorage.StorageError — atributos e formatação
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src.arc_storage import ArcStorage, StorageError
from src.types import ReflectionArc, SessionRecord


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def temp_storage(tmp_path: Path) -> Path:
    """Caminho temporário para arquivo de storage."""
    return tmp_path / "arcs.json"


@pytest.fixture
def storage(temp_storage: Path) -> ArcStorage:
    """Storage com path temporário."""
    return ArcStorage(storage_path=temp_storage)


@pytest.fixture
def sample_arc() -> ReflectionArc:
    """Arco de exemplo com uma sessão."""
    session = SessionRecord(
        session_id="sess-001",
        timestamp=datetime(2024, 1, 15, 10, 30),
        arc_name="trabalho-2024",
        input_content="Dúvidas sobre promoção",
        format="text",
        keywords=["trabalho", "promoção"],
        themes=["carreira"],
        diagnosis="Situação em análise",
        risks=["insegurança"],
        decisions=["Buscar mentoring"],
    )
    return ReflectionArc(
        name="trabalho-2024",
        description="Arco sobre carreira profissional",
        sessions=[session],
        created_at=datetime(2024, 1, 15),
        updated_at=datetime(2024, 1, 15),
    )


@pytest.fixture
def sample_arc_2() -> ReflectionArc:
    """Segundo arco de exemplo."""
    session = SessionRecord(
        session_id="sess-002",
        timestamp=datetime(2024, 2, 20, 14, 0),
        arc_name="relacionamento",
        input_content="Questões familiares",
        format="text",
        keywords=["família", "relação"],
        themes=["relacionamento"],
        diagnosis="Foco na comunicação",
        risks=[],
        decisions=["Conversa aberta"],
    )
    return ReflectionArc(
        name="relacionamento",
        description="Arco sobre vida amorosa",
        sessions=[session],
        created_at=datetime(2024, 2, 20),
        updated_at=datetime(2024, 2, 20),
    )


# ----------------------------------------------------------------------
# Testes — __init__()
# ----------------------------------------------------------------------


class TestStorageInit:
    def test_initializes_with_custom_path(self, temp_storage: Path) -> None:
        """Storage aceita path customizado."""
        storage = ArcStorage(storage_path=temp_storage)
        assert storage._storage_path == temp_storage

    def test_creates_storage_directory(self, tmp_path: Path) -> None:
        """Inicialização cria diretório de storage se necessário."""
        custom_path = tmp_path / "subdir" / "arcs.json"
        storage = ArcStorage(storage_path=custom_path)
        assert custom_path.parent.exists()


# ----------------------------------------------------------------------
# Testes — save_arc()
# ----------------------------------------------------------------------


class TestSaveArc:
    def test_save_new_arc_creates_file(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Salvando novo arco cria o arquivo de storage."""
        storage.save_arc(sample_arc)
        assert storage._storage_path.exists()

    def test_save_new_arc_stores_data(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Novo arco é persistido corretamente."""
        storage.save_arc(sample_arc)

        with open(storage._storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["name"] == "trabalho-2024"
        assert data[0]["description"] == "Arco sobre carreira profissional"

    def test_save_updates_existing_arc(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Salvando arco com mesmo nome atualiza dados existentes."""
        storage.save_arc(sample_arc)

        # Atualizar descrição
        sample_arc.description = "Descrição atualizada"
        storage.save_arc(sample_arc)

        arcs = storage.list_arcs()
        assert len(arcs) == 1
        assert arcs[0].description == "Descrição atualizada"

    def test_save_multiple_arcs(self, storage: ArcStorage, sample_arc: ReflectionArc, sample_arc_2: ReflectionArc) -> None:
        """Múltiplos arcos são salvos corretamente."""
        storage.save_arc(sample_arc)
        storage.save_arc(sample_arc_2)

        arcs = storage.list_arcs()
        assert len(arcs) == 2
        names = {arc.name for arc in arcs}
        assert "trabalho-2024" in names
        assert "relacionamento" in names

    def test_save_preserves_sessions(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Sessões são preservadas ao salvar."""
        storage.save_arc(sample_arc)

        retrieved = storage.get_arc("trabalho-2024")
        assert retrieved is not None
        assert len(retrieved.sessions) == 1
        assert retrieved.sessions[0].session_id == "sess-001"


# ----------------------------------------------------------------------
# Testes — get_arc()
# ----------------------------------------------------------------------


class TestGetArc:
    def test_get_existing_arc(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Recupera arco existente pelo nome."""
        storage.save_arc(sample_arc)

        result = storage.get_arc("trabalho-2024")
        assert result is not None
        assert result.name == "trabalho-2024"
        assert result.description == "Arco sobre carreira profissional"

    def test_get_nonexistent_arc_returns_none(self, storage: ArcStorage) -> None:
        """Arco inexistente retorna None."""
        result = storage.get_arc("nao-existe")
        assert result is None

    def test_get_arc_returns_hydrated_object(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Arco retornado tem sessões hydratadas (não dicts)."""
        storage.save_arc(sample_arc)

        result = storage.get_arc("trabalho-2024")
        assert result is not None
        assert isinstance(result, ReflectionArc)
        assert isinstance(result.sessions[0], SessionRecord)
        assert result.sessions[0].input_content == "Dúvidas sobre promoção"


# ----------------------------------------------------------------------
# Testes — list_arcs()
# ----------------------------------------------------------------------


class TestListArcs:
    def test_list_empty_storage(self, storage: ArcStorage) -> None:
        """Storage vazio retorna lista vazia."""
        result = storage.list_arcs()
        assert result == []

    def test_list_single_arc(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Lista com um arco retorna esse arco."""
        storage.save_arc(sample_arc)

        result = storage.list_arcs()
        assert len(result) == 1
        assert result[0].name == "trabalho-2024"

    def test_list_sorted_by_updated_at_descending(self, storage: ArcStorage, sample_arc: ReflectionArc, sample_arc_2: ReflectionArc) -> None:
        """Arcos são ordenados por updated_at decrescente."""
        # arco2 foi criado depois
        storage.save_arc(sample_arc)
        storage.save_arc(sample_arc_2)

        result = storage.list_arcs()
        # sample_arc_2 tem updated_at mais recente (2024-02-20 vs 2024-01-15)
        assert result[0].name == "relacionamento"
        assert result[1].name == "trabalho-2024"

    def test_list_after_update_changes_order(self, storage: ArcStorage, sample_arc: ReflectionArc, sample_arc_2: ReflectionArc) -> None:
        """Atualizar um arco antigo o move para o topo."""
        storage.save_arc(sample_arc)
        storage.save_arc(sample_arc_2)

        # Atualizar sample_arc com data mais recente
        sample_arc.updated_at = datetime.now() + timedelta(days=1)
        storage.save_arc(sample_arc)

        result = storage.list_arcs()
        assert result[0].name == "trabalho-2024"


# ----------------------------------------------------------------------
# Testes — delete_arc()
# ----------------------------------------------------------------------


class TestDeleteArc:
    def test_delete_existing_arc(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Remove arco existente retorna True."""
        storage.save_arc(sample_arc)

        result = storage.delete_arc("trabalho-2024")
        assert result is True

        # Verifica que foi removido
        assert storage.get_arc("trabalho-2024") is None
        assert storage.list_arcs() == []

    def test_delete_nonexistent_arc_returns_false(self, storage: ArcStorage) -> None:
        """Remover arco inexistente retorna False."""
        result = storage.delete_arc("nao-existe")
        assert result is False

    def test_delete_preserves_other_arcs(self, storage: ArcStorage, sample_arc: ReflectionArc, sample_arc_2: ReflectionArc) -> None:
        """Remover um arco não afeta os outros."""
        storage.save_arc(sample_arc)
        storage.save_arc(sample_arc_2)

        storage.delete_arc("trabalho-2024")

        result = storage.list_arcs()
        assert len(result) == 1
        assert result[0].name == "relacionamento"


# ----------------------------------------------------------------------
# Testes — add_session()
# ----------------------------------------------------------------------


class TestAddSession:
    def test_add_session_to_existing_arc(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Adiciona sessão a arco existente."""
        storage.save_arc(sample_arc)

        new_session = SessionRecord(
            session_id="sess-003",
            timestamp=datetime(2024, 3, 10, 9, 0),
            arc_name="trabalho-2024",
            input_content="Nova dúvida",
            format="symbols",
            keywords=["progresso"],
            themes=["carreira"],
            diagnosis="Evolução",
            risks=[],
            decisions=[],
        )

        storage.add_session("trabalho-2024", new_session)

        arc = storage.get_arc("trabalho-2024")
        assert arc is not None
        assert len(arc.sessions) == 2
        session_ids = [s.session_id for s in arc.sessions]
        assert "sess-001" in session_ids
        assert "sess-003" in session_ids

    def test_add_session_to_nonexistent_arc_raises_error(self, storage: ArcStorage) -> None:
        """Adicionar sessão a arco inexistente levanta StorageError."""
        session = SessionRecord(
            session_id="sess-999",
            timestamp=datetime.now(),
            arc_name="inexistente",
        )

        with pytest.raises(StorageError) as exc_info:
            storage.add_session("inexistente", session)
        assert "não encontrado" in str(exc_info.value)


# ----------------------------------------------------------------------
# Testes — StorageError
# ----------------------------------------------------------------------


class TestStorageError:
    def test_error_message(self) -> None:
        """StorageError contém mensagem."""
        err = StorageError("Erro de teste")
        assert "Erro de teste" in str(err)
        assert err.message == "Erro de teste"

    def test_error_with_operation(self) -> None:
        """StorageError inclui operação."""
        err = StorageError("Falha", operation="read")
        assert "read" in str(err)

    def test_error_with_details(self) -> None:
        """StorageError inclui detalhes."""
        err = StorageError("Falha", details="arquivo corrompido")
        assert "arquivo corrompido" in str(err)

    def test_error_with_all_attributes(self) -> None:
        """StorageError formatado completo."""
        err = StorageError("Falha", operation="write", details="sem espaço")
        err_str = str(err)
        assert "Falha" in err_str
        assert "write" in err_str
        assert "sem espaço" in err_str

    def test_error_is_exception_subclass(self) -> None:
        """StorageError é subclasse de Exception."""
        err = StorageError("teste")
        assert isinstance(err, Exception)


# ----------------------------------------------------------------------
# Testes — Serialização/Deserialização
# ----------------------------------------------------------------------


class TestSerialization:
    def test_datetime_isoformat(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Datas são salvas em formato ISO."""
        storage.save_arc(sample_arc)

        with open(storage._storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # created_at preserva a data original
        assert "2024-01-15" in data[0]["created_at"]
        # updated_at é atualizado para o momento atual (contém data atual)
        assert "2026-05-10" in data[0]["updated_at"]
        assert "T" in data[0]["updated_at"]  # formato ISO com T

    def test_session_fields_serialized(self, storage: ArcStorage, sample_arc: ReflectionArc) -> None:
        """Todos os campos de sessão são serializados."""
        storage.save_arc(sample_arc)

        with open(storage._storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = data[0]["sessions"][0]
        assert session["session_id"] == "sess-001"
        assert session["input_content"] == "Dúvidas sobre promoção"
        assert session["keywords"] == ["trabalho", "promoção"]
        assert session["themes"] == ["carreira"]

    def test_deserialize_with_empty_sessions(self, storage: ArcStorage) -> None:
        """Arco sem sessões é deserializado corretamente."""
        arc = ReflectionArc(
            name="vazio",
            description="Sem sessões",
            sessions=[],
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
        )
        storage.save_arc(arc)

        result = storage.get_arc("vazio")
        assert result is not None
        assert result.sessions == []


# ----------------------------------------------------------------------
# Testes — Error Handling
# ----------------------------------------------------------------------


class TestErrorHandling:
    def test_corrupted_json_file(self, temp_storage: Path) -> None:
        """Arquivo JSON corrompido levanta StorageError."""
        with open(temp_storage, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        storage = ArcStorage(storage_path=temp_storage)

        with pytest.raises(StorageError) as exc_info:
            storage._load_all_arcs()
        assert "corrompido" in str(exc_info.value).lower()

    def test_save_to_invalid_directory(self, tmp_path: Path) -> None:
        """Salvar em diretório inexistente cria automaticamente."""
        #tmp_path é válido, mas vamos forçar situação
        storage = ArcStorage(storage_path=tmp_path / "nao" / "existe" / "arcs.json")
        arc = ReflectionArc(name="teste")
        # Não deve levantar erro - diretório é criado
        storage.save_arc(arc)
        assert storage._storage_path.exists()