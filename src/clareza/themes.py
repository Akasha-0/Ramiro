# coding: utf-8
"""Theme definitions and card-to-theme mapping for Clareza."""

from typing import Optional

# Core themes based on card keyword analysis
THEMES = [
    "ação",
    "amor",
    "conhecimento",
    "transformação",
    "estrutura",
    "espiritual",
    "natureza",
    "proteção",
    "dualidade",
]

# Mapping from keywords to themes
THEME_KEYWORDS: dict[str, list[str]] = {
    "ação": [
        "ação",
        "habilidade",
        "magia",
        "ação rápida",
        "avanço",
        "determinação",
        "controle",
        "vontade",
    ],
    "amor": [
        "amor",
        "união",
        "escolha",
        "amizade",
        "lealdade",
        "proteção",
        "confiança",
        "compromisso",
        "beleza",
        "satisfação",
        "parcerias",
        "companheirismo",
        "comunidade",
    ],
    "conhecimento": [
        "intuição",
        "mistério",
        "sabedoria",
        "busca interior",
        "visão",
        "verdade",
        "causa e efeito",
        "inconsciente",
        "exploração",
    ],
    "transformação": [
        "transformação",
        "mudança",
        "destino",
        "ciclos",
        "mudança radical",
        "fim",
        "renovação",
        "renascimento",
        "liberação",
    ],
    "estrutura": [
        "autoridade",
        "estrutura",
        "poder",
        "estabilidade",
        "conselho",
        "orientação",
        "ética",
        "julgamento",
        "avaliação",
        "hierarquia",
        "lar",
        "segurança",
        "refúgio",
    ],
    "espiritual": [
        "solidão",
        "introspecção",
        "sacrifício",
        "nova perspectiva",
        "pausa",
        "equilíbrio",
        "harmonia",
        "esperança",
        "inspiração",
        "luz",
        "fé",
        "julgamento",
        "redenção",
        "avaliação",
    ],
    "natureza": [
        "abundância",
        "fertilidade",
        "natureza",
        "crescimento",
        "saúde",
        "raízes",
        "vitalidade",
        "alegria",
        "sucesso",
    ],
    "proteção": [
        "esperança",
        "estabilidade",
        "confiança",
        "segurança",
        "lealdade",
        "proteção",
        "amizade",
        "lar",
    ],
    "dualidade": [
        "ilusão",
        "armadilha",
        "vício",
        "destruição",
        "revelação",
        "caos",
        "sombra",
        "materialismo",
    ],
}

# Card ID to themes mapping (derived from card keywords)
CARD_THEMES: dict[int, list[str]] = {
    1: ["ação", "conhecimento"],        # O Mago
    2: ["conhecimento", "espiritual"],  # A Papisa
    3: ["natureza", "amor"],            # A Imperatriz
    4: ["estrutura", "ação"],            # O Imperador
    5: ["espiritual", "estrutura"],      # O Papa
    6: ["amor", "ação"],                # Os Enamorados
    7: ["ação", "transformação"],       # O Carro
    8: ["conhecimento", "espiritual"],  # A Justiça
    9: ["espiritual", "conhecimento"],   # A Eremita
    10: ["transformação", "dualidade"], # A Roda da Fortuna
    11: ["ação", "espiritual"],          # A Força
    12: ["espiritual", "transformação"],# O Enforcado
    13: ["transformação", "dualidade"],  # A Morte
    14: ["espiritual", "natureza"],     # A Temperança
    15: ["dualidade", "proteção"],      # O Diabo
    16: ["dualidade", "transformação"], # A Torre
    17: ["espiritual", "natureza"],      # A Estrela
    18: ["conhecimento", "dualidade"],   # A Lua
    19: ["natureza", "ação"],            # O Sol
    20: ["espiritual", "transformação"],# O Julgamento
    21: ["espiritual", "natureza"],      # O Mundo
    22: ["ação", "transformação"],       # O Louco
    23: ["amor", "proteção"],            # A Fidellidade
    24: ["ação", "transformação"],       # O Cavaleiro
    25: ["amor", "proteção"],            # O Cão
    26: ["natureza", "estrutura"],       # As Árvores
    27: ["natureza", "amor"],            # As Flores
    28: ["ação", "transformação"],       # A Serra
    29: ["ação", "transformação"],       # O Navio
    30: ["proteção", "natureza"],       # A Âncora
    31: ["ação", "conhecimento"],       # As Águias
    32: ["ação", "natureza"],            # A Estrela Cadente
    33: ["transformação", "natureza"],   # A Cegonha
    34: ["amor", "proteção"],           # Os Cães
    35: ["estrutura", "proteção"],      # A Casa
    36: ["natureza", "conhecimento"],     # A Floresta
}


def get_themes_for_card(card_id: int) -> list[str]:
    """Get themes for a given card ID.

    Args:
        card_id: The numeric ID of the card (1-36).

    Returns:
        List of theme names associated with the card.
    """
    return CARD_THEMES.get(card_id, [])


def get_theme_for_keyword(keyword: str) -> Optional[str]:
    """Find which theme a keyword belongs to.

    Args:
        keyword: A keyword string to look up.

    Returns:
        The theme name if found, None otherwise.
    """
    for theme, keywords in THEME_KEYWORDS.items():
        if keyword.lower() in [k.lower() for k in keywords]:
            return theme
    return None