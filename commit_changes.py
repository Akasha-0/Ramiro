#!/usr/bin/env python3
"""Commit script for subtask-1-5"""
import subprocess
import os

os.chdir('/home/skynet/ramires/ramires/.auto-claude/worktrees/tasks/027-guided-reflection-milestone-prompts')

# Stage the file
subprocess.run(['git', 'add', 'src/history_db.py'])

# Commit
result = subprocess.run([
    'git', 'commit', '-m', '''auto-claude: subtask-1-5 - Implement add_annotation() to attach reflection re

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>'''
], capture_output=True, text=True)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)