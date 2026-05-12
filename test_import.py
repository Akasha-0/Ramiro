import sys
sys.path.insert(0, '/home/skynet/ramires/ramires/.auto-claude/worktrees/tasks/030-performance-benchmarks-and-analysis-engine-profili')
from benchmarks.regression import RegressionChecker
print("RegressionChecker created with threshold:", RegressionChecker().threshold)
print("PASS")