"""Módulo de agrupamento de sessões por similaridade temática.

Agrupa sessões relacionadas com base em sobreposição de keywords
e similaridade de cartas para tiragens, permitindo encontrar
sessões passadas relevantes.

Recebe uma sessão atual e uma lista de sessões armazenadas,
retornando as N sessões mais similares ordenadas por score.
"""

import logging
from typing import Optional

from src.session_storage import SessionStorage
from src.symbols import get_symbol_by_name
from src.types import Session

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constantes de scoring
# ----------------------------------------------------------------------

# Peso para match exato de tag
TAG_MATCH_WEIGHT = 2.0

# Peso para match de keyword
KEYWORD_MATCH_WEIGHT = 1.0

# Peso para match de carta (spread)
CARD_MATCH_WEIGHT = 1.5

# Score mínimo para considerar uma sessão como relacionada
MIN_RELEVANCE_SCORE = 0.1

# Número padrão de sessões relacionadas a retornar
DEFAULT_TOP_N = 5


# ----------------------------------------------------------------------
# Extração de características
# ----------------------------------------------------------------------


def _extract_keywords_from_session(session: Session) -> set[str]:
    """Extrai keywords de uma sessão para comparação.

    Args:
        session: Sessão a extrair keywords.

    Returns:
        Conjunto de keywords normalizadas (lowercase).
    """
    keywords: set[str] = set()

    # Adicionar tags como keywords
    if session.tags:
        keywords.update(tag.lower().strip() for tag in session.tags)

    # Adicionar conteúdo bruto tokenizado
    if session.raw_content:
        tokens = session.raw_content.lower().split()
        # Filtrar palavras muito curtas
        keywords.update(t for t in tokens if len(t) >= 3)

    logger.debug("Keywords extraídas de %s: %d", session.session_id, len(keywords))
    return keywords


def _extract_cards_from_session(session: Session) -> set[str]:
    """Extrai nomes de cartas de uma sessão spread.

    Args:
        session: Sessão a extrair cartas.

    Returns:
        Conjunto de nomes de cartas normalizados.
    """
    if not session.analysis_result or not session.analysis_result.symbolic_mappings:
        return set()

    cards: set[str] = set()
    mappings = session.analysis_result.symbolic_mappings

    for key, symbol_name in mappings.items():
        if key.startswith("card:"):
            cards.add(symbol_name.lower().strip())

    logger.debug("Cartas extraídas de %s: %s", session.session_id, cards)
    return cards


def _extract_themes_from_session(session: Session) -> set[str]:
    """Extrai temas de uma sessão.

    Args:
        session: Sessão a extrair temas.

    Returns:
        Conjunto de temas normalizados.
    """
    if not session.analysis_result or not session.analysis_result.themes:
        return set()

    themes: set[str] = set(t.lower().strip() for t in session.analysis_result.themes)
    logger.debug("Temas extraídos de %s: %s", session.session_id, themes)
    return themes


# ----------------------------------------------------------------------
# Funções de scoring
# ----------------------------------------------------------------------


def _compute_keyword_overlap(
    current_keywords: set[str],
    past_keywords: set[str],
) -> float:
    """Calcula score de sobreposição de keywords.

    Args:
        current_keywords: Keywords da sessão atual.
        past_keywords: Keywords da sessão passada.

    Returns:
        Score de similaridade (0.0 a 1.0).
    """
    if not current_keywords or not past_keywords:
        return 0.0

    intersection = current_keywords & past_keywords
    union = current_keywords | past_keywords

    if not union:
        return 0.0

    # Jaccard similarity
    jaccard = len(intersection) / len(union)

    # Bônus por quantidade de matches
    match_bonus = min(len(intersection) * 0.1, 0.3)

    score = jaccard + match_bonus
    logger.debug(
        "Keyword overlap: current=%d, past=%d, intersection=%d, score=%.3f",
        len(current_keywords),
        len(past_keywords),
        len(intersection),
        score,
    )
    return score


def _compute_tag_match(
    current_tags: list[str],
    past_tags: list[str],
) -> float:
    """Calcula score de match de tags.

    Args:
        current_tags: Tags da sessão atual.
        past_tags: Tags da sessão passada.

    Returns:
        Score de match (0.0 a 1.0).
    """
    if not current_tags or not past_tags:
        return 0.0

    current_set = {t.lower().strip() for t in current_tags}
    past_set = {t.lower().strip() for t in past_tags}

    intersection = current_set & past_set

    if not intersection:
        return 0.0

    # Score proporcional ao número de matches
    score = len(intersection) / max(len(current_set), len(past_set))

    logger.debug(
        "Tag match: current=%s, past=%s, intersection=%s, score=%.3f",
        current_set,
        past_set,
        intersection,
        score,
    )
    return score


def _compute_card_similarity(
    current_cards: set[str],
    past_cards: set[str],
) -> float:
    """Calcula score de similaridade de cartas para tiragens.

    Args:
        current_cards: Cartas da sessão atual.
        past_cards: Cartas da sessão passada.

    Returns:
        Score de similaridade (0.0 a 1.0).
    """
    if not current_cards or not past_cards:
        return 0.0

    intersection = current_cards & past_cards
    union = current_cards | past_cards

    if not union:
        return 0.0

    # Similaridade Jaccard com peso para matches
    jaccard = len(intersection) / len(union)

    # Bônus por cartas compartilhadas (mais significativo)
    if intersection:
        # Verificar também similaridade temática via símbolos
        theme_bonus = _compute_symbol_theme_bonus(intersection)
        return jaccard + theme_bonus

    return jaccard


def _compute_symbol_theme_bonus(card_intersection: set[str]) -> float:
    """Calcula bônus de similaridade temática entre cartas.

    Args:
        card_intersection: Conjunto de cartas em interseção.

    Returns:
        Bônus de 0.0 a 0.3.
    """
    if len(card_intersection) < 2:
        return 0.0

    # Agrupar cartas por tema
    theme_groups: dict[str, list[str]] = {}
    for card in card_intersection:
        symbol = get_symbol_by_name(card)
        if symbol and symbol.theme:
            theme = symbol.theme.lower()
            if theme not in theme_groups:
                theme_groups[theme] = []
            theme_groups[theme].append(card)

    # Calcular bônus baseado em grupos temáticos
    bonus = 0.0
    for theme, cards in theme_groups.items():
        if len(cards) >= 2:
            # Bônus por ter 2+ cartas do mesmo tema
            bonus += 0.1

    return min(bonus, 0.3)


def _compute_theme_similarity(
    current_themes: set[str],
    past_themes: set[str],
) -> float:
    """Calcula score de similaridade de temas.

    Args:
        current_themes: Temas da sessão atual.
        past_themes: Temas da sessão passada.

    Returns:
        Score de similaridade (0.0 a 1.0).
    """
    if not current_themes or not past_themes:
        return 0.0

    intersection = current_themes & past_themes

    if not intersection:
        return 0.0

    score = len(intersection) / max(len(current_themes), len(past_themes))
    logger.debug(
        "Theme similarity: current=%s, past=%s, score=%.3f",
        current_themes,
        past_themes,
        score,
    )
    return score


def _compute_combined_score(
    current_session: Session,
    past_session: Session,
) -> float:
    """Calcula score combinado de similaridade entre sessões.

    Args:
        current_session: Sessão atual.
        past_session: Sessão passada para comparar.

    Returns:
        Score de similaridade ponderado.
    """
    # Extrair características
    current_keywords = _extract_keywords_from_session(current_session)
    past_keywords = _extract_keywords_from_session(past_session)

    current_tags = current_session.tags or []
    past_tags = past_session.tags or []

    current_cards = _extract_cards_from_session(current_session)
    past_cards = _extract_cards_from_session(past_session)

    current_themes = _extract_themes_from_session(current_session)
    past_themes = _extract_themes_from_session(past_session)

    # Calcular componentes
    keyword_score = _compute_keyword_overlap(current_keywords, past_keywords)
    tag_score = _compute_tag_match(current_tags, past_tags)
    card_score = _compute_card_similarity(current_cards, past_cards)
    theme_score = _compute_theme_similarity(current_themes, past_themes)

    # Score ponderado combinado
    # Tags têm peso maior (identificação explícita do tema)
    # Cartas têm peso intermediário (similaridade estrutural)
    # Keywords e themes têm peso base
    combined = (
        (tag_score * TAG_MATCH_WEIGHT)
        + (keyword_score * KEYWORD_MATCH_WEIGHT)
        + (card_score * CARD_MATCH_WEIGHT)
        + (theme_score * KEYWORD_MATCH_WEIGHT * 0.5)
    )

    # Normalizar para 0-1
    max_possible = TAG_MATCH_WEIGHT + KEYWORD_MATCH_WEIGHT + CARD_MATCH_WEIGHT + (KEYWORD_MATCH_WEIGHT * 0.5)
    normalized = combined / max_possible

    logger.debug(
        "Combined score for %s: keyword=%.3f, tag=%.3f, card=%.3f, theme=%.3f → total=%.3f",
        past_session.session_id,
        keyword_score,
        tag_score,
        card_score,
        theme_score,
        normalized,
    )

    return normalized


# ----------------------------------------------------------------------
# SessionClusterer
# ----------------------------------------------------------------------


class RelatedSession:
    """Representa uma sessão relacionada com score de similaridade.

    Attributes:
        session: Instância da sessão relacionada.
        score: Score de similaridade (0.0 a 1.0).
        match_reasons: Lista de razões do match (ex: 'tag:carreira').
    """

    def __init__(
        self,
        session: Session,
        score: float,
        match_reasons: Optional[list[str]] = None,
    ) -> None:
        self.session = session
        self.score = score
        self.match_reasons = match_reasons or []


class SessionClusterer:
    """Agrupador de sessões por similaridade temática.

    encontra sessões passadas relacionadas à sessão atual
    com base em sobreposição de keywords, tags, cartas e temas.

    Attributes:
        storage: Instância de SessionStorage para carregar sessões.
        top_n: Número máximo de sessões relacionadas a retornar.

    Example:
        >>> storage = SessionStorage("./data/sessions")
        >>> clusterer = SessionClusterer(storage)
        >>> related = clusterer.find_related_sessions(current_session, all_sessions)
        >>> for r in related:
        ...     print(f"{r.session.timestamp}: {r.score:.2f}")
    """

    def __init__(
        self,
        storage: Optional[SessionStorage] = None,
        top_n: int = DEFAULT_TOP_N,
    ) -> None:
        """Inicializa o clusterer de sessões.

        Args:
            storage: Instância de SessionStorage (opcional).
            top_n: Número máximo de sessões a retornar.
        """
        self.storage = storage
        self.top_n = top_n
        logger.debug("SessionClusterer inicializado, top_n=%d", top_n)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def find_related_sessions(
        self,
        current_session: Session,
        all_sessions: list[Session],
        min_score: float = MIN_RELEVANCE_SCORE,
    ) -> list[RelatedSession]:
        """Encontra sessões passadas relacionadas à sessão atual.

        Args:
            current_session: Sessão atual para comparar.
            all_sessions: Lista de sessões armazenadas.
            min_score: Score mínimo para incluir no resultado.

        Returns:
            Lista de RelatedSession ordenadas por score (maior primeiro).
        """
        logger.info(
            "Buscando sessões relacionadas para %s (total: %d sessões)",
            current_session.session_id,
            len(all_sessions),
        )

        # Filtrar sessão atual da lista
        candidates = [
            s for s in all_sessions
            if s.session_id != current_session.session_id
        ]

        if not candidates:
            logger.debug("Nenhuma sessão候选ária disponível")
            return []

        # Calcular scores
        scored_sessions: list[tuple[Session, float, list[str]]] = []

        for past_session in candidates:
            score = _compute_combined_score(current_session, past_session)
            reasons = self._get_match_reasons(current_session, past_session)

            if score >= min_score:
                scored_sessions.append((past_session, score, reasons))
                logger.debug(
                    "Sessão %s relacionada: score=%.3f, reasons=%s",
                    past_session.session_id,
                    score,
                    reasons,
                )

        # Ordenar por score descendente
        scored_sessions.sort(key=lambda x: x[1], reverse=True)

        # Limitar ao top_n
        top_sessions = scored_sessions[: self.top_n]

        # Converter para RelatedSession
        results = [
            RelatedSession(session=s, score=score, match_reasons=reasons)
            for s, score, reasons in top_sessions
        ]

        logger.info(
            "Encontradas %d sessões relacionadas (de %d candidatas)",
            len(results),
            len(candidates),
        )

        return results

    def find_related_sessions_by_content(
        self,
        raw_content: str,
        tags: Optional[list[str]] = None,
        all_sessions: Optional[list[Session]] = None,
        min_score: float = MIN_RELEVANCE_SCORE,
    ) -> list[RelatedSession]:
        """Encontra sessões relacionadas via conteúdo (sem análise completa).

        Args:
            raw_content: Conteúdo de texto para busca.
            tags: Tags opcionais para refinar busca.
            all_sessions: Lista de sessões (se None, usa storage).
            min_score: Score mínimo para incluir no resultado.

        Returns:
            Lista de RelatedSession ordenadas por score.
        """
        logger.debug("Buscando por conteúdo: %r, tags=%s", raw_content[:50], tags)

        # Criar sessão temporária para comparação
        temp_session = Session(
            session_id="__temp__",
            timestamp="",
            input_format="text",
            raw_content=raw_content,
            tags=tags or [],
        )

        # Carregar sessões se não fornecidas
        if all_sessions is None:
            if self.storage is None:
                logger.warning("Sem storage configurado, retornando lista vazia")
                return []
            all_sessions = self.storage.list_sessions()

        return self.find_related_sessions(temp_session, all_sessions, min_score)

    def cluster_by_tag(
        self,
        sessions: list[Session],
        tag: str,
    ) -> list[Session]:
        """Filtra sessões que contêm uma tag específica.

        Args:
            sessions: Lista de sessões a filtrar.
            tag: Tag para filtrar (case-insensitive).

        Returns:
            Lista de sessões com a tag especificada.
        """
        normalized_tag = tag.lower().strip()

        filtered = [
            s for s in sessions
            if any(t.lower().strip() == normalized_tag for t in s.tags)
        ]

        logger.debug(
            "Cluster por tag '%s': %d/%d sessões",
            tag,
            len(filtered),
            len(sessions),
        )

        return filtered

    def get_tag_suggestions(
        self,
        session: Session,
        available_tags: Optional[list[str]] = None,
    ) -> list[tuple[str, float]]:
        """Sugere tags baseadas no conteúdo da sessão.

        Args:
            session: Sessão para sugerir tags.
            available_tags: Lista de tags disponíveis no sistema.

        Returns:
            Lista de tuplas (tag, score) ordenadas por relevância.
        """
        suggestions: list[tuple[str, float]] = []

        # Keywords da sessão
        session_keywords = _extract_keywords_from_session(session)

        if not available_tags:
            # Usar tags mais comuns das sessões existentes
            available_tags = self._get_common_tags()

        for tag in available_tags:
            tag_lower = tag.lower().strip()
            # Verificar se a tag já existe
            if any(t.lower().strip() == tag_lower for t in session.tags):
                continue

            # Calcular similaridade
            tag_keywords = {tag_lower}
            score = _compute_keyword_overlap(session_keywords, tag_keywords)

            if score > 0:
                suggestions.append((tag, score))

        # Ordenar por score
        suggestions.sort(key=lambda x: x[1], reverse=True)

        logger.debug("Sugestões de tags para %s: %s", session.session_id, suggestions[:5])
        return suggestions[: 5]  # Top 5

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------

    def _get_match_reasons(
        self,
        current_session: Session,
        past_session: Session,
    ) -> list[str]:
        """Identifica as razões do match entre sessões.

        Args:
            current_session: Sessão atual.
            past_session: Sessão passada.

        Returns:
            Lista de razões do match (ex: 'tag:carreira').
        """
        reasons: list[str] = []

        current_tags = {t.lower().strip() for t in (current_session.tags or [])}
        past_tags = {t.lower().strip() for t in (past_session.tags or [])}

        # Tag matches
        tag_intersection = current_tags & past_tags
        for tag in tag_intersection:
            reasons.append(f"tag:{tag}")

        # Keyword matches (top 3)
        current_kw = _extract_keywords_from_session(current_session)
        past_kw = _extract_keywords_from_session(past_session)
        kw_intersection = current_kw & past_kw

        for kw in list(kw_intersection)[:3]:
            reasons.append(f"keyword:{kw}")

        # Theme matches
        current_themes = _extract_themes_from_session(current_session)
        past_themes = _extract_themes_from_session(past_session)
        theme_intersection = current_themes & past_themes

        for theme in theme_intersection:
            reasons.append(f"theme:{theme}")

        return reasons

    def _get_common_tags(self, limit: int = 20) -> list[str]:
        """Retorna as tags mais comuns no sistema.

        Args:
            limit: Número máximo de tags a retornar.

        Returns:
            Lista de tags ordenadas por frequência.
        """
        if self.storage is None:
            return []

        from collections import Counter

        sessions = self.storage.list_sessions()
        all_tags: list[str] = []

        for session in sessions:
            if session.tags:
                all_tags.extend(t.lower().strip() for t in session.tags)

        if not all_tags:
            return []

        tag_counts = Counter(all_tags)
        common_tags = [tag for tag, _ in tag_counts.most_common(limit)]

        logger.debug("Tags mais comuns: %s", common_tags[:10])
        return common_tags
