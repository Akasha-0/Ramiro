"""Plugin Manager — Sistema de Clareza Simbólico-Estratégica.

Módulo central que coordena todas as operações de plugins:
- Descoberta e carregamento de plugins
- Agregação de baralhos customizados
- Registro de regras de análise estendidas
- Geração de seções customizadas para relatórios

Usa PluginLoader de src.plugins.loader para descoberta dinâmica
de plugins via importlib.
"""

import logging
from pathlib import Path
from typing import Optional, Any, Callable

from src.plugins.types import PluginDefinition
from src.plugins.loader import PluginLoader, PluginLoadError, PluginDiscoveryError

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------

# Diretório padrão de plugins do sistema
DEFAULT_PLUGINS_DIR = "~/.clareza/plugins"


# ----------------------------------------------------------------------
# Plugin Manager
# ----------------------------------------------------------------------


class PluginManager:
    """Gerenciador central de plugins carregados.

    Coordena todas as operações de plugins incluindo:
    - Descoberta e carregamento de plugins do sistema de arquivos
    - Agregação de baralhos customizados de múltiplos plugins
    - Registro de regras de análise estendidas
    - Geração de seções customizadas para relatórios

    Attributes:
        plugins_dir: Diretório de plugins a ser escaneado (default: ~/.clareza/plugins).
        safe_mode: Se True, erros de carregamento são capturados e logados.
    """

    def __init__(
        self,
        plugins_dir: Optional[str] = None,
        safe_mode: bool = True,
    ) -> None:
        """Inicializa o gerenciador de plugins.

        Args:
            plugins_dir: Caminho para diretório de plugins. Default: ~/.clareza/plugins.
            safe_mode: Se True (default), erros são capturados silenciosamente.
        """
        self._plugins_dir = plugins_dir or DEFAULT_PLUGINS_DIR
        self._safe_mode = safe_mode
        self._loader = PluginLoader(safe_mode=safe_mode)
        self._plugins: dict[str, PluginDefinition] = {}
        self._plugin_cards: dict[str, dict[str, Any]] = {}
        self._load_errors: list[str] = []

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def load_plugins(self, directory: Optional[str] = None) -> None:
        """Descobre e carrega plugins do diretório especificado.

        Se nenhum diretório for especificado, usa o diretório padrão
        configurado na inicialização.

        Args:
            directory: Caminho para diretório de plugins (opcional).
        """
        target_dir = directory or self._plugins_dir
        logger.debug("Carregando plugins de: %s", target_dir)

        try:
            discovered = self._loader.discover_plugins(target_dir)
            self._update_registry(discovered)
        except PluginDiscoveryError as e:
            logger.warning("Falha na descoberta de plugins: %s", e)
        except PluginLoadError as e:
            logger.warning("Erro ao carregar plugin: %s", e)

    def _update_registry(
        self, discovered: dict[str, PluginDefinition]
    ) -> None:
        """Atualiza o registro interno com plugins descobertos.

        Args:
            discovered: Dict de plugins descobertos.
        """
        for name, plugin_def in discovered.items():
            self._plugins[name] = plugin_def
            self._collect_plugin_cards(plugin_def)
            self._load_errors.extend(self._loader.load_errors)

        logger.info(
            "Registro atualizado: %d plugins carregados", len(self._plugins)
        )

    def _collect_plugin_cards(self, plugin_def: PluginDefinition) -> None:
        """Coleta cartas de um plugin e adiciona ao registro.

        Args:
            plugin_def: Definição do plugin com cartas.
        """
        if not plugin_def.cards:
            return

        for card in plugin_def.cards:
            if isinstance(card, dict) and "name" in card:
                card_name = card["name"]
                # Prefixa nome da carta com nome do plugin para evitar colisão
                unique_key = f"{plugin_def.name}:{card_name}"
                self._plugin_cards[unique_key] = {
                    **card,
                    "_plugin_source": plugin_def.name,
                }
                logger.debug(
                    "Carta registrada: %s (de %s)", card_name, plugin_def.name
                )

    def get_plugins(self) -> list[PluginDefinition]:
        """Retorna lista de plugins carregados.

        Returns:
            Lista de PluginDefinition carregados com sucesso.
        """
        return list(self._plugins.values())

    def get_plugin(self, name: str) -> Optional[PluginDefinition]:
        """Retorna um plugin específico pelo nome.

        Args:
            name: Nome do plugin.

        Returns:
            PluginDefinition ou None se não encontrado.
        """
        return self._plugins.get(name)

    def get_plugins_by_capability(
        self, capability_type: str
    ) -> list[PluginDefinition]:
        """Retorna plugins que oferecem uma capability específica.

        Args:
            capability_type: Tipo de capability (ex: "card_database",
                "analysis_rules", "custom_section").

        Returns:
            Lista de PluginDefinition que têm a capability especificada.
        """
        results: list[PluginDefinition] = []
        for plugin_def in self._plugins.values():
            for cap in plugin_def.capabilities:
                if cap.type == capability_type:
                    results.append(plugin_def)
                    break
        return results

    def get_extended_cards(self) -> dict[str, dict[str, Any]]:
        """Retorna todas as cartas agregadas de plugins.

        Returns:
            Dict mapeando chaves únicas para dicts de cartas.
            A chave é "plugin_name:card_name" para evitar colisões.
        """
        return dict(self._plugin_cards)

    def get_extended_sections(
        self,
    ) -> list[tuple[str, Callable[..., str]]:
        """Retorna geradores de seções customizadas de plugins.

        Retorna tuplas de (nome_da_seção, função_geradora) para cada
        plugin que define capability do tipo "custom_section".

        Returns:
            Lista de tuplas (section_name, generator_func).
        """
        sections: list[tuple[str, Callable[..., str]]] = []
        for plugin_def in self._plugins.values():
            for cap in plugin_def.capabilities:
                if cap.type == "custom_section" and plugin_def.section_generator:
                    sections.append((cap.name, plugin_def.section_generator))
        return sections

    def get_card_database_plugins(self) -> list[PluginDefinition]:
        """Retorna plugins que oferecem baralhos customizados.

        Returns:
            Lista de PluginDefinition com capability "card_database".
        """
        return self.get_plugins_by_capability("card_database")

    def get_analysis_rules_plugins(self) -> list[PluginDefinition]:
        """Retorna plugins que oferecem regras de análise.

        Returns:
            Lista de PluginDefinition com capability "analysis_rules".
        """
        return self.get_plugins_by_capability("analysis_rules")

    def get_load_errors(self) -> list[str]:
        """Retorna lista de erros de carregamento.

        Returns:
            Lista de mensagens de erro de plugins que falharam.
        """
        return list(self._load_errors)

    def reload(self, directory: Optional[str] = None) -> None:
        """Recarrega plugins do diretório especificado.

        Limpa o registro atual antes de recarregar.

        Args:
            directory: Caminho para diretório de plugins (opcional).
        """
        self._plugins.clear()
        self._plugin_cards.clear()
        self._load_errors.clear()
        self._loader = PluginLoader(safe_mode=self._safe_mode)
        self.load_plugins(directory)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    @property
    def plugins_dir(self) -> str:
        """Retorna o diretório de plugins configurado.

        Returns:
            Caminho do diretório de plugins.
        """
        return self._plugins_dir

    @property
    def plugin_count(self) -> int:
        """Retorna o número de plugins carregados.

        Returns:
            Contagem de plugins no registro.
        """
        return len(self._plugins)

    @property
    def cards_count(self) -> int:
        """Retorna o número de cartas de plugins.

        Returns:
            Contagem de cartas agregadas de plugins.
        """
        return len(self._plugin_cards)

    def _expand_path(self, path: str) -> Path:
        """Expande caminhos com ~ e resolve path absoluto.

        Args:
            path: Caminho a ser expandido.

        Returns:
            Path resolvido.
        """
        expanded = Path(path).expanduser()
        return expanded.resolve()

    def _get_expanded_plugins_dir(self) -> str:
        """Retorna diretório de plugins com caminho expandido.

        Returns:
            Caminho expandido do diretório de plugins.
        """
        return str(self._expand_path(self._plugins_dir))


# ----------------------------------------------------------------------
# Funções de conveniência (standalone)
# ----------------------------------------------------------------------


def get_plugin_manager(
    plugins_dir: Optional[str] = None,
) -> PluginManager:
    """Retorna uma instância do PluginManager.

    Função de conveniência para obter um gerenciador de plugins
    configurado e pronto para uso.

    Args:
        plugins_dir: Caminho para diretório de plugins (opcional).

    Returns:
        PluginManager configurado.
    """
    manager = PluginManager(plugins_dir=plugins_dir)
    manager.load_plugins()
    return manager


def list_available_plugins() -> list[str]:
    """Lista nomes dos plugins disponíveis no diretório padrão.

    Returns:
        Lista de nomes de plugins.
    """
    manager = get_plugin_manager()
    return [p.name for p in manager.get_plugins()]
