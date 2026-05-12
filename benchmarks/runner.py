"""Benchmark runner with timing infrastructure.

Fornece estrutura centralizada para executar e medir performance
de todas as operações do sistema.
"""

import time
import statistics
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Resultado de uma execução de benchmark individual.

    Attributes:
        name: Nome do benchmark executado.
        iterations: Número de iterações executadas.
        total_time: Tempo total de todas as iterações (em segundos).
        mean: Tempo médio por iteração (em segundos).
        median: Tempo mediano por iteração (em segundos).
        std_dev: Desvio padrão das iterações (em segundos).
        min_time: Tempo mínimo de uma iteração (em segundos).
        max_time: Tempo máximo de uma iteração (em segundos).
        ops_per_second: Taxa de operações por segundo.
    """

    name: str
    iterations: int
    total_time: float
    mean: float
    median: float
    std_dev: float
    min_time: float
    max_time: float
    ops_per_second: float

    def to_dict(self) -> dict[str, Any]:
        """Converte resultado para dicionário para serialização JSON."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time": round(self.total_time, 6),
            "mean": round(self.mean, 6),
            "median": round(self.median, 6),
            "std_dev": round(self.std_dev, 6) if self.std_dev is not None else 0.0,
            "min_time": round(self.min_time, 6),
            "max_time": round(self.max_time, 6),
            "ops_per_second": round(self.ops_per_second, 2),
        }


@dataclass
class BenchmarkSuiteResult:
    """Resultado de uma suite de benchmarks.

    Attributes:
        suite_name: Nome da suite de benchmarks.
        results: Lista de resultados individuais.
        timestamp: Timestamp ISO da execução.
        total_duration: Tempo total da suite (em segundos).
    """

    suite_name: str
    results: list[BenchmarkResult] = field(default_factory=list)
    timestamp: str = ""
    total_duration: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Converte resultado para dicionário para serialização JSON."""
        return {
            "suite_name": self.suite_name,
            "timestamp": self.timestamp,
            "total_duration": round(self.total_duration, 6),
            "results": [r.to_dict() for r in self.results],
        }


class BenchmarkRunner:
    """Executor de benchmarks com infraestrutura de timing.

    Fornece métodos para executar benchmarks com medição precisa
    de tempo, usando time.perf_counter para máxima precisão.

    Example:
        >>> runner = BenchmarkRunner()
        >>> result = runner.run(
        ...     name="parse_text",
        ...     func=lambda: processor.parse("texto"),
        ...     iterations=100
        ... )
        >>> print(f"Mean: {result.mean:.6f}s")
    """

    def __init__(
        self,
        default_iterations: int = 10,
        warmup_iterations: int = 2,
        min_time: float = 0.001,
    ) -> None:
        """Inicializa o BenchmarkRunner.

        Args:
            default_iterations: Número padrão de iterações por benchmark.
            warmup_iterations: Número de iterações de warmup antes da medição.
            min_time: Tempo mínimo em segundos para cada iteração (para funções rápidas).
        """
        self.default_iterations = default_iterations
        self.warmup_iterations = warmup_iterations
        self.min_time = min_time
        self._results: list[BenchmarkResult] = []

    def run(
        self,
        name: str,
        func: Callable[[], Any],
        iterations: Optional[int] = None,
        setup: Optional[Callable[[], None]] = None,
    ) -> BenchmarkResult:
        """Executa um benchmark e retorna o resultado.

        Args:
            name: Nome descritivo do benchmark.
            func: Função a ser medida.
            iterations: Número de iterações (usa default se None).
            setup: Função opcional de setup executada antes de cada iteração.

        Returns:
            BenchmarkResult com estatísticas de timing.
        """
        iterations = iterations or self.default_iterations

        # Warmup
        for _ in range(self.warmup_iterations):
            try:
                func()
            except Exception as e:
                logger.warning(f"Warmup failed for {name}: {e}")

        # Execução com medição
        times: list[float] = []

        for _ in range(iterations):
            if setup is not None:
                setup()

            start = time.perf_counter()
            try:
                func()
            except Exception as e:
                logger.error(f"Benchmark {name} failed: {e}")
                raise
            end = time.perf_counter()
            times.append(end - start)

        return self._compute_stats(name, times, iterations)

    def run_suite(
        self,
        suite_name: str,
        benchmarks: list[tuple[str, Callable[[], Any]]],
        iterations: Optional[int] = None,
    ) -> BenchmarkSuiteResult:
        """Executa uma suite de benchmarks.

        Args:
            suite_name: Nome da suite.
            benchmarks: Lista de tuplas (nome, função) para executar.
            iterations: Número de iterações por benchmark.

        Returns:
            BenchmarkSuiteResult com todos os resultados.
        """
        import datetime

        results: list[BenchmarkResult] = []
        suite_start = time.perf_counter()

        for name, func in benchmarks:
            result = self.run(name, func, iterations)
            results.append(result)
            logger.debug(f"Benchmark '{name}' completed: {result.mean:.6f}s")

        total_duration = time.perf_counter() - suite_start
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return BenchmarkSuiteResult(
            suite_name=suite_name,
            results=results,
            timestamp=timestamp,
            total_duration=total_duration,
        )

    @contextmanager
    def timer(self, name: str):
        """Context manager para medir tempo de uma operação.

        Args:
            name: Nome da operação.

        Yields:
            Dict que será preenchido com o tempo medido.

        Example:
            >>> runner = BenchmarkRunner()
            >>> with runner.timer("my_operation") as timing:
            ...     do_something()
            ... print(f"Duration: {timing['duration']:.6f}s")
        """
        timing: dict[str, float] = {}
        start = time.perf_counter()
        try:
            yield timing
        finally:
            timing["duration"] = time.perf_counter() - start
            logger.debug(f"Timer '{name}': {timing['duration']:.6f}s")

    def _compute_stats(
        self,
        name: str,
        times: list[float],
        iterations: int,
    ) -> BenchmarkResult:
        """Calcula estatísticas a partir dos tempos medidos.

        Args:
            name: Nome do benchmark.
            times: Lista de tempos medidos.
            iterations: Número de iterações.

        Returns:
            BenchmarkResult com estatísticas calculadas.
        """
        total_time = sum(times)
        mean = total_time / iterations
        median = statistics.median(times)
        std_dev = statistics.stdev(times) if iterations > 1 else 0.0
        min_time = min(times)
        max_time = max(times)
        ops_per_second = iterations / total_time if total_time > 0 else 0.0

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            mean=mean,
            median=median,
            std_dev=std_dev,
            min_time=min_time,
            max_time=max_time,
            ops_per_second=ops_per_second,
        )

        self._results.append(result)
        return result

    @property
    def results(self) -> list[BenchmarkResult]:
        """Retorna todos os resultados de benchmark executados."""
        return self._results.copy()

    def clear_results(self) -> None:
        """Limpa todos os resultados armazenados."""
        self._results.clear()