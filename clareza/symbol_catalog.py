"""Catálogo simbólico estendido do Baralho Cigano.

Módulo que carrega e expõe o symbol_catalog.json — fornecendo
clusters arquetípicos, padrões nomeados entre cartas,
interações entre clusters e modificadores contextuais.

Tudo neste módulo é opcional: se o arquivo JSON estiver ausente,
funções retornam None/empty gracefully.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Singleton state
# ----------------------------------------------------------------------

_catalog: Optional[dict] = None


def _get_data_path() -> Path:
    """Retorna o caminho do symbol_catalog.json."""
    import clareza
    pkg = Path(clareza.__file__).parent
    return pkg / "data" / "symbol_catalog.json"


def _load_catalog() -> Optional[dict]:
    """Carrega symbol_catalog.json com fallback gracioso."""
    global _catalog
    if _catalog is not None:
        return _catalog

    path = _get_data_path()
    if not path.exists():
        logger.warning("symbol_catalog.json não encontrado em %s", path)
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            _catalog = json.load(f)
        logger.debug("symbol_catalog.json carregado com sucesso")
        return _catalog
    except json.JSONDecodeError as e:
        logger.error("symbol_catalog.json corrompido: %s", e)
        return None
    except Exception as e:
        logger.error("Erro ao carregar symbol_catalog.json: %s", e)
        return None


# ----------------------------------------------------------------------
# Cluster queries
# ----------------------------------------------------------------------

def get_cluster_for_card(card_id: int) -> Optional[dict]:
    """Retorna o cluster arquetípico de uma carta (se existir).

    Args:
        card_id: ID numérico da carta (1-36).

    Returns:
        Dicionário do cluster ou None se não encontrada.
    """
    catalog = _load_catalog()
    if not catalog:
        return None

    for cluster in catalog.get("card_clusters", []):
        if card_id in cluster.get("card_ids", []):
            return cluster
    return None


def get_all_clusters() -> list[dict]:
    """Retorna todos os clusters arquetípicos."""
    catalog = _load_catalog()
    if not catalog:
        return []
    return catalog.get("card_clusters", [])


# ----------------------------------------------------------------------
# Named cross-card patterns (pairs, sequences, oppositions)
# ----------------------------------------------------------------------

def _normalize_card_name(name: str) -> str:
    """Normaliza nome de carta para busca."""
    return name.strip().lower()


def _find_in_patterns(
    patterns: list[dict],
    card_names: list[str],
) -> Optional[dict]:
    """Busca um padrão que corresponda exatamente às cartas fornecidas."""
    normalized = [_normalize_card_name(n) for n in card_names]
    for pattern in patterns:
        pattern_cards = [_normalize_card_name(c) for c in pattern.get("cards", [])]
        if pattern_cards == normalized:
            return pattern
    return None


def detect_named_pair(cards: list[dict]) -> Optional[dict]:
    """Detecta se um par de cartas corresponde a um padrão nomeado.

    Args:
        cards: Lista de dicts com 'card_name' (ex: [{"card_name": "A Casa"}, ...])

    Returns:
        Dicionário do padrão ou None.
    """
    if len(cards) < 2:
        return None

    catalog = _load_catalog()
    if not catalog:
        return None

    all_pairs = catalog.get("cross_card_patterns", {}).get("pairs", [])
    for i in range(len(cards)):
        for j in range(i + 1, len(cards)):
            pair = _find_in_patterns(all_pairs, [cards[i]["card_name"], cards[j]["card_name"]])
            if pair:
                return pair
    return None


def detect_named_sequence(cards: list[dict]) -> Optional[dict]:
    """Detecta se 3+ cartas formam uma sequência nomeada.

    Args:
        cards: Lista de dicts com 'card_name', ordenada por posição.

    Returns:
        Dicionário da sequência ou None.
    """
    if len(cards) < 3:
        return None

    catalog = _load_catalog()
    if not catalog:
        return None

    sequences = catalog.get("cross_card_patterns", {}).get("sequences", [])
    card_names = [c["card_name"] for c in cards]
    normalized = [_normalize_card_name(n) for n in card_names]

    for seq in sequences:
        seq_cards = [_normalize_card_name(c) for c in seq.get("cards", [])]
        if len(seq_cards) <= len(normalized):
            # Check if the sequence appears as a subsequence
            for start in range(len(normalized) - len(seq_cards) + 1):
                if normalized[start:start + len(seq_cards)] == seq_cards:
                    return seq
    return None


def detect_opposition(cards: list[dict]) -> Optional[dict]:
    """Detecta se duas cartas formam uma oposição.

    Args:
        cards: Lista de dicts com 'card_name'.

    Returns:
        Dicionário da oposição ou None.
    """
    if len(cards) < 2:
        return None

    catalog = _load_catalog()
    if not catalog:
        return None

    oppositions = catalog.get("cross_card_patterns", {}).get("oppositions", [])
    for i in range(len(cards)):
        for j in range(i + 1, len(cards)):
            opp = _find_in_patterns(oppositions, [cards[i]["card_name"], cards[j]["card_name"]])
            if opp:
                return opp
    return None


def get_all_named_patterns() -> dict:
    """Retorna todos os padrões nomeados do catálogo."""
    catalog = _load_catalog()
    if not catalog:
        return {"pairs": [], "sequences": [], "oppositions": []}
    return catalog.get("cross_card_patterns", {})


# ----------------------------------------------------------------------
# Cluster interactions
# ----------------------------------------------------------------------

def get_cluster_interaction(cluster_id_a: str, cluster_id_b: str) -> Optional[dict]:
    """Retorna a interação entre dois clusters.

    Args:
        cluster_id_a: ID do primeiro cluster (e.g., "water").
        cluster_id_b: ID do segundo cluster.

    Returns:
        Dicionário com description e advice, ou None.
    """
    catalog = _load_catalog()
    if not catalog:
        return None

    interactions = catalog.get("cluster_interactions", {})
    key = f"{cluster_id_a}_{cluster_id_b}"
    alt_key = f"{cluster_id_b}_{cluster_id_a}"
    return interactions.get(key) or interactions.get(alt_key)


# ----------------------------------------------------------------------
# Position significance
# ----------------------------------------------------------------------

def get_position_significance(position: int) -> Optional[dict]:
    """Retorna o significado de uma posição na tiragem.

    Args:
        position: Número da posição (1-indexed).

    Returns:
        Dicionário com name, keywords, interpretation, advice, ou None.
    """
    catalog = _load_catalog()
    if not catalog:
        return None

    modifiers = catalog.get("contextual_modifiers", {})
    positions = modifiers.get("position_significance", {}).get("positions", [])
    for p in positions:
        if p.get("position") == position:
            return p
    return None


# ----------------------------------------------------------------------
# Adjacent card influence
# ----------------------------------------------------------------------

def get_adjacent_influence(
    left_card: Optional[dict],
    center_card: dict,
    right_card: Optional[dict],
) -> list[str]:
    """Retorna lista de influências contextuais baseadas em cartas vizinhas.

    Args:
        left_card: Carta à esquerda (ou None).
        center_card: Carta central.
        right_card: Carta à direita (ou None).

    Returns:
        Lista de descrições de influência aplicáveis.
    """
    influences: list[str] = []
    catalog = _load_catalog()
    if not catalog:
        return influences

    special = catalog.get("contextual_modifiers", {}).get("adjacent_card_influence", {}).get("special_combinations", [])
    card_names = [c["card_name"] for c in [left_card, center_card, right_card] if c]
    normalized = [_normalize_card_name(n) for n in card_names if n]

    for combo in special:
        combo_cards = [_normalize_card_name(c) for c in combo.get("cards", [])]
        # Check if all combo cards are present in the normalized list
        if all(c in normalized for c in combo_cards):
            influence_type = combo.get("influence", "")
            combined = combo.get("combined_interpretation", "")
            influences.append(f"[{influence_type}] {combined}")

    return influences
