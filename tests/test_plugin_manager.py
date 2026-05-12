"""Testes unitários para src/plugin_manager.py.

Cobertura:
- PluginManager.__init__() — inicialização, atributos padrão
- PluginManager.load_plugins() — descoberta e carregamento de plugins
- PluginManager.get_plugins() — listagem de plugins carregados
- PluginManager.get_plugin() — busca por plugin específico
- PluginManager.get_plugins_by_capability() — filtros por capability
- PluginManager.get_extended_cards() — agregação de cartas de plugins
- PluginManager.get_extended_sections() — seções customizadas
- PluginManager.get_card_database_plugins() — plugins de baralho
- PluginManager.get_analysis_rules_plugins() — plugins de regras
- PluginManager.get_load_errors() — erros de carregamento
- PluginManager.reload() — recarregamento de plugins
- PluginManager.plugins_dir — propriedade do diretório
- PluginManager.plugin_count — propriedade de contagem de plugins
- PluginManager.cards_count — propriedade de contagem de cartas
- get_plugin_manager() — função de conveniência
- list_available_plugins() — listagem de plugins disponíveis
"""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

import pytest

from src.plugin_manager import (
    PluginManager,
    get_plugin_manager,
    list_available_plugins,
    DEFAULT_PLUGINS_DIR,
)
from src.plugins.types import PluginDefinition, PluginCapability
from src.plugins.loader import PluginLoadError, PluginDiscoveryError


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def manager() -> PluginManager:
    """PluginManager com safe_mode ativado."""
    return PluginManager(safe_mode=True)


@pytest.fixture
def manager_no_safe() -> PluginManager:
    """PluginManager com safe_mode desativado."""
    return PluginManager(safe_mode=False)


@pytest.fixture
def mock_plugin() -> PluginDefinition:
    """PluginDefinition de exemplo."""
    return PluginDefinition(
        name="test_plugin",
        version="1.0.0",
        description="Plugin de teste",
        author="Teste",
        capabilities=[
            PluginCapability(
                type="card_database",
                name="Baralho Teste",
                description="Um baralho de teste",
            )
        ],
        cards=[
            {"name": "Carta 1", "meaning": "Significado 1"},
            {"name": "Carta 2", "meaning": "Significado 2"},
        ],
    )


@pytest.fixture
def mock_plugin_with_analysis() -> PluginDefinition:
    """PluginDefinition com regras de análise."""
    return PluginDefinition(
        name="analysis_plugin",
        version="1.0.0",
        description="Plugin de análise",
        author="Teste",
        capabilities=[
            PluginCapability(
                type="analysis_rules",
                name="Regras Customizadas",
                description="Regras de análise",
            )
        ],
        analysis_rules={"theme_weights": {"trabalho": 2.0}},
    )


@pytest.fixture
def mock_plugin_with_section() -> PluginDefinition:
    """PluginDefinition com seção customizada."""
    def section_generator(data: Any) -> str:
        return "## Seção Custom\n\nConteúdo gerado."

    return PluginDefinition(
        name="section_plugin",
        version="1.0.0",
        description="Plugin com seção customizada",
        author="Teste",
        capabilities=[
            PluginCapability(
                type="custom_section",
                name="Minha Seção",
                description="Seção customizada",
            )
        ],
        section_generator=section_generator,
    )


@pytest.fixture
def temp_plugins_dir() -> str:
    """Diretório temporário para plugins."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ----------------------------------------------------------------------
# Testes — __init__()
# ----------------------------------------------------------------------


class TestPluginManagerInit:
    def test_default_plugins_dir(self) -> None:
        """Diretório padrão é ~/.clareza/plugins."""
        manager = PluginManager()
        assert manager.plugins_dir == DEFAULT_PLUGINS_DIR

    def test_custom_plugins_dir(self) -> None:
        """Diretório customizado é configurado corretamente."""
        custom_dir = "/custom/plugins/path"
        manager = PluginManager(plugins_dir=custom_dir)
        assert manager.plugins_dir == custom_dir

    def test_safe_mode_default_true(self) -> None:
        """safe_mode é True por padrão."""
        manager = PluginManager()
        # O loader interno deve ter safe_mode=True
        assert manager._safe_mode is True

    def test_safe_mode_explicit_false(self) -> None:
        """safe_mode pode ser configurado como False."""
        manager = PluginManager(safe_mode=False)
        assert manager._safe_mode is False

    def test_initial_plugin_count_zero(self) -> None:
        """Contagem inicial de plugins é zero."""
        manager = PluginManager()
        assert manager.plugin_count == 0

    def test_initial_cards_count_zero(self) -> None:
        """Contagem inicial de cartas é zero."""
        manager = PluginManager()
        assert manager.cards_count == 0

    def test_initial_load_errors_empty(self) -> None:
        """Lista inicial de erros é vazia."""
        manager = PluginManager()
        assert manager.get_load_errors() == []


# ----------------------------------------------------------------------
# Testes — load_plugins()
# ----------------------------------------------------------------------


class TestLoadPlugins:
    def test_load_plugins_with_empty_directory(self, manager: PluginManager, temp_plugins_dir: str) -> None:
        """Diretório vazio não carrega plugins."""
        manager.load_plugins(temp_plugins_dir)
        assert manager.plugin_count == 0

    def test_load_plugins_uses_default_dir(self, manager: PluginManager) -> None:
        """Sem argumento, usa diretório padrão."""
        with patch.object(manager, '_loader') as mock_loader:
            mock_loader.discover_plugins.return_value = {}
            manager.load_plugins()
            mock_loader.discover_plugins.assert_called_once_with(manager._plugins_dir)

    def test_load_plugins_with_custom_directory(self, manager: PluginManager, temp_plugins_dir: str) -> None:
        """Diretório customizado é usado quando especificado."""
        with patch.object(manager, '_loader') as mock_loader:
            mock_loader.discover_plugins.return_value = {}
            mock_loader.load_errors = []
            manager.load_plugins(temp_plugins_dir)
            mock_loader.discover_plugins.assert_called_once_with(temp_plugins_dir)

    def test_load_plugins_updates_registry(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Plugins descobertos são adicionados ao registro."""
        with patch.object(manager, '_loader') as mock_loader:
            mock_loader.discover_plugins.return_value = {"test_plugin": mock_plugin}
            mock_loader.load_errors = []
            manager.load_plugins()
            assert manager.plugin_count == 1
            assert manager.get_plugin("test_plugin") == mock_plugin

    def test_load_plugins_handles_discovery_error(self, manager: PluginManager) -> None:
        """PluginDiscoveryError é capturado em safe_mode."""
        with patch.object(manager, '_loader') as mock_loader:
            mock_loader.discover_plugins.side_effect = PluginDiscoveryError("/path", "erro")
            mock_loader.load_errors = []
            # Não deve levantar exceção
            manager.load_plugins()
            assert manager.plugin_count == 0

    def test_load_plugins_handles_load_error(self, manager: PluginManager) -> None:
        """PluginLoadError é capturado em safe_mode."""
        with patch.object(manager, '_loader') as mock_loader:
            mock_loader.discover_plugins.side_effect = PluginLoadError("plugin", "erro")
            mock_loader.load_errors = ["Plugin 'plugin' falhou: erro"]
            # Não deve levantar exceção
            manager.load_plugins()
            assert manager.plugin_count == 0


# ----------------------------------------------------------------------
# Testes — get_plugins()
# ----------------------------------------------------------------------


class TestGetPlugins:
    def test_get_plugins_empty(self, manager: PluginManager) -> None:
        """Retorna lista vazia quando não há plugins."""
        assert manager.get_plugins() == []

    def test_get_plugins_returns_list(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Retorna lista de PluginDefinition."""
        with patch.object(manager, '_plugins', {"test": mock_plugin}):
            plugins = manager.get_plugins()
            assert isinstance(plugins, list)
            assert len(plugins) == 1
            assert plugins[0] == mock_plugin


# ----------------------------------------------------------------------
# Testes — get_plugin()
# ----------------------------------------------------------------------


class TestGetPlugin:
    def test_get_plugin_existing(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Retorna plugin quando encontrado."""
        with patch.object(manager, '_plugins', {"test_plugin": mock_plugin}):
            result = manager.get_plugin("test_plugin")
            assert result == mock_plugin

    def test_get_plugin_nonexistent(self, manager: PluginManager) -> None:
        """Retorna None quando plugin não existe."""
        result = manager.get_plugin("inexistente")
        assert result is None


# ----------------------------------------------------------------------
# Testes — get_plugins_by_capability()
# ----------------------------------------------------------------------


class TestGetPluginsByCapability:
    def test_by_capability_card_database(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Filtra plugins por capability card_database."""
        with patch.object(manager, '_plugins', {"test": mock_plugin}):
            results = manager.get_plugins_by_capability("card_database")
            assert len(results) == 1
            assert results[0].name == "test_plugin"

    def test_by_capability_analysis_rules(self, manager: PluginManager, mock_plugin_with_analysis: PluginDefinition) -> None:
        """Filtra plugins por capability analysis_rules."""
        with patch.object(manager, '_plugins', {"analysis": mock_plugin_with_analysis}):
            results = manager.get_plugins_by_capability("analysis_rules")
            assert len(results) == 1
            assert results[0].name == "analysis_plugin"

    def test_by_capability_not_found(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Retorna lista vazia quando capability não existe."""
        with patch.object(manager, '_plugins', {"test": mock_plugin}):
            results = manager.get_plugins_by_capability("nonexistent_capability")
            assert results == []

    def test_by_capability_multiple_plugins(self, manager: PluginManager, mock_plugin: PluginDefinition, mock_plugin_with_analysis: PluginDefinition) -> None:
        """Retorna múltiplos plugins com mesma capability."""
        with patch.object(manager, '_plugins', {
            "test": mock_plugin,
            "analysis": mock_plugin_with_analysis
        }):
            # mock_plugin não tem analysis_rules
            results = manager.get_plugins_by_capability("card_database")
            assert len(results) == 1


# ----------------------------------------------------------------------
# Testes — get_extended_cards()
# ----------------------------------------------------------------------


class TestGetExtendedCards:
    def test_extended_cards_empty(self, manager: PluginManager) -> None:
        """Retorna dict vazio quando não há cartas."""
        assert manager.get_extended_cards() == {}

    def test_extended_cards_from_plugin(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Agrega cartas de plugins com prefixo único."""
        with patch.object(manager, '_plugin_cards', {
            "test_plugin:Carta 1": {"name": "Carta 1", "meaning": "Significado 1"},
            "test_plugin:Carta 2": {"name": "Carta 2", "meaning": "Significado 2"},
        }):
            cards = manager.get_extended_cards()
            assert len(cards) == 2
            assert "test_plugin:Carta 1" in cards
            assert "test_plugin:Carta 2" in cards

    def test_extended_cards_returns_copy(self, manager: PluginManager) -> None:
        """Retorna cópia do dict interno."""
        with patch.object(manager, '_plugin_cards', {"key": {"name": "Test"}}):
            cards = manager.get_extended_cards()
            cards["new_key"] = {}
            assert "new_key" not in manager._plugin_cards


# ----------------------------------------------------------------------
# Testes — get_extended_sections()
# ----------------------------------------------------------------------


class TestGetExtendedSections:
    def test_extended_sections_empty(self, manager: PluginManager) -> None:
        """Retorna lista vazia quando não há seções."""
        assert manager.get_extended_sections() == []

    def test_extended_sections_from_plugin(self, manager: PluginManager, mock_plugin_with_section: PluginDefinition) -> None:
        """Retorna tuplas de seções de plugins."""
        with patch.object(manager, '_plugins', {"section": mock_plugin_with_section}):
            sections = manager.get_extended_sections()
            assert len(sections) == 1
            name, generator = sections[0]
            assert name == "Minha Seção"
            assert callable(generator)

    def test_extended_sections_generator_callable(self, manager: PluginManager, mock_plugin_with_section: PluginDefinition) -> None:
        """Gerador de seção é callable."""
        with patch.object(manager, '_plugins', {"section": mock_plugin_with_section}):
            sections = manager.get_extended_sections()
            _, generator = sections[0]
            result = generator({})
            assert "Seção Custom" in result


# ----------------------------------------------------------------------
# Testes — get_card_database_plugins()
# ----------------------------------------------------------------------


class TestGetCardDatabasePlugins:
    def test_card_database_plugins(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Retorna plugins com capability card_database."""
        with patch.object(manager, '_plugins', {"test": mock_plugin}):
            results = manager.get_card_database_plugins()
            assert len(results) == 1
            assert results[0].name == "test_plugin"

    def test_card_database_plugins_empty(self, manager: PluginManager, mock_plugin_with_analysis: PluginDefinition) -> None:
        """Retorna lista vazia quando nenhum plugin tem baralho."""
        with patch.object(manager, '_plugins', {"analysis": mock_plugin_with_analysis}):
            results = manager.get_card_database_plugins()
            assert results == []


# ----------------------------------------------------------------------
# Testes — get_analysis_rules_plugins()
# ----------------------------------------------------------------------


class TestGetAnalysisRulesPlugins:
    def test_analysis_rules_plugins(self, manager: PluginManager, mock_plugin_with_analysis: PluginDefinition) -> None:
        """Retorna plugins com capability analysis_rules."""
        with patch.object(manager, '_plugins', {"analysis": mock_plugin_with_analysis}):
            results = manager.get_analysis_rules_plugins()
            assert len(results) == 1
            assert results[0].name == "analysis_plugin"

    def test_analysis_rules_plugins_empty(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Retorna lista vazia quando nenhum plugin tem regras."""
        with patch.object(manager, '_plugins', {"test": mock_plugin}):
            results = manager.get_analysis_rules_plugins()
            assert results == []


# ----------------------------------------------------------------------
# Testes — get_load_errors()
# ----------------------------------------------------------------------


class TestGetLoadErrors:
    def test_get_load_errors_empty(self, manager: PluginManager) -> None:
        """Retorna lista vazia quando não há erros."""
        assert manager.get_load_errors() == []

    def test_get_load_errors_returns_copy(self, manager: PluginManager) -> None:
        """Retorna cópia da lista de erros."""
        with patch.object(manager, '_load_errors', ["erro 1", "erro 2"]):
            errors = manager.get_load_errors()
            errors.append("erro 3")
            assert manager._load_errors == ["erro 1", "erro 2"]


# ----------------------------------------------------------------------
# Testes — reload()
# ----------------------------------------------------------------------


class TestReload:
    def test_reload_clears_plugins(self, manager: PluginManager) -> None:
        """reload() limpa plugins antes de recarregar."""
        with patch.object(manager, '_plugins', {"old": MagicMock()}):
            with patch.object(manager, '_plugin_cards', {"key": {}}):
                with patch.object(manager, '_load_errors', ["erro"]):
                    with patch.object(manager, '_loader') as mock_loader:
                        mock_loader.discover_plugins.return_value = {}
                        mock_loader.load_errors = []
                        manager.reload()
                        assert manager.plugin_count == 0

    def test_reload_uses_custom_directory(self, manager: PluginManager, temp_plugins_dir: str) -> None:
        """reload() pode usar diretório customizado."""
        with patch.object(manager, '_loader') as mock_loader:
            mock_loader.discover_plugins.return_value = {}
            mock_loader.load_errors = []
            manager.reload(temp_plugins_dir)
            mock_loader.discover_plugins.assert_called_with(temp_plugins_dir)


# ----------------------------------------------------------------------
# Testes — propriedades
# ----------------------------------------------------------------------


class TestProperties:
    def test_plugins_dir_property(self, manager: PluginManager) -> None:
        """plugins_dir retorna o diretório configurado."""
        custom_dir = "/custom/path"
        manager = PluginManager(plugins_dir=custom_dir)
        assert manager.plugins_dir == custom_dir

    def test_plugin_count_property(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """plugin_count retorna número de plugins."""
        with patch.object(manager, '_plugins', {"a": mock_plugin, "b": mock_plugin}):
            assert manager.plugin_count == 2

    def test_cards_count_property(self, manager: PluginManager) -> None:
        """cards_count retorna número de cartas."""
        with patch.object(manager, '_plugin_cards', {"a": {}, "b": {}, "c": {}}):
            assert manager.cards_count == 3


# ----------------------------------------------------------------------
# Testes — _collect_plugin_cards()
# ----------------------------------------------------------------------


class TestCollectPluginCards:
    def test_collect_cards_with_cards(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Coleta cartas de plugin com capability card_database."""
        manager._collect_plugin_cards(mock_plugin)
        assert manager.cards_count == 2
        assert "test_plugin:Carta 1" in manager._plugin_cards
        assert "test_plugin:Carta 2" in manager._plugin_cards

    def test_collect_cards_without_cards(self, manager: PluginManager, mock_plugin_with_analysis: PluginDefinition) -> None:
        """Não coleta cartas de plugin sem baralho."""
        manager._collect_plugin_cards(mock_plugin_with_analysis)
        assert manager.cards_count == 0

    def test_collect_cards_adds_plugin_source(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Cartas recebem atributo _plugin_source."""
        manager._collect_plugin_cards(mock_plugin)
        card = manager._plugin_cards["test_plugin:Carta 1"]
        assert card["_plugin_source"] == "test_plugin"

    def test_collect_cards_handles_invalid_format(self, manager: PluginManager) -> None:
        """Ignora cards sem formato válido (não dict ou sem name)."""
        plugin = PluginDefinition(
            name="bad_plugin",
            version="1.0.0",
            cards=[{"invalid": "no name"}, "string card", None],
        )
        manager._collect_plugin_cards(plugin)
        # Nenhuma carta deve ser adicionada
        assert manager.cards_count == 0


# ----------------------------------------------------------------------
# Testes — _update_registry()
# ----------------------------------------------------------------------


class TestUpdateRegistry:
    def test_update_registry_adds_plugins(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Adiciona plugins ao registro."""
        manager._update_registry({"test": mock_plugin})
        assert manager.plugin_count == 1
        assert manager.get_plugin("test") == mock_plugin

    def test_update_registry_collects_cards(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Chama _collect_plugin_cards para cada plugin."""
        with patch.object(manager, '_collect_plugin_cards') as mock_collect:
            manager._update_registry({"test": mock_plugin})
            mock_collect.assert_called_once_with(mock_plugin)

    def test_update_registry_accumulates_errors(self, manager: PluginManager, mock_plugin: PluginDefinition) -> None:
        """Acumula erros de carregamento."""
        manager._loader.load_errors = ["erro 1", "erro 2"]
        manager._update_registry({"test": mock_plugin})
        assert len(manager._load_errors) == 2


# ----------------------------------------------------------------------
# Testes — _expand_path()
# ----------------------------------------------------------------------


class TestExpandPath:
    def test_expand_path_with_tilde(self, manager: PluginManager) -> None:
        """Expande ~ para home directory."""
        result = manager._expand_path("~/plugins")
        assert result != Path("~/plugins")
        assert "~" not in str(result)

    def test_expand_path_returns_resolved(self, manager: PluginManager) -> None:
        """Retorna path absoluto resolvido."""
        result = manager._expand_path(".")
        assert result.is_absolute()


# ----------------------------------------------------------------------
# Testes — funções de conveniência
# ----------------------------------------------------------------------


class TestConvenienceFunctions:
    def test_get_plugin_manager_creates_instance(self) -> None:
        """get_plugin_manager() retorna PluginManager."""
        with patch("src.plugin_manager.PluginManager") as MockManager:
            mock_instance = MagicMock()
            MockManager.return_value = mock_instance
            mock_instance.load_plugins.return_value = None
            result = get_plugin_manager()
            MockManager.assert_called_once_with(plugins_dir=None)
            mock_instance.load_plugins.assert_called_once()

    def test_list_available_plugins_returns_names(self) -> None:
        """list_available_plugins() retorna lista de nomes."""
        with patch("src.plugin_manager.get_plugin_manager") as mock_get:
            mock_manager = MagicMock()
            mock_manager.get_plugins.return_value = [
                PluginDefinition(name="plugin_a", version="1.0"),
                PluginDefinition(name="plugin_b", version="2.0"),
            ]
            mock_get.return_value = mock_manager
            result = list_available_plugins()
            assert result == ["plugin_a", "plugin_b"]
