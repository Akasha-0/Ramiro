"""Plugin system — Sistema de Clareza Simbólico-Estratégica.

Módulo core do sistema de plugins que permite extensão
da funcionalidade base através de plugins carregados
dinamicamente via importlib.

Features:
- Card databases (custom Lenormand variants)
- Analysis rules extensions
- Custom report sections generators

Plugins são carregados do diretório ~/.clareza/plugins/
e definidos seguindo o PluginDefinition.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any, List, Tuple

from src.plugins.types import PluginDefinition, PluginCapability
from src.plugins.hooks import CardHook, AnalysisHook, SectionHook


__version__ = "0.1.0"
__all__ = [
    "PluginDefinition",
    "PluginCapability",
    "PluginManager",
    "PluginRegistry",
    "PluginLoader",
    "load_plugins",
    "load_plugins_safely",
    "CardHook",
    "AnalysisHook",
    "SectionHook",
]


@dataclass
class PluginRegistry:
    """Registry for loaded plugins.

    Attributes:
        plugins: Dict mapping plugin names to definitions.
        cards: Dict mapping card names to card dicts from plugins.
        rules: Dict mapping rule names to rule definitions from plugins.
    """

    plugins: dict[str, PluginDefinition] = field(default_factory=dict)
    cards: dict[str, dict[str, Any]] = field(default_factory=dict)
    rules: dict[str, Any] = field(default_factory=dict)


def load_plugins(directory: Optional[str] = None) -> list[PluginDefinition]:
    """Load plugins from directory.

    Args:
        directory: Directory containing .py plugin files.
            Defaults to ~/.clareza/plugins/.

    Returns:
        List of PluginDefinition objects loaded successfully.
        Malformed plugins are skipped with a warning logged.
    """
    import logging
    from pathlib import Path
    import importlib.util

    registry = PluginRegistry()
    loader = PluginLoader(registry=registry)

    if directory is None:
        import os.path
        home = os.path.expanduser("~")
        directory = os.path.join(home, ".clareza", "plugins")

    plugins_dir = Path(directory)
    if not plugins_dir.is_dir():
        logging.getLogger(__name__).warning(
            f"Plugins directory not found: {directory}"
        )
        return []

    discovered = loader.discover_plugins(directory=str(plugins_dir))

    return list(discovered.values())


def load_plugins_safely(
    directory: Optional[str] = None,
) -> tuple[list[PluginDefinition], list[str]]:
    """Load plugins with error collection.

    Args:
        directory: Directory containing .py plugin files.
            Defaults to ~/.clareza/plugins/.

    Returns:
        Tuple of (loaded_plugins, error_messages).
        Errors are logged but do not block other plugins.
    """
    import logging
    from pathlib import Path
    import importlib.util

    registry = PluginRegistry()
    errors: list[str] = []
    loaded: list[PluginDefinition] = []

    if directory is None:
        import os.path
        home = os.path.expanduser("~")
        directory = os.path.join(home, ".clareza", "plugins")

    plugins_dir = Path(directory)
    if not plugins_dir.is_dir():
        logging.getLogger(__name__).warning(
            f"Plugins directory not found: {directory}"
        )
        return [], []

    for plugin_file in plugins_dir.glob("*.py"):
        try:
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(
                module_name, plugin_file
            )
            if spec is None or spec.loader is None:
                errors.append(f"Failed to load spec: {plugin_file}")
                continue

            module = importlib.util.module_from_spec(spec)
            if spec.loader is not None:
                spec.loader.exec_module(module)

            if hasattr(module, "PLUGIN_DEFINITION"):
                definition = module.PLUGIN_DEFINITION
                if isinstance(definition, dict):
                    plugin_def = PluginDefinition(**definition)
                    registry.plugins[plugin_def.name] = plugin_def
                    loaded.append(plugin_def)
                elif isinstance(definition, PluginDefinition):
                    registry.plugins[definition.name] = definition
                    loaded.append(definition)

        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Plugin failed to load {plugin_file}: {e}"
            )
            errors.append(str(e))

    return loaded, errors


class PluginManager:
    """Central manager for loaded plugins.

    Coordinates all plugin operations including
    card database aggregation, rules extension,
    and custom section generation.

    Attributes:
        registry: Internal plugin registry.
        loader: Plugin loader instance.
    """

    def __init__(self) -> None:
        """Initialize plugin manager with empty registry."""
        self.registry: PluginRegistry = PluginRegistry()
        self.loader: PluginLoader = PluginLoader(registry=self.registry)

    def get_plugins(self) -> list[PluginDefinition]:
        """Get list of loaded plugin definitions.

        Returns:
            List of PluginDefinition objects.
        """
        return list(self.registry.plugins.values())

    def get_extended_cards(self) -> dict[str, dict[str, Any]]:
        """Get all cards aggregated from plugins.

        Returns:
            Dict mapping card names to card dicts.
        """
        return dict(self.registry.cards)

    def get_extended_sections(
        self,
    ) -> list[tuple[str, Callable[..., str]]]:
        """Get custom section generators from plugins.

        Returns:
            List of tuples (section_name, generator_func).
        """
        sections: list[tuple[str, Callable[..., str]]] = []
        for plugin_def in self.registry.plugins.values():
            for cap in plugin_def.capabilities:
                if cap.type == "custom_section" and plugin_def.section_generator:
                    sections.append(
                        (cap.name, plugin_def.section_generator)
                    )
        return sections

    def load_from_directory(self, directory: str) -> None:
        """Load plugins from directory.

        Args:
            directory: Path to plugins directory.
        """
        discovered = self.loader.discover_plugins(directory=directory)

        for name, plugin_def in discovered.items():
            self.registry.plugins[name] = plugin_def

            if plugin_def.cards:
                for card in plugin_def.cards:
                    if isinstance(card, dict) and "name" in card:
                        self.registry.cards[card["name"]] = card

            if plugin_def.analysis_rules:
                cap_names = [c.type for c in plugin_def.capabilities]
                if "analysis_rules" in cap_names:
                    self.registry.rules.update(
                        plugin_def.analysis_rules
                    )


class PluginLoader:
    """Discovers and loads plugin modules using importlib.

    Attributes:
        registry: Plugin registry to populate.
    """

    def __init__(self, registry: PluginRegistry) -> None:
        """Initialize loader with registry.

        Args:
            registry: Plugin registry to populate.
        """
        self.registry = registry

    def discover_plugins(
        self, directory: str
    ) -> dict[str, PluginDefinition]:
        """Discover and load plugins from directory.

        Args:
            directory: Path to plugins directory.

        Returns:
            Dict mapping plugin names to definitions.
        """
        import logging
        from pathlib import Path
        import importlib.util

        discovered: dict[str, PluginDefinition] = {}
        plugins_dir = Path(directory)

        if not plugins_dir.is_dir():
            return discovered

        for plugin_file in plugins_dir.glob("*.py"):
            try:
                module_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(
                    module_name, plugin_file
                )
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                if spec.loader is not None:
                    spec.loader.exec_module(module)

                if hasattr(module, "PLUGIN_DEFINITION"):
                    definition = module.PLUGIN_DEFINITION
                    if isinstance(definition, dict):
                        plugin_def = PluginDefinition(**definition)
                        discovered[plugin_def.name] = plugin_def
                    elif isinstance(definition, PluginDefinition):
                        discovered[definition.name] = definition

            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"Plugin failed to load {plugin_file}: {e}"
                )
                continue

        return discovered


def get_manager() -> PluginManager:
    """Get global plugin manager singleton.

    Returns:
        PluginManager instance.
    """
    return PluginManager()