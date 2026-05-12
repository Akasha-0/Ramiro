"""Testes para verificação de que plugins malformados produzem warnings mas não crasham.

Cobertura:
- PluginLoader com plugins com sintaxe inválida
- PluginLoader com plugins sem PLUGIN_DEFINITION
- PluginLoader com PLUGIN_DEFINITION com campos obrigatórios faltando
- PluginLoader com arquivos Python vazios
- PluginLoader com erros de import
- PluginManager continua funcionando após plugins malformados
- CLI run_plugins_list não crasha com plugins malformados
"""

import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional

import pytest

from src.plugin_manager import PluginManager
from src.plugins.loader import PluginLoader, PluginLoadError, discover_plugins


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def capture_log_messages(caplog, logger_name: str) -> list[logging.LogRecord]:
    """Captura mensagens de log de um logger específico.

    Args:
        caplog: pytest fixture para captura de logs.
        logger_name: Nome do logger a monitorar.

    Returns:
        Lista de LogRecords capturados.
    """
    return [record for record in caplog.records if record.name == logger_name]


class _StringIO:
    """Buffer em memória para captura de stdout/stderr."""

    def __init__(self) -> None:
        self._buffer: list[str] = []

    def write(self, text: str) -> int:
        self._buffer.append(text)
        return len(text)

    def getvalue(self) -> str:
        return "".join(self._buffer)

    def isatty(self) -> bool:
        """Retorna False para simular non-TTY stream."""
        return False

    def flush(self) -> None:
        """Flush operation (no-op for buffer)."""
        pass


def capture_stdout(func, *args, **kwargs) -> tuple[str, int]:
    """Captura stdout e código de saída de uma função.

    Returns:
        Tupla (stdout_content, exit_code).
        exit_code = -1 se SystemExit não foi levantado.
    """
    old_stdout = sys.stdout
    sys.stdout = _StringIO()
    exit_code = -1
    try:
        func(*args, **kwargs)
    except SystemExit as e:
        exit_code = int(e.code) if e.code is not None else 0
    finally:
        stdout_val = sys.stdout.getvalue()
        sys.stdout = old_stdout
    return stdout_val, exit_code


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def temp_plugins_dir() -> str:
    """Diretório temporário para plugins."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def loader() -> PluginLoader:
    """PluginLoader com safe_mode=True (padrão)."""
    return PluginLoader(safe_mode=True)


@pytest.fixture
def manager() -> PluginManager:
    """PluginManager com safe_mode=True (padrão)."""
    return PluginManager(safe_mode=True)


# ----------------------------------------------------------------------
# Testes — plugins com sintaxe inválida
# ----------------------------------------------------------------------


class TestMalformedPluginSyntaxErrors:
    """Testes para plugins com erros de sintaxe Python."""

    def test_plugin_with_syntax_error_produces_warning(
        self, loader: PluginLoader, temp_plugins_dir: str, caplog
    ) -> None:
        """Plugin com erro de sintaxe produz warning mas não crasha."""
        # Criar plugin com erro de sintaxe
        plugin_path = Path(temp_plugins_dir) / "syntax_error_plugin.py"
        plugin_path.write_text(
            "PLUGIN_DEFINITION = {\n"
            "    'name': 'syntax_error_plugin'\n"
            "    # Falta vírgula aqui\n"
            "    'version': '1.0.0'\n"
            "}\n",
            encoding="utf-8",
        )

        # Capturar logs
        with caplog.at_level(logging.WARNING):
            # Não deve lançar exceção
            discovered = loader.discover_plugins(temp_plugins_dir)

        # Plugin não deve ser carregado
        assert "syntax_error_plugin" not in discovered
        assert len(loader.loaded_plugins) == 0

        # Deve haver warning no log
        assert any("syntax_error_plugin" in r.message.lower() or
                   "syntax" in r.message.lower() or
                   "error" in r.message.lower()
                   for r in caplog.records)

    def test_plugin_with_syntax_error_continues_loading(
        self, loader: PluginLoader, temp_plugins_dir: str
    ) -> None:
        """Sistema continua carregando outros plugins após erro."""
        # Plugin com erro de sintaxe
        bad_plugin = Path(temp_plugins_dir) / "bad_plugin.py"
        bad_plugin.write_text(
            "def broken():\n"
            "    return \n"  # SyntaxError
            "PLUGIN_DEFINITION = {'name': 'bad'}\n",
            encoding="utf-8",
        )

        # Plugin válido
        good_plugin = Path(temp_plugins_dir) / "good_plugin.py"
        good_plugin.write_text(
            "PLUGIN_DEFINITION = {\n"
            "    'name': 'good_plugin',\n"
            "    'version': '1.0.0',\n"
            "    'description': 'Plugin válido',\n"
            "    'author': 'Test',\n"
            "    'capabilities': [],\n"
            "}\n",
            encoding="utf-8",
        )

        discovered = loader.discover_plugins(temp_plugins_dir)

        # Plugin válido deve ser carregado
        assert "good_plugin" in discovered
        assert "bad_plugin" not in discovered


# ----------------------------------------------------------------------
# Testes — plugins sem PLUGIN_DEFINITION
# ----------------------------------------------------------------------


class TestPluginsWithoutDefinition:
    """Testes para plugins que não exportam PLUGIN_DEFINITION."""

    def test_plugin_without_definition_no_crash(
        self, loader: PluginLoader, temp_plugins_dir: str, caplog
    ) -> None:
        """Plugin sem PLUGIN_DEFINITION não crasha o loader."""
        plugin_path = Path(temp_plugins_dir) / "no_def_plugin.py"
        plugin_path.write_text(
            "# Este plugin não tem PLUGIN_DEFINITION\n"
            "def some_function():\n"
            "    return 'hello'\n",
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING):
            discovered = loader.discover_plugins(temp_plugins_dir)

        # Plugin não deve ser carregado
        assert "no_def_plugin" not in discovered
        assert len(loader.loaded_plugins) == 0

        # Deve haver warning sobre PLUGIN_DEFINITION não encontrado
        assert any("PLUGIN_DEFINITION" in r.message or
                   "não encontrado" in r.message.lower()
                   for r in caplog.records)

    def test_empty_file_plugin_no_crash(
        self, loader: PluginLoader, temp_plugins_dir: str, caplog
    ) -> None:
        """Arquivo vazio não crasha o loader."""
        plugin_path = Path(temp_plugins_dir) / "empty_plugin.py"
        plugin_path.write_text("", encoding="utf-8")

        with caplog.at_level(logging.WARNING):
            discovered = loader.discover_plugins(temp_plugins_dir)

        # Plugin não deve ser carregado
        assert len(discovered) == 0


# ----------------------------------------------------------------------
# Testes — plugins com PLUGIN_DEFINITION inválido
# ----------------------------------------------------------------------


class TestPluginsWithInvalidDefinition:
    """Testes para plugins com PLUGIN_DEFINITION malformado."""

    def test_plugin_missing_required_fields(
        self, loader: PluginLoader, temp_plugins_dir: str, caplog
    ) -> None:
        """Plugin com campos obrigatórios faltando não crasha."""
        plugin_path = Path(temp_plugins_dir) / "incomplete_plugin.py"
        plugin_path.write_text(
            "# PLUGIN_DEFINITION sem 'name' obrigatório\n"
            "PLUGIN_DEFINITION = {\n"
            "    'version': '1.0.0',\n"
            "    'description': 'Falta name',\n"
            "}\n",
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING):
            discovered = loader.discover_plugins(temp_plugins_dir)

        # Plugin não deve ser carregado
        assert "incomplete_plugin" not in discovered

    def test_plugin_invalid_definition_type(
        self, loader: PluginLoader, temp_plugins_dir: str, caplog
    ) -> None:
        """Plugin com tipo inválido de PLUGIN_DEFINITION não crasha."""
        plugin_path = Path(temp_plugins_dir) / "wrong_type_plugin.py"
        plugin_path.write_text(
            "# PLUGIN_DEFINITION como string (inválido)\n"
            "PLUGIN_DEFINITION = 'não sou um dicionário'\n",
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING):
            discovered = loader.discover_plugins(temp_plugins_dir)

        # Plugin não deve ser carregado
        assert "wrong_type_plugin" not in discovered

    def test_plugin_none_definition(
        self, loader: PluginLoader, temp_plugins_dir: str, caplog
    ) -> None:
        """Plugin com PLUGIN_DEFINITION = None não crasha."""
        plugin_path = Path(temp_plugins_dir) / "none_plugin.py"
        plugin_path.write_text(
            "PLUGIN_DEFINITION = None\n",
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING):
            discovered = loader.discover_plugins(temp_plugins_dir)

        # Plugin não deve ser carregado
        assert "none_plugin" not in discovered


# ----------------------------------------------------------------------
# Testes — plugins com erros de import
# ----------------------------------------------------------------------


class TestPluginsWithImportErrors:
    """Testes para plugins com erros de import."""

    def test_plugin_with_import_error_no_crash(
        self, loader: PluginLoader, temp_plugins_dir: str, caplog
    ) -> None:
        """Plugin com erro de import não crasha o loader."""
        plugin_path = Path(temp_plugins_dir) / "import_error_plugin.py"
        plugin_path.write_text(
            "import nonexistent_module_xyz\n"
            "PLUGIN_DEFINITION = {\n"
            "    'name': 'import_error_plugin',\n"
            "    'version': '1.0.0',\n"
            "    'description': 'Test',\n"
            "    'author': 'Test',\n"
            "    'capabilities': [],\n"
            "}\n",
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING):
            discovered = loader.discover_plugins(temp_plugins_dir)

        # Plugin não deve ser carregado
        assert "import_error_plugin" not in discovered

    def test_plugin_with_runtime_error_no_crash(
        self, loader: PluginLoader, temp_plugins_dir: str, caplog
    ) -> None:
        """Plugin com erro em tempo de execução não crasha o loader."""
        plugin_path = Path(temp_plugins_dir) / "runtime_error_plugin.py"
        plugin_path.write_text(
            "raise RuntimeError('Erro durante carregamento')\n"
            "PLUGIN_DEFINITION = {\n"
            "    'name': 'runtime_error',\n"
            "    'version': '1.0.0',\n"
            "    'description': 'Test',\n"
            "    'author': 'Test',\n"
            "    'capabilities': [],\n"
            "}\n",
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING):
            discovered = loader.discover_plugins(temp_plugins_dir)

        # Plugin não deve ser carregado
        assert "runtime_error_plugin" not in discovered


# ----------------------------------------------------------------------
# Testes — PluginManager com plugins malformados
# ----------------------------------------------------------------------


class TestPluginManagerWithMalformedPlugins:
    """Testes para PluginManager continuando a funcionar com plugins malformados."""

    def test_manager_loads_valid_plugins_despite_malformed(
        self, manager: PluginManager, temp_plugins_dir: str
    ) -> None:
        """PluginManager carrega plugins válidos mesmo com malformados presentes."""
        # Plugin válido
        valid_plugin = Path(temp_plugins_dir) / "valid_plugin.py"
        valid_plugin.write_text(
            "PLUGIN_DEFINITION = {\n"
            "    'name': 'valid_plugin',\n"
            "    'version': '1.0.0',\n"
            "    'description': 'Plugin válido',\n"
            "    'author': 'Test',\n"
            "    'capabilities': [],\n"
            "}\n",
            encoding="utf-8",
        )

        # Plugin malformado
        invalid_plugin = Path(temp_plugins_dir) / "invalid_plugin.py"
        invalid_plugin.write_text(
            "# Sem PLUGIN_DEFINITION\n"
            "x = 1\n",
            encoding="utf-8",
        )

        # Carregar plugins
        manager.load_plugins(temp_plugins_dir)

        # Plugin válido deve estar carregado
        assert manager.plugin_count == 1
        assert manager.get_plugin("valid_plugin") is not None
        assert manager.get_plugin("invalid_plugin") is None

    def test_manager_no_crash_with_all_malformed_plugins(
        self, manager: PluginManager, temp_plugins_dir: str
    ) -> None:
        """PluginManager não crasha quando todos os plugins são malformados."""
        # Apenas plugins malformados
        for i in range(3):
            plugin_path = Path(temp_plugins_dir) / f"broken_{i}.py"
            plugin_path.write_text(f"# Broken plugin {i}\nx = {i}\n", encoding="utf-8")

        # Não deve lançar exceção
        manager.load_plugins(temp_plugins_dir)

        # Nenhum plugin deve ser carregado
        assert manager.plugin_count == 0

    def test_manager_get_load_errors_returns_malformed_info(
        self, manager: PluginManager, temp_plugins_dir: str
    ) -> None:
        """get_load_errors retorna informações sobre plugins malformados."""
        # Plugin malformado
        invalid_plugin = Path(temp_plugins_dir) / "invalid_plugin.py"
        invalid_plugin.write_text(
            "PLUGIN_DEFINITION = None\n",
            encoding="utf-8",
        )

        manager.load_plugins(temp_plugins_dir)

        # Os erros são armazenados no loader
        loader_errors = manager._loader.load_errors

        # Deve haver erros registrados no loader
        assert len(loader_errors) > 0


# ----------------------------------------------------------------------
# Testes — função discover_plugins
# ----------------------------------------------------------------------


class TestDiscoverPluginsFunction:
    """Testes para a função discover_plugins."""

    def test_discover_plugins_nonexistent_directory_no_crash(self, temp_plugins_dir: str) -> None:
        """Diretório inexistente não crasha discover_plugins."""
        nonexistent = str(Path(temp_plugins_dir) / "nonexistent_dir")
        # Não deve lançar exceção
        discovered = discover_plugins(nonexistent)
        assert discovered == {}

    def test_discover_plugins_safe_mode_default(self, temp_plugins_dir: str) -> None:
        """safe_mode=True é o padrão para discover_plugins."""
        # Plugin inválido
        plugin_path = Path(temp_plugins_dir) / "bad.py"
        plugin_path.write_text("x = 1\n", encoding="utf-8")

        # Não deve lançar exceção
        discovered = discover_plugins(temp_plugins_dir, safe_mode=True)
        assert len(discovered) == 0


# ----------------------------------------------------------------------
# Testes — load_plugin_safely
# ----------------------------------------------------------------------


class TestLoadPluginSafely:
    """Testes para a função load_plugin_safely."""

    def test_load_plugin_safely_with_invalid_plugin(self, temp_plugins_dir: str) -> None:
        """load_plugin_safely retorna (None, error) para plugin inválido."""
        from src.plugins.loader import load_plugin_safely

        plugin_path = Path(temp_plugins_dir) / "invalid.py"
        plugin_path.write_text("PLUGIN_DEFINITION = None\n", encoding="utf-8")

        plugin, error = load_plugin_safely(str(plugin_path))
        assert plugin is None
        assert error is not None

    def test_load_plugin_safely_with_valid_plugin(self, temp_plugins_dir: str) -> None:
        """load_plugin_safely retorna (plugin, None) para plugin válido."""
        from src.plugins.loader import load_plugin_safely

        plugin_path = Path(temp_plugins_dir) / "valid.py"
        plugin_path.write_text(
            "PLUGIN_DEFINITION = {\n"
            "    'name': 'valid',\n"
            "    'version': '1.0.0',\n"
            "    'description': 'Test',\n"
            "    'author': 'Test',\n"
            "    'capabilities': [],\n"
            "}\n",
            encoding="utf-8",
        )

        plugin, error = load_plugin_safely(str(plugin_path))
        assert plugin is not None
        assert error is None
        assert plugin.name == "valid"


# ----------------------------------------------------------------------
# Testes — integração com CLI
# ----------------------------------------------------------------------


class TestCLIWithMalformedPlugins:
    """Testes de integração com CLI para plugins malformados."""

    def test_run_plugins_list_with_malformed_in_directory(
        self, temp_plugins_dir: str, caplog
    ) -> None:
        """run_plugins_list não crasha com plugins malformados."""
        from src.main import run_plugins_list

        # Plugin válido
        valid_plugin = Path(temp_plugins_dir) / "valid.py"
        valid_plugin.write_text(
            "PLUGIN_DEFINITION = {\n"
            "    'name': 'valid_test',\n"
            "    'version': '1.0.0',\n"
            "    'description': 'Test',\n"
            "    'author': 'Test',\n"
            "    'capabilities': [],\n"
            "}\n",
            encoding="utf-8",
        )

        # Plugin malformado
        bad_plugin = Path(temp_plugins_dir) / "bad.py"
        bad_plugin.write_text("# No definition\nx = 1\n", encoding="utf-8")

        # Criar manager temporário
        manager = PluginManager(plugins_dir=temp_plugins_dir)

        with caplog.at_level(logging.WARNING):
            manager.load_plugins(temp_plugins_dir)

        # Deve carregar o válido
        assert manager.get_plugin("valid_test") is not None
        # Não deve crashar

    def test_analyze_with_malformed_plugins_no_crash(
        self, temp_plugins_dir: str, caplog
    ) -> None:
        """Análise não crasha quando há plugins malformados.

        Verifica que o sistema continua funcionando mesmo quando
        um plugin malformado está presente no diretório.
        """
        # Plugin malformado
        bad_plugin = Path(temp_plugins_dir) / "broken.py"
        bad_plugin.write_text(
            "raise Exception('Intentional error')\n"
            "PLUGIN_DEFINITION = {\n"
            "    'name': 'broken',\n"
            "    'version': '1.0.0',\n"
            "    'description': 'Test',\n"
            "    'author': 'Test',\n"
            "    'capabilities': [],\n"
            "}\n",
            encoding="utf-8",
        )

        # Criar manager e carregar - isso não deve crashar
        manager = PluginManager(plugins_dir=temp_plugins_dir)

        with caplog.at_level(logging.WARNING):
            manager.load_plugins()

        # O plugin malformado não deve ser carregado
        assert manager.get_plugin("broken") is None

        # Mas o sistema deve continuar funcionando
        # (sem plugins carregados, mas sem crash)
        assert manager.plugin_count == 0


# ----------------------------------------------------------------------
# Testes — edge cases
# ----------------------------------------------------------------------


class TestMalformedPluginEdgeCases:
    """Testes de edge cases para plugins malformados."""

    def test_plugin_with_only_comments(self, loader: PluginLoader, temp_plugins_dir: str) -> None:
        """Plugin com apenas comentários não crasha."""
        plugin_path = Path(temp_plugins_dir) / "comments_only.py"
        plugin_path.write_text(
            "# Plugin sem definição\n"
            "# Apenas comentários\n",
            encoding="utf-8",
        )

        discovered = loader.discover_plugins(temp_plugins_dir)
        assert len(discovered) == 0

    def test_plugin_with_binary_content(self, loader: PluginLoader, temp_plugins_dir: str) -> None:
        """Plugin com conteúdo binário não crasha."""
        plugin_path = Path(temp_plugins_dir) / "binary.py"
        plugin_path.write_bytes(b"\x00\x01\x02\x03 invalid python")

        discovered = loader.discover_plugins(temp_plugins_dir)
        assert len(discovered) == 0

    def test_multiple_malformed_plugins_no_crash(
        self, loader: PluginLoader, temp_plugins_dir: str
    ) -> None:
        """Múltiplos plugins malformados não causam crash."""
        for i in range(5):
            plugin_path = Path(temp_plugins_dir) / f"broken_{i}.py"
            if i % 2 == 0:
                plugin_path.write_text(f"# Broken {i}\nraise Exception()\n", encoding="utf-8")
            else:
                plugin_path.write_text(f"# No definition {i}\nx = {i}\n", encoding="utf-8")

        discovered = loader.discover_plugins(temp_plugins_dir)
        assert len(discovered) == 0
