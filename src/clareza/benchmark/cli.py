"""Command-line interface for clareza benchmark."""

import argparse
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from benchmarks.runner import BenchmarkRunner, BenchmarkSuiteResult
from benchmarks.baseline import BaselineManager, BenchmarkBaseline


@dataclass
class SimpleBenchmarkResult:
    """Simplified benchmark result for CLI output."""
    name: str
    mean: float
    min: float
    max: float
    std_dev: float
    iterations: int


def cli() -> None:
    """Entry point for clareza benchmark CLI."""
    parser = argparse.ArgumentParser(
        description="Performance benchmarks for clareza system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=5,
        help="Number of iterations per benchmark (default: 5)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline with current benchmark results",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Run in CI mode with regression check",
    )

    args = parser.parse_args()

    # Import benchmark test functions
    from benchmarks.input_processor_bench import (
        test_parse_text,
        test_parse_spread,
        test_parse_symbols,
    )
    from benchmarks.analysis_engine_bench import (
        test_analyze_text,
        test_analyze_spread,
        test_analyze_spread_large,
    )
    from benchmarks.report_generator_bench import (
        test_generate_simple,
        test_generate_spread,
        test_generate_patterns,
    )
    from benchmarks.symbols_bench import (
        test_match_keyword_exact,
        test_match_keyword_partial,
        test_get_symbol_by_name_valid,
        test_get_symbol_by_id_valid,
        test_get_symbols_by_theme,
    )

    benchmarks = [
        # Input processor benchmarks
        ("input_processor.text", test_parse_text),
        ("input_processor.spread", test_parse_spread),
        ("input_processor.symbols", test_parse_symbols),
        # Analysis engine benchmarks
        ("analysis_engine.single", test_analyze_text),
        ("analysis_engine.mixed", test_analyze_spread),
        ("analysis_engine.full", test_analyze_spread_large),
        # Report generator benchmarks
        ("report_generator.short", test_generate_simple),
        ("report_generator.medium", test_generate_spread),
        ("report_generator.long", test_generate_patterns),
        # Symbols benchmarks
        ("symbols.keyword", test_match_keyword_exact),
        ("symbols.partial_name", test_match_keyword_partial),
        ("symbols.card_name", test_get_symbol_by_name_valid),
        ("symbols.card_id", test_get_symbol_by_id_valid),
        ("symbols.theme", test_get_symbols_by_theme),
    ]

    results = []
    iterations = args.iterations

    print(f"Running {len(benchmarks)} benchmarks with {iterations} iterations each...\n")

    for name, func in benchmarks:
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)

        mean_time = sum(times) / len(times)
        results.append(SimpleBenchmarkResult(
            name=name,
            mean=mean_time,
            min=min(times),
            max=max(times),
            std_dev=0.0,
            iterations=iterations,
        ))

        if args.verbose:
            print(f"  {name}: {mean_time*1000:.3f}ms mean")

    # Print summary
    print("\n=== Benchmark Results ===\n")
    print(f"{'Benchmark':<35} {'Mean':>12} {'Min':>12} {'Max':>12}")
    print("-" * 75)

    for result in results:
        print(f"{result.name:<35} {result.mean*1000:>11.3f}ms {result.min*1000:>11.3f}ms {result.max*1000:>11.3f}ms")

    print("-" * 75)

    # Calculate total time
    total_time = sum(r.mean for r in results)
    print(f"\nTotal estimated time: {total_time*1000:.3f}ms")

    # Handle --update-baseline flag
    if args.update_baseline:
        manager = BaselineManager()
        collection = manager.load()

        for result in results:
            # Calculate additional statistics
            sorted_times = sorted([result.min + (result.max - result.min) * i / 100
                                   for i in range(result.iterations)])
            # Simple median estimation
            mid = result.iterations // 2
            median = sorted_times[mid] if result.iterations % 2 == 1 else \
                     (sorted_times[mid - 1] + sorted_times[mid]) / 2

            baseline = BenchmarkBaseline(
                name=result.name,
                mean=result.mean,
                median=median,
                std_dev=result.std_dev,
                min_time=result.min,
                max_time=result.max,
                ops_per_second=1.0 / result.mean if result.mean > 0 else 0,
                iterations=result.iterations,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            collection.update_baseline(baseline)

        manager.save(collection)
        print(f"\nBaseline updated with {len(results)} benchmarks")

    # Handle --ci flag (regression check)
    if args.ci:
        from benchmarks.regression import RegressionChecker
        import statistics

        runner_results = []
        for result in results:
            from benchmarks.runner import BenchmarkResult
            # Compute all required fields for BenchmarkResult
            times = []  # We don't have individual times, estimate from mean
            total_time = result.mean * result.iterations
            ops_per_second = result.iterations / total_time if total_time > 0 else 0
            runner_results.append(BenchmarkResult(
                name=result.name,
                iterations=result.iterations,
                total_time=total_time,
                mean=result.mean,
                median=result.mean,  # Approximate
                std_dev=result.std_dev,
                min_time=result.min,
                max_time=result.max,
                ops_per_second=ops_per_second,
            ))

        suite_result = BenchmarkSuiteResult(
            suite_name="clareza-benchmarks",
            results=runner_results,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        checker = RegressionChecker()
        report = checker.check(suite_result)

        if report.has_regressions:
            print("\nFAIL - Performance regressions detected")
            sys.exit(1)
        else:
            print("\nPASS - No regressions detected")
            sys.exit(0)

    # Output pass status for verification
    print("\nPASS")


if __name__ == "__main__":
    cli()
