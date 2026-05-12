#!/opt/Auto-Claude/resources/python/bin/python3
"""Verify CI mode with regression detection."""
import sys
import os
sys.path.insert(0, '/home/skynet/ramires/ramires/.auto-claude/worktrees/tasks/030-performance-benchmarks-and-analysis-engine-profili')

# Verify we can import all modules first
try:
    from src.clareza.benchmark.cli import cli
    from benchmarks.runner import BenchmarkResult, BenchmarkSuiteResult
    from benchmarks.regression import RegressionChecker, RegressionReport
    from benchmarks.baseline import BaselineManager, load_baseline
    print("OK - All imports successful")
except ImportError as e:
    print(f"FAIL - Import error: {e}")
    sys.exit(1)

# Verify baseline exists
try:
    from benchmarks.baseline import load_baseline
    baselines = load_baseline()
    if baselines and len(baselines) > 0:
        print(f"OK - Baseline loaded: {len(baselines)} entries")
    else:
        print("FAIL - Baseline empty or not found")
        sys.exit(1)
except Exception as e:
    print(f"FAIL - Baseline error: {e}")
    sys.exit(1)

# Verify RegressionChecker can be instantiated
try:
    checker = RegressionChecker()
    print(f"OK - RegressionChecker created with threshold={checker.threshold}")
except Exception as e:
    print(f"FAIL - RegressionChecker error: {e}")
    sys.exit(1)

# Verify RegressionReport.to_dict() method exists
try:
    report = RegressionReport(
        suite_name="test",
        total_benchmarks=0,
        regressions_found=0,
    )
    d = report.to_dict()
    summary = report.get_summary()
    print(f"OK - RegressionReport methods work: {summary}")
except Exception as e:
    print(f"FAIL - RegressionReport error: {e}")
    sys.exit(1)

# Verify RegressionChecker.format_report() method exists
try:
    from benchmarks.runner import BenchmarkResult
    result = BenchmarkResult(
        name="test",
        iterations=5,
        total_time=0.001,
        mean=0.0002,
        median=0.0002,
        std_dev=0.00001,
        min_time=0.0001,
        max_time=0.0003,
        ops_per_second=5000,
    )
    report = checker.check_single(result, baselines.get_baseline("test"))
    output = checker.format_report(RegressionReport(
        suite_name="test",
        total_benchmarks=1,
        regressions_found=0,
        regression_results=[report] if report else [],
    ), verbose=True)
    print(f"OK - format_report works")
except Exception as e:
    print(f"FAIL - format_report error: {e}")
    sys.exit(1)

print("OK - PASS - All CI mode components verified")