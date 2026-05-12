"""Sample Lenormand deck plugin for Clareza.

This plugin provides a complete Lenormand card deck, demonstrating
how to create a card database plugin for the Clareza system.

The Lenormand deck consists of 36 cards, each with German/French
names and traditional meanings used in cartomancy practice.

Usage:
    Copy this file to ~/.clareza/plugins/lenormand_deck.py
    Run: clareza plugins list
    Run: clareza analyze -i "card:name" --cards lenormand
"""

from typing import Any

# =============================================================================
# Lenormand Card Definitions (36 cards - traditional Grand Jeu Lenormand)
# =============================================================================

LENORMAND_CARDS = [
    {
        "name": "Rider",
        "name_pt": "Cavaleiro",
        "meaning": "Notícias, mensagens, chegadas, movimento rápido",
        "keywords": ["cavaleiro", "cavalo", "notícia", "mensagem", "chegada"],
        "theme": "movimento",
    },
    {
        "name": "Clover",
        "name_pt": "Trevo",
        "meaning": "Sorte, oportunidade, otimismo, pequena fortuna",
        "keywords": ["trevo", "sorte", "oportunidade", "otimismo"],
        "theme": "fortuna",
    },
    {
        "name": "Ship",
        "name_pt": "Navio",
        "meaning": "Viagem, comércio, jornada, aventura",
        "keywords": ["navio", "viagem", "comércio", "jornada"],
        "theme": "movimento",
    },
    {
        "name": "House",
        "name_pt": "Casa",
        "meaning": "Lar, família, estabilidade, segurança doméstica",
        "keywords": ["casa", "lar", "família", "estabilidade"],
        "theme": "domínio",
    },
    {
        "name": "Tree",
        "name_pt": "Árvore",
        "meaning": "Saúde, crescimento, desenvolvimento, raízes",
        "keywords": ["árvore", "saúde", "crescimento", "natureza"],
        "theme": "natureza",
    },
    {
        "name": "Clouds",
        "name_pt": "Nuvens",
        "meaning": "Confusão, incerteza, problemas, ambiguidade",
        "keywords": ["nuvens", "confusão", "incerteza", "nublado"],
        "theme": "turbulência",
    },
    {
        "name": "Snake",
        "name_pt": "Serpente",
        "meaning": "Engano, conflito, transformação, sabedoria oculta",
        "keywords": ["serpente", "engano", "conflito", "transformação"],
        "theme": "perigo",
    },
    {
        "name": "Coffin",
        "name_pt": "Caixão",
        "meaning": "Fim, perda, transformação, renovação",
        "keywords": ["caixão", "fim", "perda", "transformação"],
        "theme": "transição",
    },
    {
        "name": "Bouquet",
        "name_pt": "Buquê",
        "meaning": "Felicidade, gratificação, harmonia, beleza",
        "keywords": ["buquê", "flores", "felicidade", "harmonia"],
        "theme": "harmonia",
    },
    {
        "name": "Mower",
        "name_pt": "Ceifador",
        "meaning": "Trabalho, esforço, coleta, fim de ciclo",
        "keywords": ["ceifa", "trabalho", "esforço", "colheita"],
        "theme": "trabalho",
    },
    {
        "name": "Hawk",
        "name_pt": "Falcão",
        "meaning": "Alerta, ambição, oportunidades, rapidez",
        "keywords": ["falcão", "alerta", "ambição", "oportunidade"],
        "theme": "ação",
    },
    {
        "name": "Bear",
        "name_pt": "Urso",
        "meaning": "Força, autoridade, proteção, questões financeiras",
        "keywords": ["urso", "força", "autoridade", "proteção"],
        "theme": "força",
    },
    {
        "name": "Dog",
        "name_pt": "Cão",
        "meaning": "Amizade, lealdade, proteção, confiança",
        "keywords": ["cão", "amizade", "lealdade", "fiel"],
        "theme": "relacionamento",
    },
    {
        "name": "Tower",
        "name_pt": "Torre",
        "meaning": "Autoridade, independência, clareza, instituições",
        "keywords": ["torre", "autoridade", "independência", "altura"],
        "theme": "domínio",
    },
    {
        "name": "Garden",
        "name_pt": "Jardim",
        "meaning": "Sociedade, eventos sociais, reunião, comunidade",
        "keywords": ["jardim", "sociedade", "social", "reunião"],
        "theme": "comunidade",
    },
    {
        "name": "Mountain",
        "name_pt": "Montanha",
        "meaning": "Obstáculo, desafio, resistência, superação",
        "keywords": ["montanha", "obstáculo", "desafio", "dificuldade"],
        "theme": "adversidade",
    },
    {
        "name": "Ways",
        "name_pt": "Caminhos",
        "meaning": "Decisão, escolha, cruzamento, bifurcação",
        "keywords": ["caminho", "decisão", "escolha", "bifurcação"],
        "theme": "decisão",
    },
    {
        "name": "Child",
        "name_pt": "Criança",
        "meaning": "Início, pureza, potencial, novo começo",
        "keywords": ["criança", "início", "pureza", "potencial"],
        "theme": "início",
    },
    {
        "name": "Fox",
        "name_pt": "Raposa",
        "meaning": "Astúcia, cautela, engano, adaptação",
        "keywords": ["raposa", "astúcia", "cautela", "esperteza"],
        "theme": "estratégia",
    },
    {
        "name": "Bull",
        "name_pt": "Touro",
        "meaning": "Prosperidade, estabilidade, paciência, confirmação",
        "keywords": ["touro", "prosperidade", "estabilidade", "força"],
        "theme": "abundância",
    },
    {
        "name": "Stars",
        "name_pt": "Estrelas",
        "meaning": "Esperança, inspiração, orientação, espiritualidade",
        "keywords": ["estrelas", "esperança", "inspiração", "orientação"],
        "theme": "espiritual",
    },
    {
        "name": "Stork",
        "name_pt": "Cegonha",
        "meaning": "Mudança, renovação, transformação, maternidade",
        "keywords": ["cegonha", "mudança", "renovação", "transformação"],
        "theme": "mudança",
    },
    {
        "name": "Book",
        "name_pt": "Livro",
        "meaning": "Conhecimento, segredos, formação, investigação",
        "keywords": ["livro", "conhecimento", "segredos", "estudo"],
        "theme": "conhecimento",
    },
    {
        "name": "Letter",
        "name_pt": "Carta",
        "meaning": "Comunicação, notícias, documentos, convites",
        "keywords": ["carta", "comunicação", "notícia", "documento"],
        "theme": "comunicação",
    },
    {
        "name": "Man",
        "name_pt": "Homem",
        "meaning": "O masculino, ação, figura paterna, parceiro",
        "keywords": ["homem", "masculino", "pai", "parceiro"],
        "theme": "pessoa",
    },
    {
        "name": "Woman",
        "name_pt": "Mulher",
        "meaning": "O feminino, intuição, figura materna, parceira",
        "keywords": ["mulher", "feminino", "mãe", "parceira"],
        "theme": "pessoa",
    },
    {
        "name": "Heart",
        "name_pt": "Coração",
        "meaning": "Amor, emoção, paixão, relacionamentos",
        "keywords": ["coração", "amor", "emoção", "paixão"],
        "theme": "emoção",
    },
    {
        "name": "Ring",
        "name_pt": "Anel",
        "meaning": "Compromisso, acordo, promessa, compromisso",
        "keywords": ["anel", "compromisso", "acordo", "promessa"],
        "theme": "relacionamento",
    },
    {
        "name": "Scissors",
        "name_pt": "Tesoura",
        "meaning": "Decisão, corte, separação, conflito",
        "keywords": ["tesoura", "decisão", "corte", "separação"],
        "theme": "decisão",
    },
    {
        "name": "Chimney",
        "name_pt": "Chaminé",
        "meaning": "Fogo, calor domesticado, conforto, lar",
        "keywords": ["chaminé", "fogo", "calor", "conforto"],
        "theme": "domínio",
    },
    {
        "name": "Fish",
        "name_pt": "Peixe",
        "meaning": "Dinheiro, prosperidade, intuição, emoções profundas",
        "keywords": ["peixe", "dinheiro", "prosperidade", "intuição"],
        "theme": "abundância",
    },
    {
        "name": "Anchor",
        "name_pt": "Âncora",
        "meaning": "Estabilidade, segurança, raíz, tradição",
        "keywords": ["âncora", "estabilidade", "segurança", "raíz"],
        "theme": "estabilidade",
    },
    {
        "name": "Cross",
        "name_pt": "Cruz",
        "meaning": "Sofrimento, peso, burden, desafio espiritual",
        "keywords": ["cruz", "sofrimento", "peso", "desafio"],
        "theme": "adversidade",
    },
    {
        "name": "Key",
        "name_pt": "Chave",
        "meaning": "Solução, descoberta, abertura, oportunidade",
        "keywords": ["chave", "solução", "descoberta", "abertura"],
        "theme": "oportunidade",
    },
    {
        "name": "Birds",
        "name_pt": "Pássaros",
        "meaning": "Mensagens, comunicação, leves preocupações",
        "keywords": ["pássaros", "mensagens", "comunicação", "voo"],
        "theme": "comunicação",
    },
    {
        "name": "Lily",
        "name_pt": "Lírio",
        "meaning": "Paz, tranquilidade, velhice, sabedoria",
        "keywords": ["lírio", "paz", "tranquilidade", "sabedoria"],
        "theme": "harmonia",
    },
]


# =============================================================================
# Plugin Definition
# =============================================================================

PLUGIN_DEFINITION = {
    "name": "lenormand_deck",
    "version": "0.1.0",
    "description": "Sample Lenormand deck plugin with 36 traditional cards",
    "author": "Clareza Community",
    "capabilities": [
        {
            "type": "card_database",
            "name": "Lenormand Deck",
            "description": "Traditional 36-card Lenormand deck with German/French names",
        },
        {
            "type": "analysis_rules",
            "name": "Lenormand Analysis Rules",
            "description": "Theme weights and pattern keywords for Lenormand cards",
        },
        {
            "type": "custom_section",
            "name": "Lenormand Overview",
            "description": "Overview section with Lenormand-specific insights",
        },
    ],
    "cards": LENORMAND_CARDS,
    "analysis_rules": {
        "theme_weights": {
            "movimento": 1.2,
            "decisão": 1.5,
            "relacionamento": 1.3,
            "mudança": 1.4,
            "transição": 1.3,
            "perigo": 0.8,
            "fortuna": 1.1,
            "ação": 1.3,
            "abundância": 1.2,
            "comunicação": 1.1,
        },
        "pattern_keywords": {
            "movimento_rápido": ["cavaleiro", "falcão", "navio"],
            "social": ["jardim", "casa", "cães"],
            "decisão_importante": ["caminhos", "tesoura", "anel"],
            "conflito": ["serpente", "raposa", "montanha"],
        },
    },
    "section_generator": None,
}


# =============================================================================
# Section Generator Function
# =============================================================================

def _lenormand_section_generator(data: Any) -> str:
    """Generate Lenormand-specific custom report section.

    Args:
        data: Analysis data passed to the generator.

    Returns:
        Formatted markdown section content.
    """
    content = data.get("content", {}) if isinstance(data, dict) else {}
    cards_found = content.get("cards_encontradas", [])
    temas = content.get("temas", [])

    # Count theme frequencies
    theme_counts: dict[str, int] = {}
    for tema in temas:
        theme_counts[tema] = theme_counts.get(tema, 0) + 1

    # Sort themes by frequency
    sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)

    # Get dominant theme
    dominant_theme = sorted_themes[0][0] if sorted_themes else "geral"

    # Build theme summary
    theme_summary = "\n".join(
        f"- **{theme}**: {count} ocorrência(s)"
        for theme, count in sorted_themes[:5]
    ) if sorted_themes else "Nenhum tema identificado"

    return f"""## Visão Geral do Lenormand

Esta seção foi gerada pelo plugin Lenormand Deck.

### Análise de Temas

**Tema dominante:** {dominant_theme}

**Distribuição de temas:**
{theme_summary}

### Cartas Identificadas

Total de cartas encontradas: {len(cards_found)}

{', '.join(cards_found) if cards_found else 'Nenhuma carta específica identificada'}

### Notas de Implementação

- Plugin Lenormand Deck carregado com sucesso
- {len(LENORMAND_CARDS)} cartas disponíveis no deck
- Análise temática aplicada às cartas identificadas

---
*Gerado por lenormand_deck v{PLUGIN_DEFINITION['version']}*
"""


# Attach the generator function to the definition
PLUGIN_DEFINITION["section_generator"] = _lenormand_section_generator


# =============================================================================
# Optional On-Load Hook
# =============================================================================

def on_load() -> None:
    """Hook called when plugin is loaded.

    Use this for initialization tasks like:
    - Logging successful load
    - Validating deck structure
    - Setting up configuration
    """
    import logging
    logger = logging.getLogger("clareza.plugins.lenormand")
    logger.info(
        "lenormand_deck plugin loaded: %d cards available",
        len(LENORMAND_CARDS)
    )


# Attach on_load hook
PLUGIN_DEFINITION["on_load"] = on_load
