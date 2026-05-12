#!/opt/Auto-Claude/resources/python/bin/python3
"""Run benchmark CLI with CI mode."""
import sys
sys.path.insert(0, '/home/skynet/ramires/ramires/.auto-claude/worktrees/tasks/030-performance-benchmarks-and-analysis-engine-profili')
from src.clareza.benchmark.cli import cli
sys.argv = ['benchmark', '--ci']
try:
    cli()
except SystemExit:
    pass