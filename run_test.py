import sys
sys.path.insert(0, '/home/skynet/ramires/ramires/.auto-claude/worktrees/tasks/027-guided-reflection-milestone-prompts')
from src.history_db import HistoryDB
db = HistoryDB()
sessions = db.list_sessions()
print('list OK:', len(sessions))