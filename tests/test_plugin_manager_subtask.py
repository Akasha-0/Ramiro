"""Tests for src.plugin_manager module."""
import pytest
from src.plugin_manager import PluginManager, get_plugin_manager


def test_plugin_manager_import():
    """Test that PluginManager can be imported."""
    from src.plugin_manager import PluginManager
    assert PluginManager is not None


def test_plugin_manager_instantiation():
    """Test that PluginManager can be instantiated."""
    pm = PluginManager()
    assert pm is not None


def test_plugin_manager_initial_state():
    """Test PluginManager initial state."""
    pm = PluginManager()
    assert pm.plugin_count == 0
    assert pm.cards_count == 0


def test_plugin_manager_get_plugins():
    """Test get_plugins returns list."""
    pm = PluginManager()
    plugins = pm.get_plugins()
    assert isinstance(plugins, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
