"""Gerador de arcos narrativos — Sistema de Clareza.

Módulo que analisa múltiplas sessões e gera uma visualização narrativa
do arco temporal:
- build_arc: constrói um Arco a partir de sessões ordenadas
- identify_threads: identifica threads narrativas que atravessam sessões
- generate_timeline: gera visualização ASCII da linha do tempo
- generate_recurring_symbols: lista símbolos recorrentes entre sessões
- generate_narrative_summary: gera sumário narrativo conectando sessões
- generate: função principal que gera a visualização completa

Recebe lista de Session (types.py) e retorna visualização em Markdown.
"""

import logging
from collections import Counter
from datetime import datetime
from typing import Optional

from src.types import (
    Arc,
    ChapterSummary,
    NarrativeThread,
    Session,
    SessionContext,
)

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Templates de visualização
# ----------------------------------------------------------------------

ARC_TEMPLATE = """# Arco Narrativo — {arc_name}

{summary_section}

{timeline_section}

{recurring_symbols_section}

{threads_section}

{resolution_section}

---
*Arco gerado por Sistema de Clareza Simbólico-Estratégica v0.0.1 — ferramenta de reflexão, não previsão determinista.*
"""

TIMELINE_TEMPLATE = """## Linha do Tempo

{entries}

**Período**: {start_date} → {end_date}
**Total de sessões**: {session_count}
"""

TIMELINE_ENTRY_TEMPLATE = """
### {session_label}

- **Data**: {timestamp}
- **Formato**: {input_format}
- **Diagnóstico**: {diagnosis}
{unresolved_note}
"""

RECURRING_SYMBOLS_TEMPLATE = """## Símbolos Recorrentes

{intro}

{symbols_list}

{insight}
"""

THREADS_TEMPLATE = """## Temas Persistentes

{intro}

{threads_list}
"""

THREAD_TEMPLATE = """### {thread_name}

- **Tema**: {theme}
- **Status**: {status}
- **Sessões**: {session_count}
- **Primeira menção**: {first_mention}
- **Última menção**: {last_mention}

**Progressão**: {progression}
"""

RESOLUTION_TEMPLATE = """## Síntese e Reflexão

{summary}

{unresolved_section}

{insight}
"""

# ----------------------------------------------------------------------
# Threshold para considerar símbolo recorrente
# ----------------------------------------------------------------------

_RECURRING_THRESHOLD = 2

# ----------------------------------------------------------------------
# Status labels
# ----------------------------------------------------------------------

_STATUS_LABELS: dict[str, str] = {
    "active": "Em evolução",
    "resolved": "Resolvido",
    "escalated": "Escalado",
}


# ----------------------------------------------------------------------
# Gerador de arcos
# ----------------------------------------------------------------------


class ArcGenerator:
    """Gerador de arcos narrativos a partir de sessões.

    Transforma múltiplas sessões em uma visualização narrativa que
    mostra a evolução temporal, símbolos recorrentes e threads temáticas.

    Attributes:
        session_context: Contexto de sessão opcional para evitar repetições.
    """

    def __init__(self, session_context: Optional[SessionContext] = None) -> None:
        self.session_context = session_context
        logger.debug("ArcGenerator inicializado, context=%s", session_context is not None)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generate(
        self,
        sessions: list[Session],
        arc_name: Optional[str] = None,
        include_timeline: bool = True,
        include_recurring_symbols: bool = True,
        include_threads: bool = True,
        include_summary: bool = True,
    ) -> str:
        """Gera visualização do arco narrativo em Markdown.

        Args:
            sessions: Lista de sessões ordenadas por timestamp.
            arc_name: Nome do arco (opcional, gerado automaticamente se None).
            include_timeline: Se True, inclui seção de linha do tempo.
            include_recurring_symbols: Se True, inclui seção de símbolos recorrentes.
            include_threads: Se True, inclui seção de threads narrativas.
            include_summary: Se True, inclui seção de síntese.

        Returns:
            String com visualização do arco em Markdown.
        """
        if not sessions:
            logger.warning("Nenhuma sessão fornecida para gerar arco")
            return self._empty_arc_message()

        logger.info(
            "Gerando arco narrativo para %d sessões",
            len(sessions),
        )

        # Construir arco
        arc = self.build_arc(sessions, arc_name)

        # Montar seções
        sections: list[str] = []

        if include_summary:
            summary = self.generate_narrative_summary(arc)
            sections.append(summary)

        if include_timeline:
            timeline = self.generate_timeline(arc)
            sections.append(timeline)

        if include_recurring_symbols:
            recurring = self.generate_recurring_symbols(arc)
            sections.append(recurring)

        if include_threads:
            threads = self.generate_threads(arc)
            sections.append(threads)

        # Síntese final
        synthesis = self._generate_synthesis(arc)
        sections.append(synthesis)

        logger.info("Arco gerado com %d seções", len(sections))
        return "\n\n".join(sections)

    def build_arc(
        self,
        sessions: list[Session],
        arc_name: Optional[str] = None,
    ) -> Arc:
        """Constrói um Arco a partir de sessões ordenadas.

        Args:
            sessions: Lista de sessões ordenadas por timestamp.
            arc_name: Nome do arco (opcional).

        Returns:
            Arc com sessões, threads identificadas e metadados.
        """
        if not sessions:
            raise ValueError("Lista de sessões vazia")

        # Gerar nome do arco se não fornecido
        if arc_name is None:
            arc_name = self._generate_arc_name(sessions)

        # Identificar threads
        threads = self.identify_threads(sessions)

        # Identificar datas
        start_date = self._extract_date(sessions[0].timestamp)
        end_date = self._extract_date(sessions[-1].timestamp)

        # Identificar temas dominantes
        dominant_themes = self._extract_dominant_themes(sessions)

        # Identificar unresolved threads
        unresolved_threads = [t for t in threads if t.status == "active"]

        arc = Arc(
            arc_id=self._generate_arc_id(sessions),
            name=arc_name,
            sessions=sessions,
            threads=threads,
            start_date=start_date,
            end_date=end_date,
            dominant_themes=dominant_themes,
        )

        logger.info(
            "Arco construído: id=%s, name=%s, sessions=%d, threads=%d",
            arc.arc_id,
            arc.name,
            len(sessions),
            len(threads),
        )

        return arc

    def identify_threads(self, sessions: list[Session]) -> list[NarrativeThread]:
        """Identifica threads narrativas que atravessam múltiplas sessões.

        Args:
            sessions: Lista de sessões ordenadas.

        Returns:
            Lista de NarrativeThread identificadas.
        """
        if not sessions:
            return []

        # Agrupar sessões por tema
        theme_sessions: dict[str, list[tuple[Session, str]]] = {}

        for session in sessions:
            if session.analysis_result and session.analysis_result.themes:
                for theme in session.analysis_result.themes:
                    if theme not in theme_sessions:
                        theme_sessions[theme] = []
                    theme_sessions[theme].append((session, session.timestamp))

        threads: list[NarrativeThread] = []

        for theme, session_list in theme_sessions.items():
            if len(session_list) >= _RECURRING_THRESHOLD:
                thread_id = f"thread_{theme.replace(' ', '_')}"
                session_ids = [s.session_id for s, _ in session_list]
                first_ts = session_list[0][1]
                last_ts = session_list[-1][1]

                # Determinar status baseado nas sessões
                status = self._determine_thread_status(session_list, session_ids)

                # Gerar progressão
                progression = self._generate_progression(theme, session_list)

                thread = NarrativeThread(
                    thread_id=thread_id,
                    name=theme.title(),
                    theme=theme,
                    session_ids=session_ids,
                    status=status,
                    first_mention=first_ts,
                    last_mention=last_ts,
                    progression=progression,
                )
                threads.append(thread)

        logger.debug("Threads identificadas: %d", len(threads))
        return threads

    def generate_timeline(self, arc: Arc) -> str:
        """Gera visualização ASCII da linha do tempo.

        Args:
            arc: Arco com sessões.

        Returns:
            String com linha do tempo formatada em Markdown.
        """
        if not arc.sessions:
            return "*Linha do tempo não disponível.*"

        entries: list[str] = []

        for i, session in enumerate(arc.sessions, start=1):
            label = f"Sessão {i}"

            diagnosis = ""
            if session.analysis_result:
                diagnosis = session.analysis_result.diagnosis or "Sem diagnóstico"

            unresolved_note = ""
            if session.unresolved_threads:
                threads_count = len(session.unresolved_threads)
                unresolved_note = f"- *{threads_count} thread(s) não resolvida(s)*"

            entry = TIMELINE_ENTRY_TEMPLATE.format(
                session_label=label,
                timestamp=self._format_timestamp(session.timestamp),
                input_format=session.input_format,
                diagnosis=diagnosis[:100] + ("..." if len(diagnosis) > 100 else ""),
                unresolved_note=unresolved_note,
            )
            entries.append(entry)

        timeline_content = TIMELINE_TEMPLATE.format(
            entries="\n".join(entries),
            start_date=arc.start_date or "—",
            end_date=arc.end_date or "—",
            session_count=len(arc.sessions),
        )

        return timeline_content

    def generate_recurring_symbols(self, arc: Arc) -> str:
        """Gera lista de símbolos recorrentes entre sessões.

        Args:
            arc: Arco com sessões analisadas.

        Returns:
            String com seção de símbolos recorrentes.
        """
        if not arc.sessions:
            return "*Símbolos recorrentes não disponíveis.*"

        # Coletar todos os símbolos das sessões
        all_symbols: list[str] = []
        session_symbols: dict[int, list[str]] = {}

        for i, session in enumerate(arc.sessions):
            if session.analysis_result and session.analysis_result.symbolic_mappings:
                session_symbols[i] = []
                for kw, symbol_name in session.analysis_result.symbolic_mappings.items():
                    all_symbols.append(symbol_name)
                    session_symbols[i].append(symbol_name)

        if not all_symbols:
            return "*Nenhum símbolo detectado nas sessões.*"

        # Contar frequência
        symbol_counts = Counter(all_symbols)

        # Filtrar recorrentes
        recurring = [(s, c) for s, c in symbol_counts.items() if c >= _RECURRING_THRESHOLD]

        if not recurring:
            return "*Nenhum símbolo recorrente detectado (mínimo 2 ocorrências).*"

        # Ordenar por frequência
        recurring.sort(key=lambda x: x[1], reverse=True)

        symbols_list = "\n".join(
            f"- **{symbol}** (apareceu em {count} sessões)"
            for symbol, count in recurring
        )

        # Gerar insight
        top_symbol = recurring[0][0]
        top_count = recurring[0][1]
        insight = (
            f"O símbolo **{top_symbol}** é o mais recorrente, "
            f"aparecendo em {top_count} sessões. "
            f"Isso sugere uma energia constante relacionada a este tema na sua jornada."
        )

        return RECURRING_SYMBOLS_TEMPLATE.format(
            intro=f"Foram identificados **{len(recurring)}** símbolos recorrentes nas sessões analisadas:",
            symbols_list=symbols_list,
            insight=insight,
        )

    def generate_threads(self, arc: Arc) -> str:
        """Gera seção de threads narrativas persistentes.

        Args:
            arc: Arco com threads identificadas.

        Returns:
            String com seção de threads.
        """
        if not arc.threads:
            return "*Nenhuma thread narrativa persistente identificada.*"

        threads_list: list[str] = []

        for thread in arc.threads:
            status_label = _STATUS_LABELS.get(thread.status, thread.status)
            progression_text = "; ".join(thread.progression[-3:]) if thread.progression else "Sem progressão registrada"

            thread_content = THREAD_TEMPLATE.format(
                thread_name=thread.name,
                theme=thread.theme,
                status=status_label,
                session_count=len(thread.session_ids),
                first_mention=self._format_timestamp(thread.first_mention) if thread.first_mention else "—",
                last_mention=self._format_timestamp(thread.last_mention) if thread.last_mention else "—",
                progression=progression_text,
            )
            threads_list.append(thread_content)

        return THREADS_TEMPLATE.format(
            intro=f"Foram identificadas **{len(arc.threads)}** threads narrativas que atravessam múltiplas sessões:",
            threads_list="\n".join(threads_list),
        )

    # ------------------------------------------------------------------
    # Geração de sumário narrativo
    # ------------------------------------------------------------------

    def generate_narrative_summary(self, arc: Arc) -> str:
        """Gera sumário narrativo conectando as sessões.

        Args:
            arc: Arco com sessões.

        Returns:
            String com seção de sumário narrativo.
        """
        if not arc.sessions:
            return "*Sumário não disponível.*"

        session_count = len(arc.sessions)
        date_range = f"{arc.start_date or '—'} a {arc.end_date or '—'}"

        # Coletar temas únicos
        all_themes: set[str] = set()
        for session in arc.sessions:
            if session.analysis_result and session.analysis_result.themes:
                all_themes.update(session.analysis_result.themes)

        themes_text = ", ".join(sorted(all_themes)) if all_themes else "diversos"

        # Verificar threads
        thread_count = len(arc.threads)
        unresolved_count = sum(1 for t in arc.threads if t.status == "active")

        # Gerar narrativa
        narrative_parts: list[str] = []

        if session_count == 1:
            narrative_parts.append(
                f"Esta análise representa um momento único de reflexão "
                f"sobre {themes_text}."
            )
        else:
            narrative_parts.append(
                f"Ao longo do período de {date_range}, foram realizadas "
                f"{session_count} sessões de reflexão."
            )
            narrative_parts.append(
                f"Os temas explorados incluem: {themes_text}."
            )

            if thread_count > 0:
                if unresolved_count > 0:
                    narrative_parts.append(
                        f"Foi identificada {thread_count} thread(s) narrativa(s), "
                        f"das quais {unresolved_count} permanece(m) em evolução."
                    )
                else:
                    narrative_parts.append(
                        f"Foram identificadas {thread_count} thread(s) narrativa(s), "
                        f"todas encontrando-se em estado de resolução."
                    )

        summary_text = " ".join(narrative_parts)

        # Adicionar insight baseado nos temas dominantes
        if arc.dominant_themes:
            dominant = arc.dominant_themes[0]
            summary_text += (
                f" O tema predominante parece ser **{dominant}**, "
                f"que merece atenção especial na sua jornada."
            )

        return f"## Síntese Narrativa\n\n{summary_text}"

    # ------------------------------------------------------------------
    # Utilitários internos
    # ------------------------------------------------------------------

    def _empty_arc_message(self) -> str:
        """Retorna mensagem para arco vazio."""
        return (
            "# Arco Narrativo\n\n"
            "*Nenhuma sessão encontrada para o período solicitado. "
            "Continue suas reflexões para construir um arco narrativo ao longo do tempo.*\n\n"
            "---\n"
            "*Arco gerado por Sistema de Clareza Simbólico-Estratégica v0.0.1.*"
        )

    def _generate_arc_id(self, sessions: list[Session]) -> str:
        """Gera ID único para o arco baseado nas sessões."""
        if not sessions:
            return "arc_empty"
        first_id = sessions[0].session_id[:8]
        last_id = sessions[-1].session_id[:8]
        return f"arc_{first_id}_{last_id}"

    def _generate_arc_name(self, sessions: list[Session]) -> str:
        """Gera nome descritivo para o arco."""
        if not sessions:
            return "Arco Vazio"

        start = self._extract_date(sessions[0].timestamp)
        end = self._extract_date(sessions[-1].timestamp)

        if start == end:
            return f"Jornada de {start}"
        return f"Jornada de {start} a {end}"

    def _extract_date(self, timestamp: str) -> str:
        """Extrai data formatada do timestamp."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y")
        except (ValueError, AttributeError):
            return timestamp[:10] if timestamp else "—"

    def _format_timestamp(self, timestamp: Optional[str]) -> str:
        """Formata timestamp para exibição."""
        if not timestamp:
            return "—"
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y às %H:%M")
        except (ValueError, AttributeError):
            return timestamp

    def _extract_dominant_themes(self, sessions: list[Session]) -> list[str]:
        """Extrai temas dominantes das sessões."""
        theme_counts: Counter[str] = Counter()

        for session in sessions:
            if session.analysis_result and session.analysis_result.themes:
                theme_counts.update(session.analysis_result.themes)

        if not theme_counts:
            return []

        return [theme for theme, _ in theme_counts.most_common(3)]

    def _determine_thread_status(
        self,
        session_list: list[tuple[Session, str]],
        session_ids: list[str],
    ) -> str:
        """Determina o status de uma thread baseado nas sessões."""
        # Verificar se a última sessão tem a thread como unresolved
        if session_list:
            last_session = session_list[-1][0]
            for thread_id in last_session.unresolved_threads:
                if thread_id in session_ids:
                    return "active"

        return "active"

    def _generate_progression(
        self,
        theme: str,
        session_list: list[tuple[Session, str]],
    ) -> list[str]:
        """Gera lista de progressão para uma thread."""
        progression: list[str] = []

        for i, (session, _) in enumerate(session_list, start=1):
            if session.analysis_result:
                diagnosis = session.analysis_result.diagnosis
                if diagnosis:
                    short = diagnosis[:50] + ("..." if len(diagnosis) > 50 else "")
                    progression.append(f"Sessão {i}: {short}")

        return progression

    def _generate_synthesis(self, arc: Arc) -> str:
        """Gera seção de síntese e reflexão final."""
        parts: list[str] = []

        # Unresolved threads
        active_threads = [t for t in arc.threads if t.status == "active"]
        if active_threads:
            unresolved_section = (
                "**Threads em evolução**: "
                + ", ".join(t.name for t in active_threads)
                + ". Estas questões continuam pendentes e merecem atenção contínua."
            )
        else:
            unresolved_section = "Não foram identificadas threads em evolução ativa."

        # Insight geral
        if arc.dominant_themes:
            dominant = arc.dominant_themes[0]
            insight = (
                f"Este arco sugere que a sua jornada atual está centrada em **{dominant}**. "
                f"Mantenha atenção a este tema enquanto continua suas reflexões."
            )
        else:
            insight = "Continue suas reflexões para desenvolver maior clareza sobre os seus temas centrais."

        return RESOLUTION_TEMPLATE.format(
            summary=self.generate_narrative_summary(arc) if arc.sessions else "",
            unresolved_section=unresolved_section,
            insight=insight,
        )
