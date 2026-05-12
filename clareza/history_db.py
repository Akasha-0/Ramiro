"""Histórico de sessões — Sistema de Clareza Simbólico-Estratégica.

Módulo de persistência para sessões de reflexão usando arquivos JSON.
Permite salvar, carregar e gerenciar sessões anteriores.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .types import Session, NarrativeThread, Arc, ChapterSummary, SessionAnnotation

logger = logging.getLogger(__name__)

# Nome do arquivo de índice de sessões
SESSIONS_INDEX_FILENAME = "sessions_index.json"

# Nome do arquivo de threads narrativas
THREADS_FILENAME = "threads.json"

# Nome do arquivo de arcos narrativos
ARCS_FILENAME = "arcs.json"

# Nome do arquivo de capítulos
CHAPTERS_FILENAME = "chapters.json"

# Nome do arquivo de anotações
ANNOTATIONS_FILENAME = "annotations.json"


class HistoryDBError(Exception):
    """Erro genérico do HistoryDB."""

    pass


class SessionNotFoundError(HistoryDBError):
    """Sessão não encontrada no banco de dados."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Sessão não encontrada: {session_id}")


class HistoryDB:
    """Banco de dados de histórico de sessões.

    Gerencia persistência de sessões, threads narrativas, arcos e capítulos
    usando arquivos JSON no diretório especificado.

    Attributes:
        data_dir: Diretório onde os arquivos JSON são armazenados.
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        """Inicializa o HistoryDB.

        Args:
            data_dir: Diretório para armazenar dados. Se None, usa
                      ~/.local/share/clareza/sessions.
        """
        if data_dir is None:
            data_dir = Path.home() / ".local" / "share" / "clareza" / "sessions"

        self.data_dir = Path(data_dir)
        self._ensure_data_dir()
        self._sessions_index_path = self.data_dir / SESSIONS_INDEX_FILENAME
        self._threads_path = self.data_dir / THREADS_FILENAME
        self._arcs_path = self.data_dir / ARCS_FILENAME
        self._chapters_path = self.data_dir / CHAPTERS_FILENAME
        self._annotations_path = self.data_dir / ANNOTATIONS_FILENAME

        logger.debug("HistoryDB inicializado em: %s", self.data_dir)

    def _ensure_data_dir(self) -> None:
        """Garante que o diretório de dados existe."""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Diretório de dados criado: %s", self.data_dir)

    def _serialize_session(self, session: Session) -> dict:
        """Serializa uma sessão para dicionário.

        Args:
            session: Sessão a serializar.

        Returns:
            Dicionário representando a sessão.
        """
        data = {
            "session_id": session.session_id,
            "timestamp": session.timestamp,
            "input_format": session.input_format,
            "raw_content": session.raw_content,
            "unresolved_threads": session.unresolved_threads,
            "annotations": [
                {
                    "annotation_id": a.annotation_id,
                    "session_id": a.session_id,
                    "milestone_id": a.milestone_id,
                    "content": a.content,
                    "timestamp": a.timestamp,
                    "theme_tags": a.theme_tags,
                    "linked_thread_ids": a.linked_thread_ids,
                    "is_milestone_completed": a.is_milestone_completed,
                }
                for a in session.annotations
            ],
        }

        if session.analysis_result is not None:
            ar = session.analysis_result
            data["analysis_result"] = {
                "diagnosis": ar.diagnosis,
                "themes": ar.themes,
                "risks": ar.risks,
                "decisions": ar.decisions,
                "practical_plan": ar.practical_plan,
                "card_interpretations": ar.card_interpretations,
                "symbolic_mappings": ar.symbolic_mappings,
                "cross_card_patterns": [
                    {
                        "pattern_type": p.pattern_type,
                        "card_ids": p.card_ids,
                        "interpretation": p.interpretation,
                        "strength": p.strength,
                    }
                    for p in ar.cross_card_patterns
                ],
            }

        return data

    def _deserialize_session(self, data: dict) -> Session:
        """Desserializa um dicionário para sessão.

        Args:
            data: Dicionário com dados da sessão.

        Returns:
            Session instanciada.
        """
        from .types import AnalysisResult, CrossCardPattern, SessionAnnotation

        analysis_result = None
        if "analysis_result" in data and data["analysis_result"] is not None:
            ar_data = data["analysis_result"]
            cross_patterns = [
                CrossCardPattern(
                    pattern_type=cp["pattern_type"],
                    card_ids=cp["card_ids"],
                    interpretation=cp["interpretation"],
                    strength=cp.get("strength"),
                )
                for cp in ar_data.get("cross_card_patterns", [])
            ]
            analysis_result = AnalysisResult(
                diagnosis=ar_data["diagnosis"],
                themes=ar_data.get("themes", []),
                risks=ar_data.get("risks", []),
                decisions=ar_data.get("decisions", []),
                practical_plan=ar_data.get("practical_plan", ""),
                card_interpretations=ar_data.get("card_interpretations"),
                symbolic_mappings=ar_data.get("symbolic_mappings"),
                cross_card_patterns=cross_patterns,
            )

        # Deserialize annotations
        annotations = []
        for ann_data in data.get("annotations", []):
            annotations.append(SessionAnnotation(
                annotation_id=ann_data["annotation_id"],
                session_id=ann_data["session_id"],
                milestone_id=ann_data["milestone_id"],
                content=ann_data["content"],
                timestamp=ann_data["timestamp"],
                theme_tags=ann_data.get("theme_tags", []),
                linked_thread_ids=ann_data.get("linked_thread_ids", []),
                is_milestone_completed=ann_data.get("is_milestone_completed", False),
            ))

        return Session(
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            input_format=data["input_format"],
            raw_content=data["raw_content"],
            analysis_result=analysis_result,
            unresolved_threads=data.get("unresolved_threads", []),
            annotations=annotations,
        )

    def save_session(self, session: Session) -> None:
        """Salva uma sessão no banco de dados.

        Args:
            session: Sessão a salvar.

        Raises:
            HistoryDBError: Se houver erro ao salvar.
        """
        try:
            # Carregar índice existente
            index = self._load_index()

            # Adicionar ou atualizar sessão no índice
            index[session.session_id] = {
                "timestamp": session.timestamp,
                "input_format": session.input_format,
                "file": f"{session.session_id}.json",
            }

            # Salvar índice atualizado
            self._save_index(index)

            # Salvar arquivo da sessão
            session_path = self.data_dir / f"{session.session_id}.json"
            session_data = self._serialize_session(session)
            with open(session_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            logger.info("Sessão salva: %s", session.session_id)

        except Exception as e:
            logger.error("Erro ao salvar sessão %s: %s", session.session_id, e)
            raise HistoryDBError(f"Falha ao salvar sessão: {e}") from e

    def load_session(self, session_id: str) -> Session:
        """Carrega uma sessão pelo ID.

        Args:
            session_id: ID da sessão a carregar.

        Returns:
            Sessão carregada.

        Raises:
            SessionNotFoundError: Se a sessão não existir.
            HistoryDBError: Se houver erro ao carregar.
        """
        session_path = self.data_dir / f"{session_id}.json"

        if not session_path.exists():
            logger.warning("Sessão não encontrada: %s", session_id)
            raise SessionNotFoundError(session_id)

        try:
            with open(session_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            session = self._deserialize_session(data)
            logger.debug("Sessão carregada: %s", session_id)
            return session

        except json.JSONDecodeError as e:
            logger.error("Erro ao decodificar sessão %s: %s", session_id, e)
            raise HistoryDBError(f"Arquivo de sessão corrompido: {e}") from e
        except Exception as e:
            logger.error("Erro ao carregar sessão %s: %s", session_id, e)
            raise HistoryDBError(f"Falha ao carregar sessão: {e}") from e

    def get_session(self, session_id: str) -> Optional[Session]:
        """Busca uma sessão pelo ID (alias para load_session).

        Args:
            session_id: ID da sessão a buscar.

        Returns:
            Sessão encontrada ou None se não existir.
        """
        try:
            return self.load_session(session_id)
        except SessionNotFoundError:
            return None

    def list_sessions(self, tag: Optional[str] = None) -> list[dict]:
        """Lista sessões no banco de dados, opcionalmente filtradas por tag/tema.

        Args:
            tag: Tag ou tema para filtrar sessões. Se None, retorna todas.
                 A filtragem verifica themes do analysis_result e theme_tags
                 das annotations da sessão (case-insensitive).

        Returns:
            Lista de dicionários com metadados das sessões filtradas.
        """
        index = self._load_index()
        sessions = []

        for session_id, info in index.items():
            # Se tag é especificada, precisamos carregar a sessão completa
            # para verificar themes e annotations
            if tag is not None:
                session = self.get_session(session_id)
                if session is None:
                    continue

                # Verificar se a tag está nos themes do analysis_result
                themes_match = False
                if session.analysis_result is not None:
                    themes_lower = [t.lower() for t in session.analysis_result.themes]
                    tag_lower = tag.lower()
                    if any(tag_lower in theme for theme in themes_lower):
                        themes_match = True

                # Verificar se a tag está nas theme_tags das annotations
                annotations_match = False
                for annotation in session.annotations:
                    tags_lower = [t.lower() for t in annotation.theme_tags]
                    if any(tag.lower() in t for t in tags_lower):
                        annotations_match = True
                        break

                # Incluir apenas se a tag estiver presente em themes ou annotations
                if not themes_match and not annotations_match:
                    continue

            sessions.append({
                "session_id": session_id,
                "timestamp": info.get("timestamp"),
                "input_format": info.get("input_format"),
            })

        # Ordenar por timestamp (mais recente primeiro)
        sessions.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> None:
        """Remove uma sessão do banco de dados.

        Args:
            session_id: ID da sessão a remover.

        Raises:
            SessionNotFoundError: Se a sessão não existir.
            HistoryDBError: Se houver erro ao remover.
        """
        session_path = self.data_dir / f"{session_id}.json"

        if not session_path.exists():
            raise SessionNotFoundError(session_id)

        try:
            # Remover arquivo da sessão
            session_path.unlink()

            # Atualizar índice
            index = self._load_index()
            if session_id in index:
                del index[session_id]
                self._save_index(index)

            logger.info("Sessão removida: %s", session_id)

        except Exception as e:
            logger.error("Erro ao remover sessão %s: %s", session_id, e)
            raise HistoryDBError(f"Falha ao remover sessão: {e}") from e

    def _load_index(self) -> dict:
        """Carrega o índice de sessões.

        Returns:
            Dicionário com índice de sessões.
        """
        if not self._sessions_index_path.exists():
            return {}

        try:
            with open(self._sessions_index_path, "r", encoding="utf-8") as f:
                return json.load(f) or {}
        except json.JSONDecodeError:
            logger.warning("Índice de sessões corrompido, criando novo")
            return {}
        except Exception as e:
            logger.error("Erro ao carregar índice: %s", e)
            return {}

    def _save_index(self, index: dict) -> None:
        """Salva o índice de sessões.

        Args:
            index: Dicionário com índice a salvar.
        """
        with open(self._sessions_index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    # ----------------------------------------------------------------------
    # Threads Narrativas
    # ----------------------------------------------------------------------

    def save_threads(self, threads: list[NarrativeThread]) -> None:
        """Salva threads narrativas.

        Args:
            threads: Lista de threads a salvar.

        Raises:
            HistoryDBError: Se houver erro ao salvar.
        """
        try:
            data = [
                {
                    "thread_id": t.thread_id,
                    "name": t.name,
                    "theme": t.theme,
                    "session_ids": t.session_ids,
                    "status": t.status,
                    "first_mention": t.first_mention,
                    "last_mention": t.last_mention,
                    "progression": t.progression,
                }
                for t in threads
            ]

            with open(self._threads_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("Threads salvas: %d", len(threads))

        except Exception as e:
            logger.error("Erro ao salvar threads: %s", e)
            raise HistoryDBError(f"Falha ao salvar threads: {e}") from e

    def load_threads(self) -> list[NarrativeThread]:
        """Carrega threads narrativas.

        Returns:
            Lista de threads carregadas.
        """
        if not self._threads_path.exists():
            return []

        try:
            with open(self._threads_path, "r", encoding="utf-8") as f:
                data = json.load(f) or []

            return [
                NarrativeThread(
                    thread_id=t["thread_id"],
                    name=t["name"],
                    theme=t["theme"],
                    session_ids=t.get("session_ids", []),
                    status=t.get("status", "active"),
                    first_mention=t.get("first_mention"),
                    last_mention=t.get("last_mention"),
                    progression=t.get("progression", []),
                )
                for t in data
            ]

        except Exception as e:
            logger.error("Erro ao carregar threads: %s", e)
            return []

    # ----------------------------------------------------------------------
    # Arcos Narrativos
    # ----------------------------------------------------------------------

    def save_arcs(self, arcs: list[Arc]) -> None:
        """Salva arcos narrativos.

        Args:
            arcs: Lista de arcos a salvar.

        Raises:
            HistoryDBError: Se houver erro ao salvar.
        """
        try:
            data = []

            for arc in arcs:
                arc_data = {
                    "arc_id": arc.arc_id,
                    "name": arc.name,
                    "start_date": arc.start_date,
                    "end_date": arc.end_date,
                    "dominant_themes": arc.dominant_themes,
                    "sessions": [
                        self._serialize_session(s) for s in arc.sessions
                    ],
                    "threads": [
                        {
                            "thread_id": t.thread_id,
                            "name": t.name,
                            "theme": t.theme,
                            "session_ids": t.session_ids,
                            "status": t.status,
                            "first_mention": t.first_mention,
                            "last_mention": t.last_mention,
                            "progression": t.progression,
                        }
                        for t in arc.threads
                    ],
                }
                data.append(arc_data)

            with open(self._arcs_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("Arcos salvos: %d", len(arcs))

        except Exception as e:
            logger.error("Erro ao salvar arcos: %s", e)
            raise HistoryDBError(f"Falha ao salvar arcos: {e}") from e

    def load_arcs(self) -> list[Arc]:
        """Carrega arcos narrativos.

        Returns:
            Lista de arcos carregados.
        """
        if not self._arcs_path.exists():
            return []

        try:
            with open(self._arcs_path, "r", encoding="utf-8") as f:
                data = json.load(f) or []

            arcs = []
            for arc_data in data:
                sessions = [self._deserialize_session(s) for s in arc_data.get("sessions", [])]
                threads = [
                    NarrativeThread(
                        thread_id=t["thread_id"],
                        name=t["name"],
                        theme=t["theme"],
                        session_ids=t.get("session_ids", []),
                        status=t.get("status", "active"),
                        first_mention=t.get("first_mention"),
                        last_mention=t.get("last_mention"),
                        progression=t.get("progression", []),
                    )
                    for t in arc_data.get("threads", [])
                ]
                arcs.append(Arc(
                    arc_id=arc_data["arc_id"],
                    name=arc_data["name"],
                    sessions=sessions,
                    threads=threads,
                    start_date=arc_data.get("start_date"),
                    end_date=arc_data.get("end_date"),
                    dominant_themes=arc_data.get("dominant_themes", []),
                ))

            return arcs

        except Exception as e:
            logger.error("Erro ao carregar arcos: %s", e)
            return []

    # ----------------------------------------------------------------------
    # Capítulos
    # ----------------------------------------------------------------------

    def save_chapters(self, chapters: list[ChapterSummary]) -> None:
        """Salva sumários de capítulos.

        Args:
            chapters: Lista de capítulos a salvar.

        Raises:
            HistoryDBError: Se houver erro ao salvar.
        """
        try:
            data = [
                {
                    "chapter_number": c.chapter_number,
                    "title": c.title,
                    "arc_id": c.arc_id,
                    "sessions_covered": c.sessions_covered,
                    "narrative_summary": c.narrative_summary,
                    "unresolved_threads": c.unresolved_threads,
                    "escalation_detected": c.escalation_detected,
                    "resolution_detected": c.resolution_detected,
                    "key_insight": c.key_insight,
                }
                for c in chapters
            ]

            with open(self._chapters_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("Capítulos salvos: %d", len(chapters))

        except Exception as e:
            logger.error("Erro ao salvar capítulos: %s", e)
            raise HistoryDBError(f"Falha ao salvar capítulos: {e}") from e

    def load_chapters(self) -> list[ChapterSummary]:
        """Carrega sumários de capítulos.

        Returns:
            Lista de capítulos carregados.
        """
        if not self._chapters_path.exists():
            return []

        try:
            with open(self._chapters_path, "r", encoding="utf-8") as f:
                data = json.load(f) or []

            return [
                ChapterSummary(
                    chapter_number=c["chapter_number"],
                    title=c["title"],
                    arc_id=c["arc_id"],
                    sessions_covered=c.get("sessions_covered", []),
                    narrative_summary=c.get("narrative_summary", ""),
                    unresolved_threads=c.get("unresolved_threads", []),
                    escalation_detected=c.get("escalation_detected", False),
                    resolution_detected=c.get("resolution_detected", False),
                    key_insight=c.get("key_insight", ""),
                )
                for c in data
            ]

        except Exception as e:
            logger.error("Erro ao carregar capítulos: %s", e)
            return []

    # ----------------------------------------------------------------------
    # Anotações de Sessão
    # ----------------------------------------------------------------------

    def save_annotations(self, annotations: list[SessionAnnotation]) -> None:
        """Salva anotações de sessão.

        Args:
            annotations: Lista de anotações a salvar.

        Raises:
            HistoryDBError: Se houver erro ao salvar.
        """
        try:
            data = [
                {
                    "annotation_id": a.annotation_id,
                    "session_id": a.session_id,
                    "milestone_id": a.milestone_id,
                    "content": a.content,
                    "timestamp": a.timestamp,
                    "theme_tags": a.theme_tags,
                    "linked_thread_ids": a.linked_thread_ids,
                    "is_milestone_completed": a.is_milestone_completed,
                }
                for a in annotations
            ]

            with open(self._annotations_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("Anotações salvas: %d", len(annotations))

        except Exception as e:
            logger.error("Erro ao salvar anotações: %s", e)
            raise HistoryDBError(f"Falha ao salvar anotações: {e}") from e

    def load_annotations(self) -> list[SessionAnnotation]:
        """Carrega todas as anotações.

        Returns:
            Lista de anotações carregadas.
        """
        if not self._annotations_path.exists():
            return []

        try:
            with open(self._annotations_path, "r", encoding="utf-8") as f:
                data = json.load(f) or []

            return [
                SessionAnnotation(
                    annotation_id=ann["annotation_id"],
                    session_id=ann["session_id"],
                    milestone_id=ann["milestone_id"],
                    content=ann["content"],
                    timestamp=ann["timestamp"],
                    theme_tags=ann.get("theme_tags", []),
                    linked_thread_ids=ann.get("linked_thread_ids", []),
                    is_milestone_completed=ann.get("is_milestone_completed", False),
                )
                for ann in data
            ]

        except Exception as e:
            logger.error("Erro ao carregar anotações: %s", e)
            return []

    def get_annotations_for_session(self, session_id: str) -> list[SessionAnnotation]:
        """Retorna todas as anotações de uma sessão específica.

        Args:
            session_id: ID da sessão.

        Returns:
            Lista de anotações da sessão.
        """
        all_annotations = self.load_annotations()
        return [a for a in all_annotations if a.session_id == session_id]

    def get_annotations_for_milestone(
        self, milestone_id: str
    ) -> list[SessionAnnotation]:
        """Retorna todas as anotações de um milestone específico.

        Args:
            milestone_id: ID do milestone.

        Returns:
            Lista de anotações do milestone.
        """
        all_annotations = self.load_annotations()
        return [a for a in all_annotations if a.milestone_id == milestone_id]

    def get_completed_milestones(self) -> list[str]:
        """Retorna IDs dos milestones marcados como concluídos.

        Returns:
            Lista de IDs de milestones concluídos.
        """
        all_annotations = self.load_annotations()
        return [
            a.milestone_id
            for a in all_annotations
            if a.is_milestone_completed
        ]

    def add_annotation(
        self,
        session_id: str,
        content: str,
        milestone_id: Optional[str] = None,
        theme_tags: Optional[list[str]] = None,
        linked_thread_ids: Optional[list[str]] = None,
        is_milestone_completed: bool = False,
    ) -> SessionAnnotation:
        """Adiciona uma anotação/reflexão a uma sessão.

        Args:
            session_id: ID da sessão à qual adicionar a anotação.
            content: Texto da reflexão/resposta do usuário.
            milestone_id: ID do milestone/prompt que originou a reflexão (opcional).
            theme_tags: Tags de temas identificados na reflexão (opcional).
            linked_thread_ids: IDs das threads narrativas relacionadas (opcional).
            is_milestone_completed: Indica se o milestone foi marcado como concluído.

        Returns:
            SessionAnnotation criada e salva.

        Raises:
            SessionNotFoundError: Se a sessão não existir.
            HistoryDBError: Se houver erro ao salvar.
        """
        # Verificar se a sessão existe
        session = self.get_session(session_id)
        if session is None:
            logger.warning("Tentativa de anotar sessão inexistente: %s", session_id)
            raise SessionNotFoundError(session_id)

        # Carregar todas as anotações existentes
        all_annotations = self.load_annotations()

        # Criar nova anotação
        from .types import SessionAnnotation

        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        annotation_id = f"ann-{session_id}-{len(all_annotations) + 1}-{timestamp}"

        new_annotation = SessionAnnotation(
            annotation_id=annotation_id,
            session_id=session_id,
            milestone_id=milestone_id or "",
            content=content,
            timestamp=timestamp,
            theme_tags=theme_tags or [],
            linked_thread_ids=linked_thread_ids or [],
            is_milestone_completed=is_milestone_completed,
        )

        # Adicionar à lista e salvar
        all_annotations.append(new_annotation)
        self.save_annotations(all_annotations)

        logger.info("Anotação adicionada à sessão %s: %s", session_id, annotation_id)
        return new_annotation

    # ----------------------------------------------------------------------
    # Utilitários
    # ----------------------------------------------------------------------

    def get_session_count(self) -> int:
        """Retorna o número de sessões armazenadas.

        Returns:
            Número de sessões no banco de dados.
        """
        index = self._load_index()
        return len(index)

    def clear_all(self) -> None:
        """Remove todos os dados do banco de histórico.

        ATENÇÃO: Esta ação é irreversível.
        """
        try:
            # Remover todos os arquivos JSON
            for json_file in self.data_dir.glob("*.json"):
                json_file.unlink()

            logger.warning("Banco de histórico limpo: %s", self.data_dir)

        except Exception as e:
            logger.error("Erro ao limpar banco de histórico: %s", e)
            raise HistoryDBError(f"Falha ao limpar banco: {e}") from e