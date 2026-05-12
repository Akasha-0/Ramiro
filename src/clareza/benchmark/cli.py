"""Command-line interface for clareza benchmark."""

import argparse
import sys
import time
from dataclasses import dataclass

from benchmarks.runner import BenchmarkRunner, BenchmarkSuiteResult


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


if __name__ == "__main__":
    cli()
