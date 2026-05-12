#!/opt/Auto-Claude/resources/python/bin/python3
"""Simple CI mode verification - minimal."""
import sys
import os

# Change to worktree directory
worktree = '/home/skynet/ramires/ramires/.auto-claude/worktrees/tasks/030-performance-benchmarks-and-analysis-engine-profili'
os.chdir(worktree)
sys.path.insert(0, worktree)

# Step 1: Verify benchmark modules exist
import benchmarks.runner
import benchmarks.regression
import benchmarks.baseline
print("OK - Benchmark modules importable")

# Step 2: Verify RegressionChecker class exists
rc = benchmarks.regression.RegressionChecker()
print(f"OK - RegressionChecker threshold={rc.threshold}")

# Step 3: Verify baseline can be loaded
bc = benchmarks.baseline.load_baseline()
print(f"OK - Baseline has {len(bc.baselines)} entries")

# Step 4: Create a test result and check it against baseline
br = benchmarks.runner.BenchmarkResult(
    name="input_processor.text",
    iterations=5,
    total_time=0.001,
    mean=0.0002,
    median=0.0002,
    std_dev=0.00001,
    min_time=0.0001,
    max_time=0.0003,
    ops_per_second=5000,
)
baseline = bc.get_baseline("input_processor.text")
if baseline:
    rr = rc.check_single(br, baseline)
    print(f"OK - Regression check: {rr.regression_percent:.2f}% (is_regression={rr.is_regression})")
else:
    print("WARN - No baseline for input_processor.text")

# Step 5: Verify get_exit_code method
rr_all = benchmarks.regression.RegressionReport(suite_name="test", total_benchmarks=1)
print(f"OK - get_exit_code(clean)={rc.get_exit_code(rr_all)}")

# Final result
rr_with_reg = benchmarks.regression.RegressionReport(suite_name="test", total_benchmarks=1, regressions_found=1, has_regressions=True)
print(f"OK - get_exit_code(regression)={rc.get_exit_code(rr_with_reg)}")

print("PASS")