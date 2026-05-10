"""Catálogo de símbolos do Baralho Cigano.

Módulo central que carrega o catálogo de 36 cartas do Baralho Cigano
a partir de cigano_deck.json usando o card_loader, com funções de consulta.

Baseado em data/cigano_deck.json — as definições aqui servem como
catálogo em memória para consulta rápida durante a análise.
"""

from dataclasses import dataclass
from typing import Optional

from src.card_loader import load_deck


@dataclass
class CiganoSymbol:
    """Representa um símbolo individual do Baralho Cigano.

    Attributes:
        id: Identificador numérico único da carta (1–36).
        name: Nome oficial da carta.
        name_pt: Nome em português (pode ser diferente do oficial).
        alternate_names: Nomes alternativos e variant spellings.
        keywords: Lista de palavras-chave que mapeiam para esta carta (themes).
        theme: Tema principal (based on most common theme in themes).
        interpretation: Interpretação base da carta.
        directions: Interpretações direcionais (upright/reversed).
        emotional_associations: Associações emocionais.
        contextual_notes: Notas contextuais sobre a carta.
    """

    id: int
    name: str
    name_pt: str
    alternate_names: list[str]
    themes: list[str]
    meaning: str
    directions: dict[str, str]
    emotional_associations: list[str]
    contextual_notes: str

    @property
    def keywords(self) -> list[str]:
        """Alias for themes for backward compatibility."""
        return self.themes

    @property
    def interpretation(self) -> str:
        """Alias for meaning for backward compatibility."""
        return self.meaning

    @property
    def theme(self) -> str:
        """Extract most common theme from themes list."""
        return self.themes[0] if self.themes else "espiritual"

    @property
    def advice(self) -> str:
        """Generate advice from contextual_notes."""
        return self.contextual_notes or ""


# ----------------------------------------------------------------------
# Catálogo carregado em memória
# ----------------------------------------------------------------------


def _load_catalog() -> list[CiganoSymbol]:
    """Load and convert deck data to CiganoSymbol objects."""
    deck = load_deck()
    return [
        CiganoSymbol(
            id=card["id"],
            name=card["name"],
            name_pt=card.get("name_pt", card["name"]),
            alternate_names=card.get("alternate_names", []),
            themes=card["themes"],
            meaning=card["meaning"],
            directions=card["directions"],
            emotional_associations=card.get("emotional_associations", []),
            contextual_notes=card.get("contextual_notes", ""),
        )
        for card in deck
    ]


_CIGANO_DECK: list[CiganoSymbol] = _load_catalog()

# ----------------------------------------------------------------------
# Índice rápido em memória para consultas por palavra-chave
# ----------------------------------------------------------------------


def _build_keyword_index() -> dict[str, list[int]]:
    """Build keyword index from loaded deck."""
    index: dict[str, list[int]] = {}
    for symbol in _CIGANO_DECK:
        for kw in symbol.themes:
            normalized = kw.lower().strip()
            if normalized not in index:
                index[normalized] = []
            index[normalized].append(symbol.id)
        for kw in symbol.alternate_names:
            normalized = kw.lower().strip()
            if normalized not in index:
                index[normalized] = []
            index[normalized].append(symbol.id)
    return index


_KEYWORD_INDEX: dict[str, list[int]] = _build_keyword_index()


# ----------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------


def get_all_symbols() -> list[CiganoSymbol]:
    """Retorna lista com todas as 36 cartas do Baralho Cigano.

    Returns:
        Lista de CiganoSymbol em ordem numérica (1–36).
    """
    return list(_CIGANO_DECK)


def get_symbol_by_id(symbol_id: int) -> Optional[CiganoSymbol]:
    """Retorna o símbolo correspondente ao ID fornecido.

    Args:
        symbol_id: Identificador único da carta (1–36).

    Returns:
        CiganoSymbol correspondente ou None se não encontrado.
    """
    for symbol in _CIGANO_DECK:
        if symbol.id == symbol_id:
            return symbol
    return None


def get_symbol_by_name(name: str) -> Optional[CiganoSymbol]:
    """Retorna o símbolo correspondente ao nome fornecido.

    A busca é case-insensitive e normaliza espaços.
    Suporta busca por nome oficial, nome_pt, e alternate_names.

    Args:
        name: Nome da carta (ex: "Estrela", "A Casa", "Cruz", "The Kiss").

    Returns:
        CiganoSymbol correspondente ou None se não encontrado.
    """
    normalized = name.lower().strip()
    for symbol in _CIGANO_DECK:
        if symbol.name.lower() == normalized or symbol.name_pt.lower() == normalized:
            return symbol
        for alt_name in symbol.alternate_names:
            if alt_name.lower().strip() == normalized:
                return symbol
    return None


def match_keyword(keyword: str) -> list[CiganoSymbol]:
    """Retorna os símbolos que correspondem a uma palavra-chave.

    A busca é case-insensitive e normaliza espaços. Suporta correspondência
    parcial (a palavra-chave precisa estar contida na keyword indexada).

    Args:
        keyword: Palavra ou termo a buscar (ex: "casa", "amor", "viagem").

    Returns:
        Lista de CiganoSymbol que correspondem à palavra-chave (pode ser vazia).
    """
    if not keyword:
        return []

    normalized = keyword.lower().strip()

    results: list[CiganoSymbol] = []
    seen_ids: set[int] = set()

    for indexed_kw, symbol_ids in _KEYWORD_INDEX.items():
        if normalized in indexed_kw or indexed_kw in normalized:
            for sid in symbol_ids:
                if sid not in seen_ids:
                    symbol = get_symbol_by_id(sid)
                    if symbol:
                        results.append(symbol)
                        seen_ids.add(sid)

    return results


def get_themes() -> list[str]:
    """Retorna a lista de temas únicos presentes no catálogo.

    Returns:
        Lista ordenada de nomes de temas.
    """
    return sorted({s.themes[0] for s in _CIGANO_DECK if s.themes})


def get_symbols_by_theme(theme: str) -> list[CiganoSymbol]:
    """Retorna todos os símbolos belonging a um tema específico.

    Args:
        theme: Nome do tema (ex: "trabalho", "relação", "espiritual").

    Returns:
        Lista de CiganoSymbol do tema especificado.
    """
    normalized = theme.lower().strip()
    return [s for s in _CIGANO_DECK if s.themes and s.themes[0] == normalized]


def get_symbol_count() -> int:
    """Retorna o número total de símbolos no catálogo.

    Returns:
        Contagem de símbolos (deve ser 36).
    """
    return len(_CIGANO_DECK)
