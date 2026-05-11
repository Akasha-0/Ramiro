"""Módulo de persistência de sessões via JSON.

Define a classe SessionStorage que gerencia o armazenamento e
recuperação de sessões (Session) em arquivos JSON no sistema de arquivos.

Cada sessão é salva como um arquivo JSON отдельный, facilitando
a organização e a busca individual.
"""

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from src.types import Session

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Exceções
# ----------------------------------------------------------------------


class SessionStorageError(Exception):
    """Raised when session storage operations fail."""

    pass


class SessionNotFoundError(SessionStorageError):
    """Raised when a requested session does not exist."""

    pass


# ----------------------------------------------------------------------
# SessionStorage
# ----------------------------------------------------------------------


class SessionStorage:
    """Gerenciador de persistência de sessões em arquivos JSON.

    Cada sessão é armazenada em um arquivo отдельный com nome
    `<session_id>.json` dentro do diretório configurado.

    Attributes:
        storage_dir: Caminho do diretório de armazenamento.
        _sessions_cache: Cache em memória das sessões carregadas.

    Example:
        >>> storage = SessionStorage("./data/sessions")
        >>> storage.save_session(session)
        >>> sessions = storage.list_sessions()
        >>> session = storage.load_session("abc123")
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        """Inicializa o gerenciador de sessões.

        Args:
            storage_dir: Diretório para armazenar os arquivos JSON.
                         Se None, usa ./data/sessions dentro do pacote.
        """
        if storage_dir is None:
            base_dir = Path(__file__).parent.parent
            storage_dir = base_dir / "data" / "sessions"

        self.storage_dir = Path(storage_dir)
        self._sessions_cache: dict[str, Session] = {}
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Garante que o diretório de armazenamento existe.

        Raises:
            SessionStorageError: Se o diretório não puder ser criado.
        """
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Diretório de armazenamento: %s", self.storage_dir)
        except OSError as e:
            raise SessionStorageError(
                f"Não foi possível criar diretório de armazenamento: {self.storage_dir}"
            ) from e

    def _get_session_path(self, session_id: str) -> Path:
        """Retorna o caminho do arquivo JSON para uma sessão.

        Args:
            session_id: Identificador único da sessão.

        Returns:
            Path para o arquivo JSON da sessão.
        """
        return self.storage_dir / f"{session_id}.json"

    def _session_to_dict(self, session: Session) -> dict:
        """Converte uma sessão para dicionário serializável em JSON.

        Args:
            session: Instância de Session a converter.

        Returns:
            Dicionário representando a sessão.
        """
        data = asdict(session)
        # Remove campos None para JSON mais limpo
        return {k: v for k, v in data.items() if v is not None}

    def _dict_to_session(self, data: dict) -> Session:
        """Converte um dicionário para uma instância de Session.

        Args:
            data: Dicionário com dados da sessão.

        Returns:
            Instância de Session reconstruída.

        Raises:
            SessionStorageError: Se os dados forem inválidos.
        """
        required_fields = ["session_id", "timestamp", "input_format", "raw_content"]
        for field in required_fields:
            if field not in data:
                raise SessionStorageError(
                    f"Dados de sessão incompletos: campo '{field}' ausente"
                )

        return Session(
            session_id=str(data["session_id"]),
            timestamp=str(data["timestamp"]),
            input_format=str(data["input_format"]),
            raw_content=str(data["raw_content"]),
            analysis_result=data.get("analysis_result"),
            unresolved_threads=data.get("unresolved_threads", []),
            tags=data.get("tags", []),
        )

    def save_session(self, session: Session) -> None:
        """Salva uma sessão no armazenamento.

        Args:
            session: Instância de Session a salvar.

        Raises:
            SessionStorageError: Se a escrita falhar.
        """
        session_path = self._get_session_path(session.session_id)

        try:
            data = self._session_to_dict(session)
            with open(session_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atualiza cache
            self._sessions_cache[session.session_id] = session
            logger.debug("Sessão salva: %s", session.session_id)

        except OSError as e:
            raise SessionStorageError(
                f"Falha ao salvar sessão {session.session_id}: {e}"
            ) from e
        except (TypeError, ValueError) as e:
            raise SessionStorageError(
                f"Dados inválidos para sessão {session.session_id}: {e}"
            ) from e

    def load_session(self, session_id: str) -> Session:
        """Carrega uma sessão do armazenamento.

        Args:
            session_id: Identificador único da sessão.

        Returns:
            Instância de Session carregada.

        Raises:
            SessionNotFoundError: Se a sessão não existir.
            SessionStorageError: Se a leitura falhar.
        """
        # Verifica cache primeiro
        if session_id in self._sessions_cache:
            logger.debug("Sessão encontrada em cache: %s", session_id)
            return self._sessions_cache[session_id]

        session_path = self._get_session_path(session_id)

        if not session_path.exists():
            raise SessionNotFoundError(f"Sessão não encontrada: {session_id}")

        try:
            with open(session_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            session = self._dict_to_session(data)

            # Atualiza cache
            self._sessions_cache[session_id] = session
            logger.debug("Sessão carregada: %s", session_id)

            return session

        except json.JSONDecodeError as e:
            raise SessionStorageError(
                f"JSON inválido na sessão {session_id}: {e}"
            ) from e
        except OSError as e:
            raise SessionStorageError(
                f"Falha ao carregar sessão {session_id}: {e}"
            ) from e

    def delete_session(self, session_id: str) -> None:
        """Remove uma sessão do armazenamento.

        Args:
            session_id: Identificador único da sessão.

        Raises:
            SessionNotFoundError: Se a sessão não existir.
            SessionStorageError: Se a remoção falhar.
        """
        session_path = self._get_session_path(session_id)

        if not session_path.exists():
            raise SessionNotFoundError(f"Sessão não encontrada para deletion: {session_id}")

        try:
            session_path.unlink()

            # Remove do cache
            self._sessions_cache.pop(session_id, None)
            logger.debug("Sessão removida: %s", session_id)

        except OSError as e:
            raise SessionStorageError(
                f"Falha ao remover sessão {session_id}: {e}"
            ) from e

    def list_sessions(self) -> list[Session]:
        """Lista todas as sessões armazenadas.

        Returns:
            Lista de instâncias de Session ordenadas por timestamp (mais recente primeiro).
        """
        sessions: list[Session] = []

        if not self.storage_dir.exists():
            logger.debug("Diretório de armazenamento não existe: %s", self.storage_dir)
            return sessions

        for file_path in self.storage_dir.glob("*.json"):
            session_id = file_path.stem
            try:
                session = self.load_session(session_id)
                sessions.append(session)
            except (SessionNotFoundError, SessionStorageError) as e:
                logger.warning("Erro ao carregar sessão %s: %s", session_id, e)
                continue

        # Ordena por timestamp (mais recente primeiro)
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        logger.debug("Listadas %d sessões", len(sessions))

        return sessions

    def list_sessions_by_tag(self, tag: str) -> list[Session]:
        """Lista sessões filtradas por tag.

        Args:
            tag: Tag para filtrar as sessões (case-insensitive).

        Returns:
            Lista de sessões que contain a tag especificada.
        """
        all_sessions = self.list_sessions()
        normalized_tag = tag.lower().strip()

        filtered = [
            session
            for session in all_sessions
            if any(t.lower().strip() == normalized_tag for t in session.tags)
        ]

        logger.debug("Encontradas %d sessões com tag '%s'", len(filtered), tag)
        return filtered

    def get_session_count(self) -> int:
        """Retorna o número de sessões armazenadas.

        Returns:
            Contagem de sessões.
        """
        if not self.storage_dir.exists():
            return 0

        count = len(list(self.storage_dir.glob("*.json")))
        logger.debug("Total de sessões: %d", count)
        return count

    def clear_cache(self) -> None:
        """Limpa o cache em memória de sessões carregadas.

        Útil para forçar re-leitura do disco.
        """
        self._sessions_cache.clear()
        logger.debug("Cache de sessões limpo")

    def session_exists(self, session_id: str) -> bool:
        """Verifica se uma sessão existe no armazenamento.

        Args:
            session_id: Identificador único da sessão.

        Returns:
            True se a sessão existir, False caso contrário.
        """
        session_path = self._get_session_path(session_id)
        exists = session_path.exists()

        # Também verifica cache
        if not exists and session_id in self._sessions_cache:
            exists = True

        return exists