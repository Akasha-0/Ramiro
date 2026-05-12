#!/usr/bin/env python3
"""Test script for list_sessions verification."""
from src.history_db import HistoryDB

db = HistoryDB()
sessions = db.list_sessions()
print('list OK:', len(sessions))

# Test with tag filter
sessions_filtered = db.list_sessions(tag="trabalho")
print('list filtered OK:', len(sessions_filtered))

print("All tests passed!")