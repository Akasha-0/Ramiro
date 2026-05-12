import sys
sys.path.insert(0, '/home/skynet/ramires/ramires/.auto-claude/worktrees/tasks/028-plugin-architecture-for-card-databases-and-analysi')

try:
    from src.symbols import register_plugin_cards, get_all_cards_including_plugins
    print('OK')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()