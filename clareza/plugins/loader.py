"""Plugin loader — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por descobrir e carregar plugins Python
usando importlib. Plugins são arquivos .py que exportam
PLUGIN_DEFINITION.

Plugins são carregados do diretório ~/.clareza/plugins/ por padrão,
mas podem ser especificados via parâmetro directory.
"""

import importlib.util
import logging
from pathlib import Path
from typing import Optional

from clareza.plugins.types import PluginDefinition, PluginCapability

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Exceção lançada quando o carregamento de um plugin falha."""

    def __init__(
        self,
        plugin_name: str,
        reason: str,
        details: Optional[str] = None,
        recovery: Optional[str] = None,
    ) -> None:
        self.plugin_name = plugin_name
        self.reason = reason
        self.details = details
        self.recovery = recovery
        full = f"Plugin '{plugin_name}' falhou: {reason}"
        if details:
            full = f"{full} — {details}"
        if recovery:
            full = f"{full}\nDica: {recovery}"
        super().__init__(full)


class PluginDiscoveryError(Exception):
    """Exceção lançada quando a descoberta de plugins falha."""

    def __init__(self, directory: str, reason: str) -> None:
        self.directory = directory
        self.reason = reason
        super().__init__(f"Falha ao descobrir plugins em '{directory}': {reason}")


class PluginLoader:
    """Descobre e carrega plugins usando importlib.

    Cada plugin deve exportar PLUGIN_DEFINITION (dict ou PluginDefinition).

    Attributes:
        safe_mode: Se True, erros de carregamento são capturados e logados
            ao invés de levantar exceções.
    """

    def __init__(self, safe_mode: bool = True) -> None:
        self.safe_mode = safe_mode
        self._loaded_plugins: dict[str, PluginDefinition] = {}
        self._load_errors: list[str] = []

    @property
    def loaded_plugins(self) -> dict[str, PluginDefinition]:
        """Retorna dicionário de plugins carregados."""
        return self._loaded_plugins

    @property
    def load_errors(self) -> list[str]:
        """Retorna lista de erros ocurridos durante carregamento."""
        return self._load_errors

    def discover_plugins(self, directory: str) -> dict[str, PluginDefinition]:
        """Descobre e carrega plugins de um diretório.

        Args:
            directory: Caminho para o diretório de plugins.

        Returns:
            Dict mapeando nomes de plugins para PluginDefinition.
        """
        discovered: dict[str, PluginDefinition] = {}
        plugins_dir = Path(directory)

        if not plugins_dir.is_dir():
            if not self.safe_mode:
                raise PluginDiscoveryError(directory, "diretório não encontrado")
            logger.warning("Diretório de plugins não encontrado: %s", directory)
            return discovered

        logger.debug("Descobrindo plugins em: %s", plugins_dir)

        for plugin_file in plugins_dir.glob("*.py"):
            if plugin_file.stem.startswith("_"):
                continue

            try:
                plugin_def = self._load_plugin_file(plugin_file)
                if plugin_def:
                    discovered[plugin_def.name] = plugin_def
                    self._loaded_plugins[plugin_def.name] = plugin_def
                    logger.info("Plugin carregado: %s (v%s)", plugin_def.name, plugin_def.version)
            except PluginLoadError as e:
                self._load_errors.append(str(e))
                if not self.safe_mode:
                    raise
                logger.warning("Plugin ignorado: %s", e)

        logger.debug(
            "Descoberta concluída: %d plugins carregados de %d arquivos",
            len(discovered),
            len(list(plugins_dir.glob("*.py"))),
        )
        return discovered

    def load_plugin(self, file_path: str) -> Optional[PluginDefinition]:
        """Carrega um plugin específico de um arquivo.

        Args:
            file_path: Caminho para o arquivo .py do plugin.

        Returns:
            PluginDefinition carregado ou None se falhar.
        """
        plugin_path = Path(file_path)
        if not plugin_path.exists():
            logger.error("Arquivo de plugin não encontrado: %s", file_path)
            return None

        try:
            return self._load_plugin_file(plugin_path)
        except PluginLoadError as e:
            logger.error("Falha ao carregar plugin: %s", e)
            return None

    def get_plugin(self, name: str) -> Optional[PluginDefinition]:
        """Retorna um plugin carregado pelo nome."""
        return self._loaded_plugins.get(name)

    def get_plugins_by_capability(self, capability_type: str) -> list[PluginDefinition]:
        """Retorna plugins que oferecem uma capability específica."""
        return [
            p for p in self._loaded_plugins.values()
            if any(cap.type == capability_type for cap in p.capabilities)
        ]

    def reload(self, directory: str) -> dict[str, PluginDefinition]:
        """Recarrega plugins do diretório, limpando estado anterior."""
        self._loaded_plugins.clear()
        self._load_errors.clear()
        return self.discover_plugins(directory)

    def _load_plugin_file(self, plugin_file: Path) -> PluginDefinition:
        """Carrega um arquivo de plugin individual."""
        module_name = plugin_file.stem

        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if spec is None:
            raise PluginLoadError(
                module_name, "spec inválido",
                details=f"Não foi possível criar spec para {plugin_file}",
                recovery="Verifique se o arquivo contém código Python válido",
            )

        if spec.loader is None:
            raise PluginLoadError(
                module_name, "loader não disponível",
                details=f"Arquivo não pode ser executado como módulo: {plugin_file}",
                recovery="Verifique se o arquivo .py está bem formado",
            )

        try:
            module = importlib.util.module_from_spec(spec)
        except Exception as e:
            raise PluginLoadError(
                module_name, "falha ao criar módulo", details=str(e),
            )

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise PluginLoadError(
                module_name, "erro na execução", details=str(e),
                recovery="Verifique a sintaxe do arquivo Python",
            )

        if not hasattr(module, "PLUGIN_DEFINITION"):
            raise PluginLoadError(
                module_name, "PLUGIN_DEFINITION não encontrado",
                details="O módulo deve exportar 'PLUGIN_DEFINITION'",
                recovery="Adicione PLUGIN_DEFINITION = {...} ao arquivo",
            )

        definition = module.PLUGIN_DEFINITION
        return self._parse_definition(module_name, definition)

    def _parse_definition(
        self, module_name: str, definition: object
    ) -> PluginDefinition:
        """Parseia e valida um PLUGIN_DEFINITION."""
        if isinstance(definition, dict):
            try:
                return PluginDefinition(**definition)
            except TypeError as e:
                raise PluginLoadError(
                    module_name, "definição inválida", details=str(e),
                    recovery="Verifique os campos obrigatórios: name, version",
                )
        elif isinstance(definition, PluginDefinition):
            return definition
        else:
            raise PluginLoadError(
                module_name, "tipo inválido",
                details=f"Esperado dict ou PluginDefinition, obtido {type(definition).__name__}",
                recovery="PLUGIN_DEFINITION deve ser dict ou PluginDefinition",
            )


def discover_plugins(
    directory: str,
    safe_mode: bool = True,
) -> dict[str, PluginDefinition]:
    """Função de conveniência para descoberta de plugins."""
    loader = PluginLoader(safe_mode=safe_mode)
    return loader.discover_plugins(directory)


def load_plugin_safely(
    file_path: str,
) -> tuple[Optional[PluginDefinition], Optional[str]]:
    """Carrega um plugin específico com tratamento de erros.

    Returns:
        Tupla (PluginDefinition, None) em sucesso ou (None, mensagem) em falha.
    """
    loader = PluginLoader(safe_mode=True)
    plugin = loader.load_plugin(file_path)
    errors = loader.load_errors

    if plugin:
        return plugin, None
    elif errors:
        return None, errors[-1]
    else:
        return None, f"Plugin não encontrado ou inválido: {file_path}"
