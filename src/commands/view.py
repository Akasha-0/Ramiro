"""Módulo de comando view — Exibe relatórios salvos.

Este módulo contém a lógica para exibir relatórios de sessões
anteriores armazenadas no banco de dados SQLite.
"""

import logging
import sys
from typing import Optional

from src.database import SessionDB, DatabaseError

logger = logging.getLogger(__name__)


def run_view(session_id: int) -> bool:
    """Exibe o relatório salvo de uma sessão específica.

    Args:
        session_id: ID da sessão cujo relatório será exibido.

    Returns:
        True se o relatório foi exibido com sucesso, False caso contrário.

    Raises:
        SystemExit: Em caso de erro ou sessão não encontrada.
    """
    logger.info("Exibindo relatório da sessão %d", session_id)

    try:
        db = SessionDB()
        session = db.get_session(session_id)

        if session is None:
            logger.warning("Sessão %d não encontrada", session_id)
            print(f"Erro: Sessão {session_id} não encontrada.", file=sys.stderr)
            sys.exit(1)

        # Verificar se há caminho de relatório salvo
        if not session.report_path:
            logger.warning("Sessão %d não tem relatório salvo", session_id)
            print(f"Erro: Sessão {session_id} não possui relatório salvo.", file=sys.stderr)
            sys.exit(1)

        # Ler e exibir o conteúdo do relatório
        try:
            with open(session.report_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            logger.error("Falha ao ler relatório %s: %s", session.report_path, e)
            print(f"Erro: Não foi possível ler o relatório em {session.report_path}", file=sys.stderr)
            sys.exit(1)

        # Exibir o relatório
        print(content)
        logger.info("Relatório da sessão %d exibido com sucesso", session_id)
        return True

    except DatabaseError as e:
        logger.error("Erro ao acessar banco de dados: %s", e)
        print(f"Erro ao acessar banco de dados: {e}", file=sys.stderr)
        raise SystemExit(1)