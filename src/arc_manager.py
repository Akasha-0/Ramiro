"""Gerenciador de arcos de reflexão — Sistema de Clareza Simbólico-Estratégica.

Módulo que orquestra operações de arcos de reflexão:
- Criação de novos arcos
- Adição de sessões a arcos existentes
- Listagem e retrieval de arcos
- Geração de sumários de arcos

Trabalha em conjunto com ArcStorage para persistência.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from src.arc_storage import ArcStorage
from src.types import ArcSummary, ReflectionArc, SessionRecord, StructuredInput, AnalysisResult

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Exceções
# ----------------------------------------------------------------------


class ArcManagerError(Exception):
    """Exceção lançada quando operações do ArcManager falham.

    Attributes:
        message: Descrição legível do erro.
        arc_name: Nome do arco envolvido (se aplicável).
        details: Detalhes adicionais sobre a natureza do erro.
    """

    def __init__(
        self,
        message: str,
        arc_name: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        self.message = message
        self.arc_name = arc_name
        self.details = details
        full = message
        if arc_name:
            full = f"{message} (arc: {arc_name})"
        if details:
            full = f"{full}: {details}"
        super().__init__(full)


# ----------------------------------------------------------------------
# Gerenciador principal
# ----------------------------------------------------------------------


class ArcManager:
    """Gerenciador de operações para arcos de reflexão.

    Orquestra a criação, atualização e consulta de arcos de reflexão.
    Utiliza ArcStorage para persistência e mantém cache em memória
    para performance em operações repetidas.

    Attributes:
        storage: Instância de ArcStorage para persistência.
        _arc_cache: Cache em memória de arcos carregados.
    """

    def __init__(self, storage: Optional[ArcStorage] = None) -> None:
        """Inicializa o ArcManager.

        Args:
            storage: Instância de ArcStorage (cria nova se não fornecida).
        """
        self._storage = storage or ArcStorage()
        self._arc_cache: dict[str, ReflectionArc] = {}
        logger.debug("ArcManager inicializado")

    # ------------------------------------------------------------------
    # API pública - Operações de arco
    # ------------------------------------------------------------------

    def create_arc(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> ReflectionArc:
        """Cria um novo arco de reflexão.

        Args:
            name: Nome único do arco.
            description: Descrição opcional do arco.

        Returns:
            ReflectionArc recém-criado.

        Raises:
            ArcManagerError: Se um arco com o mesmo nome já existir.
        """
        logger.info("Criando arco: %s", name)

        # Verificar se já existe
        existing = self._storage.get_arc(name)
        if existing is not None:
            raise ArcManagerError(
                f"Arco já existe: {name}",
                arc_name=name,
            )

        arc = ReflectionArc(
            name=name,
            description=description,
            sessions=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self._storage.save_arc(arc)
        self._arc_cache[name] = arc

        logger.info("Arco criado: %s", name)
        return arc

    def get_or_create_arc(self, name: str) -> ReflectionArc:
        """Retorna arco existente ou cria novo com o nome fornecido.

        Args:
            name: Nome do arco.

        Returns:
            ReflectionArc existente ou recém-criado.
        """
        logger.debug("Get or create arc: %s", name)

        existing = self._storage.get_arc(name)
        if existing is not None:
            self._arc_cache[name] = existing
            return existing

        return self.create_arc(name)

    def get_arc(self, name: str) -> Optional[ReflectionArc]:
        """Recupera um arco pelo nome.

        Args:
            name: Nome do arco a recuperar.

        Returns:
            ReflectionArc se encontrado, None caso contrário.
        """
        # Verificar cache primeiro
        if name in self._arc_cache:
            return self._arc_cache[name]

        arc = self._storage.get_arc(name)
        if arc is not None:
            self._arc_cache[name] = arc

        return arc

    def list_arcs(self) -> list[ReflectionArc]:
        """Lista todos os arcos de reflexão.

        Returns:
            Lista de todos os arcos ordenados por atualização recente.
        """
        logger.debug("Listando arcos")
        return self._storage.list_arcs()

    def delete_arc(self, name: str) -> bool:
        """Remove um arco de reflexão.

        Args:
            name: Nome do arco a remover.

        Returns:
            True se o arco foi removido, False se não existia.
        """
        logger.info("Removendo arco: %s", name)

        # Limpar cache
        if name in self._arc_cache:
            del self._arc_cache[name]

        result = self._storage.delete_arc(name)
        if result:
            logger.info("Arco removido: %s", name)
        else:
            logger.debug("Arco não encontrado para remoção: %s", name)

        return result

    # ------------------------------------------------------------------
    # API pública - Operações de sessão
    # ------------------------------------------------------------------

    def add_session(
        self,
        arc_name: str,
        input_data: StructuredInput,
        analysis_result: AnalysisResult,
    ) -> SessionRecord:
        """Adiciona uma sessão de reflexão a um arco.

        Cria um novo arco se não existir, ou adiciona a um existente.

        Args:
            arc_name: Nome do arco.
            input_data: Input estruturado da sessão.
            analysis_result: Resultado da análise da sessão.

        Returns:
            SessionRecord criado.

        Raises:
            ArcManagerError: Se houver erro ao adicionar sessão.
        """
        logger.info("Adicionando sessão ao arco: %s", arc_name)

        # Obter ou criar arco
        arc = self.get_or_create_arc(arc_name)

        # Extrair dados para sessão
        keywords = input_data.keywords or []
        cards = [c.card_name for c in (input_data.cards or [])]

        session = SessionRecord(
            session_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            arc_name=arc_name,
            input_content=input_data.raw_content,
            format=input_data.format,
            keywords=keywords,
            themes=analysis_result.themes,
            cards=cards,
            diagnosis=analysis_result.diagnosis,
            risks=analysis_result.risks,
            decisions=analysis_result.decisions,
        )

        arc.sessions.append(session)
        self._storage.save_arc(arc)

        # Atualizar cache
        self._arc_cache[arc_name] = arc

        logger.info(
            "Sessão %s adicionada ao arco %s (total: %d)",
            session.session_id,
            arc_name,
            len(arc.sessions),
        )

        return session

    def get_session(self, arc_name: str, session_id: str) -> Optional[SessionRecord]:
        """Recupera uma sessão específica de um arco.

        Args:
            arc_name: Nome do arco.
            session_id: ID da sessão.

        Returns:
            SessionRecord se encontrado, None caso contrário.
        """
        arc = self.get_arc(arc_name)
        if arc is None:
            return None

        for session in arc.sessions:
            if session.session_id == session_id:
                return session

        return None

    def get_arc_sessions(self, arc_name: str) -> list[SessionRecord]:
        """Retorna todas as sessões de um arco.

        Args:
            arc_name: Nome do arco.

        Returns:
            Lista de sessões (vazia se arco não existir).
        """
        arc = self.get_arc(arc_name)
        if arc is None:
            return []

        return arc.sessions

    # ------------------------------------------------------------------
    # API pública - Sumários
    # ------------------------------------------------------------------

    def generate_arc_summary(self, arc_name: str) -> Optional[ArcSummary]:
        """Gera sumário estatístico de um arco de reflexão.

        Args:
            arc_name: Nome do arco.

        Returns:
            ArcSummary com estatísticas ou None se arco não existir.
        """
        logger.info("Gerando sumário para arco: %s", arc_name)

        arc = self.get_arc(arc_name)
        if arc is None:
            logger.debug("Arco não encontrado para sumário: %s", arc_name)
            return None

        if not arc.sessions:
            logger.debug("Arco sem sessões: %s", arc_name)
            return ArcSummary(
                arc_name=arc_name,
                total_sessions=0,
                date_range=None,
                top_themes=[],
                top_cards=[],
                session_ids=[],
            )

        # Calcular date range
        timestamps = [s.timestamp for s in arc.sessions]
        date_range = (min(timestamps), max(timestamps))

        # Calcular temas mais frequentes (top 3)
        theme_counts: dict[str, int] = {}
        for session in arc.sessions:
            for theme in session.themes:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1

        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        top_themes = [t for t, _ in sorted_themes[:3]]

        # Calcular cartas mais frequentes (top 3)
        card_counts: dict[str, int] = {}
        for session in arc.sessions:
            for card in session.cards:
                card_counts[card] = card_counts.get(card, 0) + 1

        sorted_cards = sorted(card_counts.items(), key=lambda x: x[1], reverse=True)
        top_cards = [c for c, _ in sorted_cards[:3]]

        # Coletar IDs de sessão
        session_ids = [s.session_id for s in arc.sessions]

        summary = ArcSummary(
            arc_name=arc_name,
            total_sessions=len(arc.sessions),
            date_range=date_range,
            top_themes=top_themes,
            top_cards=top_cards,
            session_ids=session_ids,
        )

        logger.info(
            "Sumário gerado: %s (%d sessões, %d temas, %d cartas)",
            arc_name,
            summary.total_sessions,
            len(top_themes),
            len(top_cards),
        )

        return summary

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def clear_cache(self) -> None:
        """Limpa o cache em memória de arcos."""
        self._arc_cache.clear()
        logger.debug("Cache limpo")

    def get_arc_stats(self, arc_name: str) -> Optional[dict]:
        """Retorna estatísticas resumidas de um arco.

        Args:
            arc_name: Nome do arco.

        Returns:
            Dicionário com estatísticas ou None se arco não existir.
        """
        arc = self.get_arc(arc_name)
        if arc is None:
            return None

        total_themes = sum(len(s.themes) for s in arc.sessions)
        total_risks = sum(len(s.risks) for s in arc.sessions)
        total_decisions = sum(len(s.decisions) for s in arc.sessions)

        return {
            "name": arc_name,
            "total_sessions": len(arc.sessions),
            "total_themes": total_themes,
            "total_risks": total_risks,
            "total_decisions": total_decisions,
            "created_at": arc.created_at.isoformat(),
            "updated_at": arc.updated_at.isoformat(),
            "description": arc.description,
        }