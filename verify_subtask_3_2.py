#!/usr/bin/env python3
"""Verification script for subtask-3-2 - get_plugins() method."""
import sys
sys.path.insert(0, '.')

from src.plugin_manager import PluginManager

def verify():
    """Run verification checks for get_plugins()."""
    print("=== Subtask 3-2 Verification: get_plugins() ===")
    print()

    # Step 1: Create PluginManager
    print("1. Creating PluginManager instance...")
    pm = PluginManager()
    print(f"   PluginManager created successfully")

    # Step 2: Call get_plugins()
    print()
    print("2. Calling get_plugins()...")
    plugins = pm.get_plugins()
    print(f"   Return type: {type(plugins)}")
    print(f"   Is list: {isinstance(plugins, list)}")

    # Verification
    print()
    print("=== VERIFICATION RESULT ===")
    if isinstance(plugins, list):
        print("✓ PASSED: get_plugins() returns a list")
        return True
    else:
        print(f"✗ FAILED: Expected list, got {type(plugins)}")
        return False

if __name__ == '__main__':
    success = verify()
    sys.exit(0 if success else 1)