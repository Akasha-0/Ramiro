#!/opt/Auto-Claude/resources/python/bin/python3
"""Run benchmark CLI with CI mode - simple version."""
import sys
sys.path.insert(0, '.')
from src.clareza.benchmark.cli import cli
sys.argv = ['benchmark', '--ci']
try:
    cli()
except SystemExit:
    pass