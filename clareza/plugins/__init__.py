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

from clareza.plugins.types import PluginDefinition, PluginCapability
from clareza.plugins.loader import (
    PluginLoader,
    PluginLoadError,
    PluginDiscoveryError,
    discover_plugins,
    load_plugin_safely,
)

__version__ = "0.1.0"
__all__ = [
    "PluginDefinition",
    "PluginCapability",
    "PluginManager",
    "PluginLoader",
    "PluginLoadError",
    "PluginDiscoveryError",
    "discover_plugins",
    "load_plugin_safely",
]
