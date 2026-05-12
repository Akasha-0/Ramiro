"""Sample plugin for testing the Clareza plugin system.

This plugin demonstrates the minimum required structure
for a valid Clareza plugin with all three capability types:
- card_database: provides additional cards
- analysis_rules: provides custom analysis rules
- custom_section: provides a custom report section generator
"""

from typing import Any

# Required: Plugin definition following PluginDefinition dataclass structure
PLUGIN_DEFINITION = {
    "name": "sample_plugin",
    "version": "0.1.0",
    "description": "Sample plugin for testing the plugin system",
    "author": "Clareza Test Suite",
    "capabilities": [
        {
            "type": "card_database",
            "name": "Sample Cards",
            "description": "Sample cards for testing",
        },
        {
            "type": "analysis_rules",
            "name": "Sample Analysis Rules",
            "description": "Custom analysis rules for testing",
        },
        {
            "type": "custom_section",
            "name": "Sample Section",
            "description": "Custom report section for testing",
        },
    ],
    "cards": [
        {
            "name": "Sample Carta 1",
            "name_pt": "Carta Amostra 1",
            "meaning": "Primeira carta de exemplo do plugin",
            "keywords": ["teste", "amostra", "exemplo"],
            "theme": "teste",
        },
        {
            "name": "Sample Carta 2",
            "name_pt": "Carta Amostra 2",
            "meaning": "Segunda carta de exemplo do plugin",
            "keywords": ["teste", "amostra", "exemplo2"],
            "theme": "teste",
        },
    ],
    "analysis_rules": {
        "theme_weights": {
            "teste": 1.5,
        },
        "pattern_keywords": {
            "sample_pattern": ["teste", "amostra"],
        },
    },
    "section_generator": None,  # Will be set below
}


def _sample_section_generator(data: Any) -> str:
    """Generate a sample custom report section.

    Args:
        data: Analysis data passed to the generator.

    Returns:
        Formatted markdown section content.
    """
    content = data.get("content", {}) if isinstance(data, dict) else {}
    tema = content.get("tema", "geral")

    return f"""## Seção Personalizada do Sample Plugin

Esta seção foi gerada pelo plugin de exemplo.

**Tema identificado:** {tema}

### Notas de Implementação

- O plugin foi carregado com sucesso
- A seção foi gerada pelo section_generator
- Dados recebidos: {type(data).__name__}

---
*Gerado por sample_plugin v{PLUGIN_DEFINITION['version']}*
"""


# Attach the generator function to the definition
PLUGIN_DEFINITION["section_generator"] = _sample_section_generator


def on_load() -> None:
    """Optional hook called when plugin is loaded.

    Use this for initialization tasks like:
    - Setting up connections
    - Validating configuration
    - Registering handlers
    """
    import logging
    logger = logging.getLogger("clareza.plugins.sample")
    logger.info("sample_plugin loaded successfully")


# Attach on_load hook
PLUGIN_DEFINITION["on_load"] = on_load