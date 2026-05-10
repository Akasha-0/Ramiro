"""Armazenamento de arcos de reflexão — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável pela persistência de dados de arcos de reflexão.
Gerencia leitura/escrita de arcos e sessões em storage JSON.

Arquivo de storage: ~/.clareza/arcs.json
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from src.types import ReflectionArc, SessionRecord

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------

_STORAGE_DIR = Path.home() / ".clareza"
_STORAGE_FILE = _STORAGE_DIR / "arcs.json"

# ----------------------------------------------------------------------
# Exceções
# ----------------------------------------------------------------------


class StorageError(Exception):
    """Exceção lançada quando operações de storage falham.

    Attributes:
        message: Descrição legível do erro.
        operation: Operação que estava sendo executada (read/write/delete).
        details: Detalhes adicionais sobre a natureza do erro.
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        self.message = message
        self.operation = operation
        self.details = details
        full = message
        if operation:
            full = f"{message} (op: {operation})"
        if details:
            full = f"{full}: {details}"
        super().__init__(full)


# ----------------------------------------------------------------------
# Storage principal
# ----------------------------------------------------------------------


class ArcStorage:
    """Gerenciador de persistência para arcos de reflexão.

    Implementa operações CRUD para arcos e sessões usando
    storage JSON local em ~/.clareza/arcs.json.

    Attributes:
        storage_path: Caminho do arquivo de storage (para testes).
    """

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._storage_path = storage_path or _STORAGE_FILE
        self._ensure_storage_dir()
        logger.debug("ArcStorage inicializado, path=%s", self._storage_path)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def save_arc(self, arc: ReflectionArc) -> None:
        """Salva um arco de reflexão no storage.

        Se o arco já existir (mesmo nome), atualiza os dados.
        Se não existir, cria novo arco.

        Args:
            arc: Arco de reflexão a ser salvo.

        Raises:
            StorageError: Se houver erro ao salvar no disco.
        """
        logger.info("Salvando arco: %s", arc.name)

        try:
            all_arcs = self._load_all_arcs()

            # Encontrar índice do arco existente ou adicionar novo
            existing_idx = None
            for idx, a in enumerate(all_arcs):
                if a.name == arc.name:
                    existing_idx = idx
                    break

            # Atualizar timestamp
            from datetime import datetime
            arc.updated_at = datetime.now()

            if existing_idx is not None:
                all_arcs[existing_idx] = arc
                logger.debug("Arco atualizado: %s", arc.name)
            else:
                all_arcs.append(arc)
                logger.debug("Novo arco criado: %s", arc.name)

            self._save_all_arcs(all_arcs)
            logger.info("Arco salvo com sucesso: %s (%d sessões)", arc.name, len(arc.sessions))

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                "Falha ao salvar arco",
                operation="write",
                details=str(e),
            ) from e

    def get_arc(self, name: str) -> Optional[ReflectionArc]:
        """Recupera um arco pelo nome.

        Args:
            name: Nome do arco a recuperar.

        Returns:
            ReflectionArc se encontrado, None caso contrário.
        """
        logger.debug("Buscando arco: %s", name)

        all_arcs = self._load_all_arcs()
        for arc in all_arcs:
            if arc.name == name:
                logger.debug("Arco encontrado: %s", name)
                return arc

        logger.debug("Arco não encontrado: %s", name)
        return None

    def list_arcs(self) -> list[ReflectionArc]:
        """Lista todos os arcos de reflexão armazenados.

        Returns:
            Lista de todos os arcos ordenados por updated_at (mais recente primeiro).
        """
        logger.debug("Listando todos os arcos")

        all_arcs = self._load_all_arcs()
        # Ordenar por updated_at decrescente
        all_arcs.sort(key=lambda a: a.updated_at, reverse=True)

        logger.debug("Encontrados %d arcos", len(all_arcs))
        return all_arcs

    def delete_arc(self, name: str) -> bool:
        """Remove um arco do storage.

        Args:
            name: Nome do arco a remover.

        Returns:
            True se o arco foi removido, False se não existia.
        """
        logger.info("Removendo arco: %s", name)

        try:
            all_arcs = self._load_all_arcs()
            initial_count = len(all_arcs)

            all_arcs = [a for a in all_arcs if a.name != name]

            if len(all_arcs) == initial_count:
                logger.debug("Arco não encontrado para remoção: %s", name)
                return False

            self._save_all_arcs(all_arcs)
            logger.info("Arco removido: %s", name)
            return True

        except Exception as e:
            raise StorageError(
                "Falha ao remover arco",
                operation="delete",
                details=str(e),
            ) from e

    def add_session(self, arc_name: str, session: SessionRecord) -> None:
        """Adiciona uma sessão a um arco existente.

        Args:
            arc_name: Nome do arco.
            session: Registro de sessão a adicionar.

        Raises:
            StorageError: Se o arco não existir.
        """
        logger.info("Adicionando sessão %s ao arco %s", session.session_id, arc_name)

        arc = self.get_arc(arc_name)
        if arc is None:
            raise StorageError(
                f"Arco não encontrado: {arc_name}",
                operation="add_session",
            )

        arc.sessions.append(session)
        self.save_arc(arc)
        logger.debug("Sessão adicionada ao arco: %s", arc_name)

    # ------------------------------------------------------------------
    # Utilitários de storage
    # ------------------------------------------------------------------

    def _ensure_storage_dir(self) -> None:
        """Garante que o diretório de storage existe."""
        if not self._storage_path.parent.exists():
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug("Diretório de storage criado: %s", self._storage_path.parent)

    def _load_all_arcs(self) -> list[ReflectionArc]:
        """Carrega todos os arcos do arquivo de storage.

        Returns:
            Lista de arcos (pode estar vazia).

        Raises:
            StorageError: Se o arquivo estiver corrompido.
        """
        if not self._storage_path.exists():
            logger.debug("Arquivo de storage não existe, retornando lista vazia")
            return []

        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            arcs = self._deserialize_arcs(data)
            logger.debug("Carregados %d arcos do storage", len(arcs))
            return arcs

        except json.JSONDecodeError as e:
            raise StorageError(
                "Arquivo de storage corrompido",
                operation="read",
                details=str(e),
            ) from e
        except Exception as e:
            raise StorageError(
                "Falha ao ler storage",
                operation="read",
                details=str(e),
            ) from e

    def _save_all_arcs(self, arcs: list[ReflectionArc]) -> None:
        """Salva todos os arcos no arquivo de storage.

        Args:
            arcs: Lista de arcos a serem salvos.

        Raises:
            StorageError: Se houver erro ao escrever.
        """
        try:
            data = self._serialize_arcs(arcs)

            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug("Storage salvo com %d arcos", len(arcs))

        except Exception as e:
            raise StorageError(
                "Falha ao escrever storage",
                operation="write",
                details=str(e),
            ) from e

    # ------------------------------------------------------------------
    # Serialização/Deserialização
    # ------------------------------------------------------------------

    def _serialize_arcs(self, arcs: list[ReflectionArc]) -> list[dict]:
        """Serializa lista de arcos para formato JSON.

        Args:
            arcs: Lista de arcos a serializar.

        Returns:
            Lista de dicionários serializáveis.
        """
        return [self._serialize_arc(arc) for arc in arcs]

    def _serialize_arc(self, arc: ReflectionArc) -> dict:
        """Serializa um arco individual.

        Args:
            arc: Arco a serializar.

        Returns:
            Dicionário com dados do arco.
        """
        return {
            "name": arc.name,
            "description": arc.description,
            "created_at": arc.created_at.isoformat(),
            "updated_at": arc.updated_at.isoformat(),
            "sessions": [self._serialize_session(s) for s in arc.sessions],
        }

    def _serialize_session(self, session: SessionRecord) -> dict:
        """Serializa um registro de sessão.

        Args:
            session: Sessão a serializar.

        Returns:
            Dicionário com dados da sessão.
        """
        return {
            "session_id": session.session_id,
            "timestamp": session.timestamp.isoformat(),
            "arc_name": session.arc_name,
            "input_content": session.input_content,
            "format": session.format,
            "keywords": session.keywords,
            "themes": session.themes,
            "cards": session.cards,
            "diagnosis": session.diagnosis,
            "risks": session.risks,
            "decisions": session.decisions,
        }

    def _deserialize_arcs(self, data: list[dict]) -> list[ReflectionArc]:
        """Desserializa lista de dicionários para arcos.

        Args:
            data: Lista de dicionários JSON.

        Returns:
            Lista de ReflectionArc.
        """
        from datetime import datetime

        arcs: list[ReflectionArc] = []
        for item in data:
            try:
                arc = self._deserialize_arc(item)
                arcs.append(arc)
            except Exception as e:
                logger.warning("Erro ao desserializar arco: %s", e)
                continue

        return arcs

    def _deserialize_arc(self, data: dict) -> ReflectionArc:
        """Desserializa um arco de um dicionário.

        Args:
            data: Dicionário com dados do arco.

        Returns:
            ReflectionArc hydrated.
        """
        from datetime import datetime

        sessions = [self._deserialize_session(s) for s in data.get("sessions", [])]

        return ReflectionArc(
            name=data["name"],
            description=data.get("description"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            sessions=sessions,
        )

    def _deserialize_session(self, data: dict) -> SessionRecord:
        """Desserializa uma sessão de um dicionário.

        Args:
            data: Dicionário com dados da sessão.

        Returns:
            SessionRecord hydrated.
        """
        from datetime import datetime

        return SessionRecord(
            session_id=data["session_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            arc_name=data.get("arc_name"),
            input_content=data.get("input_content", ""),
            format=data.get("format", "text"),
            keywords=data.get("keywords", []),
            themes=data.get("themes", []),
            cards=data.get("cards", []),
            diagnosis=data.get("diagnosis", ""),
            risks=data.get("risks", []),
            decisions=data.get("decisions", []),
        )