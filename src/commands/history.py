"""Módulo de comando history — Lista sessões anteriores.

Este módulo contém a lógica para exibir o histórico de sessões
de análise armazenadas no banco de dados SQLite.
"""

import logging
from typing import Optional

from src.database import SessionDB, DatabaseError
from src.types import SessionRecord

logger = logging.getLogger(__name__)


def format_session_line(session: SessionRecord) -> str:
    """Formata uma sessão para exibição em uma linha.

    Args:
        session: Registro da sessão a formatar.

    Returns:
        String formatada com data, ID e preview do texto.
    """
    import json

    # Formatar data para exibição legível
    timestamp = session.timestamp or ""
    if timestamp:
        #Converter ISO para formato legível: "10/05/2026 14:30"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            timestamp = dt.strftime("%d/%m/%Y %H:%M")
        except (ValueError, AttributeError):
            pass  # Manter formato original se falhar

    # Truncar texto longo
    preview = session.input_text[:60] if session.input_text else ""
    if len(session.input_text) > 60:
        preview += "..."

    # Extrair cartas do JSON
    cards_preview = ""
    try:
        cards_list = json.loads(session.cards or "[]")
        if cards_list:
            cards_preview = f" [{', '.join(cards_list[:3])}]"
            if len(cards_list) > 3:
                cards_preview = cards_preview.rstrip(", ") + "...]"
    except (json.JSONDecodeError, TypeError):
        pass

    session_id = session.id or "?"

    return f"[{session_id}] {timestamp} —{cards_preview} {preview}"


def run_history(
    search: Optional[str] = None,
    limit: int = 10,
) -> list[SessionRecord]:
    """Lista sessões anteriores do histórico.

    Args:
        search: Palavra-chave opcional para filtrar sessões.
        limit: Número máximo de sessões a exibir.

    Returns:
        Lista de SessionRecord encontrados (para testes).

    Raises:
        SystemExit: Em caso de erro do banco de dados.
    """
    logger.info("Listando histórico: search=%r, limit=%d", search, limit)

    try:
        db = SessionDB()
        sessions = db.get_sessions(search=search, limit=limit)

        if not sessions:
            print("Nenhuma sessão encontrada.")
            logger.info("Nenhuma sessão no histórico")
            return sessions

        # Exibir sessões
        print(f"{len(sessions)} sessão(ões) encontrada(s):\n")
        for session in sessions:
            line = format_session_line(session)
            print(line)

        logger.info("%d sessões exibidas", len(sessions))
        return sessions

    except DatabaseError as e:
        logger.error("Erro ao acessar banco de dados: %s", e)
        print(f"Erro ao acessar histórico: {e}", file=__import__("sys").stderr)
        raise SystemExit(1)