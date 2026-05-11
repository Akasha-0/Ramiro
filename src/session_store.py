"""Armazenamento de sessões — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por persistir e recuperar sessões de reflexão
usando JSON como formato de armazenamento. Cada sessão contém
o input do usuário, resultado da análise, e metadados.

O storage é baseado em arquivo JSON com suporte a:
- Persistência de sessões individuais
- Recuperação de histórico de sessões
- Rastreamento de threads narrativas entre sessões
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.types import Session, SessionContext, NarrativeThread, Arc

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Exceções
# ----------------------------------------------------------------------


class StorageError(Exception):
    """Exceção lançada quando operações de storage falham.

    Attributes:
        message: Descrição legível do erro.
        operation: Nome da operação que falhou (read/write/delete).
        details: Detalhes adicionais sobre a natureza do erro.
        recovery: Orientação de recuperação em português (opcional).
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[str] = None,
        recovery: Optional[str] = None,
    ) -> None:
        self.message = message
        self.operation = operation
        self.details = details
        self.recovery = recovery
        full = message
        if operation:
            full = f"{message} (operação: {operation})"
        if details:
            full = f"{full}: {details}"
        if recovery:
            full = f"{full}\nDica: {recovery}"
        super().__init__(full)


# ----------------------------------------------------------------------
# Storage de sessões
# ----------------------------------------------------------------------


class SessionStore:
    """Armazenamento de sessões com persistência JSON.

    Gerencia o ciclo de vida de sessões de reflexão, incluindo:
    - Criação de novas sessões
    - Persistência em arquivo JSON
    - Recuperação de sessões por ID
    - Listagem de sessões existentes

    Attributes:
        storage_path: Caminho para o arquivo de storage JSON.
        auto_save: Se True, salva automaticamente após cada operação.
    """

    _DEFAULT_FILENAME = "sessions.json"

    def __init__(
        self,
        storage_path: Optional[str] = None,
        auto_save: bool = True,
    ) -> None:
        """Inicializa o storage de sessões.

        Args:
            storage_path: Caminho para o arquivo JSON. Se None, usa
                sessions.json no diretório de dados.
            auto_save: Se True, salva automaticamente após cada modificação.
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Usar diretório de dados padrão
            data_dir = Path("data")
            self.storage_path = data_dir / self._DEFAULT_FILENAME

        self.auto_save = auto_save
        self._sessions: dict[str, Session] = {}
        self._load()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def create_session(
        self,
        raw_content: str,
        input_format: str,
        session_id: Optional[str] = None,
    ) -> Session:
        """Cria uma nova sessão.

        Args:
            raw_content: Conteúdo bruto original do usuário.
            input_format: Formato do input ("text", "spread", "symbols").
            session_id: ID opcional. Se None, gera UUID automaticamente.

        Returns:
            Nova sessão criada com ID único.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        timestamp = datetime.now().isoformat()

        session = Session(
            session_id=session_id,
            timestamp=timestamp,
            input_format=input_format,
            raw_content=raw_content,
            analysis_result=None,
            unresolved_threads=[],
        )

        self._sessions[session_id] = session
        logger.info("Sessão criada: %s", session_id)

        if self.auto_save:
            self._save()

        return session

    def save_session(self, session: Session) -> None:
        """Salva uma sessão no storage.

        Args:
            session: Sessão a ser persistida.
        """
        self._sessions[session.session_id] = session
        logger.debug("Sessão salva: %s", session.session_id)

        if self.auto_save:
            self._save()

    def get_session(self, session_id: str) -> Optional[Session]:
        """Recupera uma sessão pelo ID.

        Args:
            session_id: ID da sessão a recuperar.

        Returns:
            Sessão encontrada ou None se não existir.
        """
        session = self._sessions.get(session_id)
        if session is None:
            logger.debug("Sessão não encontrada: %s", session_id)
        return session

    def list_sessions(self) -> list[Session]:
        """Lista todas as sessões ordenadas por timestamp.

        Returns:
            Lista de sessões ordenadas da mais antiga para a mais recente.
        """
        sessions = list(self._sessions.values())
        sessions.sort(key=lambda s: s.timestamp)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Remove uma sessão do storage.

        Args:
            session_id: ID da sessão a remover.

        Returns:
            True se a sessão foi removida, False se não existia.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Sessão removida: %s", session_id)

            if self.auto_save:
                self._save()

            return True

        logger.debug("Tentativa de remover sessão inexistente: %s", session_id)
        return False

    def session_exists(self, session_id: str) -> bool:
        """Verifica se uma sessão existe.

        Args:
            session_id: ID da sessão a verificar.

        Returns:
            True se a sessão existe, False caso contrário.
        """
        return session_id in self._sessions

    def get_session_count(self) -> int:
        """Retorna o número de sessões armazenadas.

        Returns:
            Quantidade de sessões no storage.
        """
        return len(self._sessions)

    def get_sessions_by_tag(self, tag: str) -> list[Session]:
        """Retorna sessões filtradas por tag.

        Args:
            tag: Tag para filtrar as sessões.

        Returns:
            Lista de sessões que possuem a tag especificada,
            ordenadas por timestamp.
        """
        matching = [
            session for session in self._sessions.values()
            if tag.lower() in [t.lower() for t in session.tags]
        ]
        matching.sort(key=lambda s: s.timestamp)
        logger.debug("Sessões com tag '%s': %d", tag, len(matching))
        return matching

    # ------------------------------------------------------------------
    # Persistência JSON
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Carrega sessões do arquivo JSON.

        Cria o arquivo se não existir.
        """
        if not self.storage_path.exists():
            logger.debug("Arquivo de storage não existe, criando: %s", self.storage_path)
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._save()
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._sessions = self._deserialize_sessions(data)
            logger.info("Carregadas %d sessões do storage", len(self._sessions))

        except json.JSONDecodeError as e:
            logger.warning("Arquivo JSON corrompido, iniciando novo storage: %s", e)
            self._sessions = {}

        except PermissionError:
            raise StorageError(
                "Sem permissão para ler o arquivo",
                operation="load",
                details=str(self.storage_path),
                recovery="Verifique as permissões do arquivo de storage.",
            )

        except OSError as e:
            raise StorageError(
                "Erro ao ler arquivo de storage",
                operation="load",
                details=str(e),
                recovery="Verifique se o arquivo de storage não está corrompido.",
            )

    def _save(self) -> None:
        """Salva sessões no arquivo JSON."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(
                    self._serialize_sessions(self._sessions),
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            logger.debug("Storage salvo: %s", self.storage_path)

        except PermissionError:
            raise StorageError(
                "Sem permissão para salvar",
                operation="save",
                details=str(self.storage_path),
                recovery="Verifique as permissões do diretório de storage.",
            )

        except OSError as e:
            raise StorageError(
                "Erro ao salvar arquivo de storage",
                operation="save",
                details=str(e),
                recovery="Verifique se há espaço em disco suficiente.",
            )

    def _serialize_sessions(self, sessions: dict[str, Session]) -> dict:
        """Serializa sessões para formato JSON.

        Args:
            sessions: Dicionário de sessões.

        Returns:
            Dicionário serializado para JSON.
        """
        return {
            session_id: self._session_to_dict(session)
            for session_id, session in sessions.items()
        }

    def _deserialize_sessions(self, data: dict) -> dict[str, Session]:
        """Desserializa sessões de formato JSON.

        Args:
            data: Dicionário JSON com sessões.

        Returns:
            Dicionário de sessões reconstruídas.
        """
        sessions: dict[str, Session] = {}

        for session_id, session_data in data.items():
            try:
                sessions[session_id] = self._dict_to_session(session_data)
            except (KeyError, TypeError, ValueError) as e:
                logger.warning(
                    "Sessão com dados inválidos ignorada: %s - %s",
                    session_id,
                    e,
                )

        return sessions

    def _session_to_dict(self, session: Session) -> dict:
        """Converte sessão para dicionário serializável.

        Args:
            session: Sessão a converter.

        Returns:
            Dicionário com dados da sessão.
        """
        data = {
            "session_id": session.session_id,
            "timestamp": session.timestamp,
            "input_format": session.input_format,
            "raw_content": session.raw_content,
            "unresolved_threads": session.unresolved_threads,
            "tags": session.tags,
        }

        # Serialize analysis_result if present
        if session.analysis_result is not None:
            analysis = session.analysis_result
            data["analysis_result"] = {
                "diagnosis": analysis.diagnosis,
                "themes": analysis.themes,
                "risks": analysis.risks,
                "decisions": analysis.decisions,
                "practical_plan": analysis.practical_plan,
                "card_interpretations": analysis.card_interpretations,
                "symbolic_mappings": analysis.symbolic_mappings,
            }

        return data

    def _dict_to_session(self, data: dict) -> Session:
        """Converte dicionário para sessão.

        Args:
            data: Dicionário com dados da sessão.

        Returns:
            Sessão reconstruída.
        """
        from src.types import AnalysisResult

        # Deserialize analysis_result if present
        analysis_result = None
        if "analysis_result" in data and data["analysis_result"] is not None:
            ar_data = data["analysis_result"]
            analysis_result = AnalysisResult(
                diagnosis=ar_data.get("diagnosis", ""),
                themes=ar_data.get("themes", []),
                risks=ar_data.get("risks", []),
                decisions=ar_data.get("decisions", []),
                practical_plan=ar_data.get("practical_plan", ""),
                card_interpretations=ar_data.get("card_interpretations"),
                symbolic_mappings=ar_data.get("symbolic_mappings"),
            )

        return Session(
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            input_format=data["input_format"],
            raw_content=data["raw_content"],
            analysis_result=analysis_result,
            unresolved_threads=data.get("unresolved_threads", []),
            tags=data.get("tags", []),
        )
