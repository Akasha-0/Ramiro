"""Plugin type definitions — Sistema de Clareza Simbólico-Estratégica.

Define os contratos e estruturas de dados para o sistema de plugins.
Todos os plugins devem expor as estruturas definidas aqui.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any


@dataclass
class PluginCapability:
    """Capability offered by a plugin.

    Attributes:
        type: Type of capability
            ("card_database", "analysis_rules", "custom_section").
        name: Human-readable name of the capability.
        description: Description of what the capability does.
        config: Optional configuration dict for this capability.
    """

    type: str
    name: str
    description: str = ""
    config: Optional[dict[str, Any]] = None


@dataclass
class PluginDefinition:
    """Definition of a plugin for the Clareza system.

    Attributes:
        name: Unique name of the plugin.
        version: Version string of the plugin.
        description: Description of what the plugin does.
        author: Author of the plugin.
        capabilities: List of capabilities provided by this plugin.
        cards: List of card dicts (for card_database capability).
        analysis_rules: Optional dict of analysis rules (for analysis_rules capability).
        section_generator: Optional callable (for custom_section capability).
        on_load: Optional callable executed when plugin loads.
    """

    name: str
    version: str
    description: str = ""
    author: str = ""
    capabilities: list[PluginCapability] = field(default_factory=list)
    cards: Optional[list[dict[str, Any]]] = None
    analysis_rules: Optional[dict[str, Any]] = None
    section_generator: Optional[Callable[..., str]] = None
    on_load: Optional[Callable[[], None]] = None
