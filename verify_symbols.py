#!/usr/bin/env python3
"""Test script for symbols.py plugin registry functions."""

import sys
import os

# Add project root to path
project_root = '/home/skynet/ramires/ramires/.auto-claude/worktrees/tasks/028-plugin-architecture-for-card-databases-and-analysi'
sys.path.insert(0, project_root)
os.chdir(project_root)

try:
    # Import the functions we need to verify
    from src.symbols import register_plugin_cards, get_all_cards_including_plugins, plugin_card_registry

    # Verify they are callable/exist
    assert callable(register_plugin_cards), "register_plugin_cards should be callable"
    assert callable(get_all_cards_including_plugins), "get_all_cards_including_plugins should be callable"
    assert isinstance(plugin_card_registry, dict), "plugin_card_registry should be a dict"

    # Test basic functionality
    test_cards = [
        {"name": "Test Card", "keywords": ["test"], "theme": "test"}
    ]
    count = register_plugin_cards(test_cards, "test_plugin")
    assert count == 1, f"Expected 1 card registered, got {count}"

    all_cards = get_all_cards_including_plugins()
    assert len(all_cards) > 36, f"Expected more than 36 cards, got {len(all_cards)}"

    # Write success output to a file we can read
    with open(os.path.join(project_root, 'test_result.txt'), 'w') as f:
        f.write("OK\n")

    print("OK")

except Exception as e:
    # Write error output to a file
    import traceback
    error_msg = f"Error: {type(e).__name__}: {e}\n"
    with open(os.path.join(project_root, 'test_result.txt'), 'w') as f:
        f.write(error_msg)
        f.write(traceback.format_exc())

    print(error_msg)
    traceback.print_exc()