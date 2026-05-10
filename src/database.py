"""Módulo de banco de dados — Sistema de Clareza Simbólico-Estratégica.

Utiliza SQLite (sqlite3 do stdlib Python) para persistir histórico de sessões
de análise. Cada sessão armazena: timestamp, texto original, cartas sorteadas,
formato usado, e caminho do relatório salvo.

Nenhuma estrutura de dados solta é retornada — todos os resultados são
SessionRecord (types.py).
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.types import SessionRecord

logger = logging.getLogger(__name__)

# Caminho do banco de dados (na pasta data/)
_DB_DIR = Path("data")
_DB_PATH = _DB_DIR / "sessions.db"

# ----------------------------------------------------------------------
# Exceções
# ----------------------------------------------------------------------


class DatabaseError(Exception):
    """Exceção lançada quando operações do banco de dados falham.

    Attributes:
        message: Descrição legível do erro.
        details: Detalhes adicionais sobre a natureza do erro.
    """

    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
    ) -> None:
        self.message = message
        self.details = details
        full = message
        if details:
            full = f"{full}: {details}"
        super().__init__(full)


# ----------------------------------------------------------------------
# Função auxiliar de conexão
# ----------------------------------------------------------------------


def _get_connection() -> sqlite3.Connection:
    """Obtém conexão com o banco de dados.

    Returns:
        Conexão sqlite3 ativa.

    Raises:
        DatabaseError: Se não for possível conectar ao banco.
    """
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise DatabaseError(
            "Falha ao conectar ao banco de dados",
            details=str(e),
        )


# ----------------------------------------------------------------------
# Função de inicialização
# ----------------------------------------------------------------------


def init_db() -> None:
    """Inicializa o banco de dados criando a tabela de sessões se necessário.

    Cria o diretório data/ e o arquivo de banco de dados SQLite se não existirem.

    Raises:
        DatabaseError: Se não for possível criar o banco.
    """
    logger.debug("Inicializando banco de dados em %s", _DB_PATH)

    try:
        # Criar diretório data/ se não existir
        _DB_DIR.mkdir(parents=True, exist_ok=True)

        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    cards TEXT NOT NULL DEFAULT '[]',
                    format TEXT NOT NULL DEFAULT 'text',
                    report_path TEXT
                )
            """)
            conn.commit()
            logger.info("Banco de dados inicializado com sucesso")
        finally:
            conn.close()
    except DatabaseError:
        raise
    except sqlite3.Error as e:
        raise DatabaseError(
            "Falha ao inicializar banco de dados",
            details=str(e),
        )


# ----------------------------------------------------------------------
# Classe SessionDB
# ----------------------------------------------------------------------


class SessionDB:
    """Interface principal para operações no banco de dados de sessões.

    Encapsula todas as operações CRUD para sessões de análise.
    O banco é automaticamente inicializado no primeiro uso.

    Example:
        >>> db = SessionDB()
        >>> sessions = db.get_sessions()
        >>> db.save_session(
        ...     input_text="Preciso decidir sobre minha carreira",
        ...     cards=["Cruz", "Estrela"],
        ...     format="symbols"
        ... )
    """

    def __init__(self) -> None:
        """Inicializa a interface do banco de dados."""
        # Garantir que o banco existe
        if not _DB_PATH.exists():
            init_db()
        logger.debug("SessionDB pronto para uso")

    # ------------------------------------------------------------------
    # Operações CRUD
    # ------------------------------------------------------------------

    def save_session(
        self,
        input_text: str,
        cards: Optional[list[str]] = None,
        format: str = "text",
        report_path: Optional[str] = None,
    ) -> int:
        """Salva uma nova sessão no banco de dados.

        Args:
            input_text: Texto original da entrada do usuário.
            cards: Lista de nomes das cartas sorteadas (opcional).
            format: Formato usado ("text", "spread", "symbols").
            report_path: Caminho para o arquivo de relatório salvo (opcional).

        Returns:
            O ID da sessão recém-criada.

        Raises:
            DatabaseError: Se não for possível salvar a sessão.
        """
        cards_json = json.dumps(cards or [], ensure_ascii=False)
        timestamp = datetime.utcnow().isoformat()

        logger.debug(
            "Salvando sessão: format=%r, cards=%d",
            format,
            len(cards or []),
        )

        try:
            conn = _get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO sessions (timestamp, input_text, cards, format, report_path)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (timestamp, input_text, cards_json, format, report_path),
                )
                conn.commit()
                session_id = cursor.lastrowid
                logger.info("Sessão %d salva com sucesso", session_id)
                return session_id
            finally:
                conn.close()
        except sqlite3.Error as e:
            raise DatabaseError(
                "Falha ao salvar sessão",
                details=str(e),
            )

    def get_sessions(
        self,
        limit: Optional[int] = None,
        search: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> list[SessionRecord]:
        """Recupera sessões do banco de dados com filtros opcionais.

        Args:
            limit: Número máximo de sessões a retornar (padrão: sem limite).
            search: Filtra por texto que contenha a palavra-chave.
            since: Data mínima no formato ISO (inclusive).
            until: Data máxima no formato ISO (inclusive).

        Returns:
            Lista de SessionRecord ordenados por data decrescente.

        Raises:
            DatabaseError: Se não for possível recuperar as sessões.
        """
        query = "SELECT * FROM sessions WHERE 1=1"
        params: list[str] = []

        if search:
            query += " AND (input_text LIKE ? OR cards LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        if until:
            query += " AND timestamp <= ?"
            params.append(until)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        logger.debug("Recuperando sessões: search=%r, since=%r, until=%r, limit=%r",
                     search, since, until, limit)

        try:
            conn = _get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                sessions = []
                for row in rows:
                    cards_list = json.loads(row["cards"])
                    sessions.append(SessionRecord(
                        id=row["id"],
                        timestamp=row["timestamp"],
                        input_text=row["input_text"],
                        cards=json.dumps(cards_list),
                        format=row["format"],
                        report_path=row["report_path"],
                    ))

                logger.debug("Recuperadas %d sessões", len(sessions))
                return sessions
            finally:
                conn.close()
        except sqlite3.Error as e:
            raise DatabaseError(
                "Falha ao recuperar sessões",
                details=str(e),
            )

    def get_session(self, session_id: int) -> Optional[SessionRecord]:
        """Recupera uma sessão específica pelo ID.

        Args:
            session_id: ID da sessão a recuperar.

        Returns:
            SessionRecord se encontrado, ou None se não existir.

        Raises:
            DatabaseError: Se não for possível recuperar a sessão.
        """
        logger.debug("Recuperando sessão %d", session_id)

        try:
            conn = _get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM sessions WHERE id = ?",
                    (session_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                cards_list = json.loads(row["cards"])
                return SessionRecord(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    input_text=row["input_text"],
                    cards=json.dumps(cards_list),
                    format=row["format"],
                    report_path=row["report_path"],
                )
            finally:
                conn.close()
        except sqlite3.Error as e:
            raise DatabaseError(
                "Falha ao recuperar sessão",
                details=str(e),
            )

    def delete_session(self, session_id: int) -> bool:
        """Remove uma sessão do banco de dados.

        Args:
            session_id: ID da sessão a remover.

        Returns:
            True se a sessão foi removida, False se não existed.

        Raises:
            DatabaseError: Se não for possível remover a sessão.
        """
        logger.debug("Removendo sessão %d", session_id)

        try:
            conn = _get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM sessions WHERE id = ?",
                    (session_id,),
                )
                conn.commit()
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info("Sessão %d removida", session_id)
                return deleted
            finally:
                conn.close()
        except sqlite3.Error as e:
            raise DatabaseError(
                "Falha ao remover sessão",
                details=str(e),
            )
