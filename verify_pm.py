#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

errors = []

try:
    from src.plugin_manager import PluginManager
    pm = PluginManager()
    print('OK')
except ImportError as e:
    errors.append(f'ImportError: {e}')
except Exception as e:
    errors.append(f'Exception: {e}')

if errors:
    for err in errors:
        print(err, file=sys.stderr)
    sys.exit(1)
