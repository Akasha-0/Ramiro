"""Regression detection for performance benchmarks.

Fornece funcionalidades para detectar regressions de performance
entre execuções de benchmarks e baselines salvos, com suporte
para integração em CI/CD.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Any

from benchmarks.baseline import (
    BaselineManager,
    BaselineCollection,
    BenchmarkBaseline,
)
from benchmarks.runner import BenchmarkResult, BenchmarkSuiteResult

logger = logging.getLogger(__name__)


@dataclass
class RegressionResult:
    """Resultado da detecção de regressão para um benchmark individual.

    Attributes:
        name: Nome do benchmark.
        baseline_mean: Tempo médio do baseline (em segundos).
        current_mean: Tempo médio atual (em segundos).
        regression_ratio: Razão entre tempo atual e baseline (1.0 = sem mudança).
        regression_percent: Porcentagem de regressão (> 0 indica slowdown).
        is_regression: Indica se houve regressão além do threshold.
        threshold: Threshold configurado para detecção.
    """

    name: str
    baseline_mean: float
    current_mean: float
    regression_ratio: float
    regression_percent: float
    is_regression: bool
    threshold: float


@dataclass
class RegressionReport:
    """Relatório de regressões detectadas em uma suite de benchmarks.

    Attributes:
        suite_name: Nome da suite avaliada.
        total_benchmarks: Número total de benchmarks avaliados.
        regressions_found: Número de regressões detectadas.
        regression_results: Lista de resultados individuais.
        has_regressions: Indica se alguma regressão foi detectada.
        max_regression_percent: Maior porcentagem de regressão encontrada.
        timestamp: Timestamp ISO da verificação.
    """

    suite_name: str
    total_benchmarks: int = 0
    regressions_found: int = 0
    regression_results: list[RegressionResult] = field(default_factory=list)
    has_regressions: bool = False
    max_regression_percent: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Converte relatório para dicionário para serialização JSON."""
        return {
            "suite_name": self.suite_name,
            "total_benchmarks": self.total_benchmarks,
            "regressions_found": self.regressions_found,
            "has_regressions": self.has_regressions,
            "max_regression_percent": round(self.max_regression_percent, 2),
            "timestamp": self.timestamp,
            "regressions": [r.__dict__ for r in self.regression_results],
        }

    def get_summary(self) -> str:
        """Retorna resumo textual do relatório."""
        if not self.has_regressions:
            return f"[PASS] All {self.total_benchmarks} benchmarks within threshold"
        return (
            f"[FAIL] {self.regressions_found}/{self.total_benchmarks} benchmarks "
            f"regressed (max: {self.max_regression_percent:.1f}%)"
        )


class RegressionChecker:
    """Detector de regressões de performance para CI/CD.

    Compara resultados de benchmarks com baselines salvos e
    detecta quando a performance degrada além de um threshold
    configurável (default: 20%).

    Example:
        >>> checker = RegressionChecker(threshold=0.20)
        >>> suite_result = runner.run_suite("test", benchmarks)
        >>> report = checker.check(suite_result)
        >>> if report.has_regressions:
        ...     print(f"Regressions detected: {report.regressions_found}")
    """

    DEFAULT_THRESHOLD = 0.20  # 20% de regressão máxima permitida

    def __init__(
        self,
        threshold: Optional[float] = None,
        baseline_manager: Optional[BaselineManager] = None,
    ) -> None:
        """Inicializa o RegressionChecker.

        Args:
            threshold: Threshold de regressão (0.0-1.0, default: 0.20 = 20%).
            baseline_manager: BaselineManager opcional (cria padrão se None).
        """
        self.threshold = threshold if threshold is not None else self.DEFAULT_THRESHOLD
        self.baseline_manager = baseline_manager or BaselineManager()

        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {self.threshold}")

    def check(self, suite_result: BenchmarkSuiteResult) -> RegressionReport:
        """Verifica regressões em uma suite de benchmarks.

        Args:
            suite_result: Resultado da suite de benchmarks.

        Returns:
            RegressionReport com resultados da verificação.
        """
        import datetime

        baselines = self.baseline_manager.load()

        regression_results: list[RegressionResult] = []
        regressions_found = 0
        max_regression_percent = 0.0

        for result in suite_result.results:
            baseline = baselines.get_baseline(result.name)

            if baseline is None:
                logger.debug(f"No baseline for '{result.name}', skipping")
                continue

            regression_result = self._check_single(result, baseline)
            regression_results.append(regression_result)

            if regression_result.is_regression:
                regressions_found += 1
                logger.warning(
                    f"Regression detected: {result.name} is "
                    f"{regression_result.regression_percent:.1f}% slower "
                    f"(threshold: {self.threshold * 100:.0f}%)"
                )

            max_regression_percent = max(
                max_regression_percent,
                regression_result.regression_percent
            )

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        report = RegressionReport(
            suite_name=suite_result.suite_name,
            total_benchmarks=len(regression_results),
            regressions_found=regressions_found,
            regression_results=regression_results,
            has_regressions=regressions_found > 0,
            max_regression_percent=max_regression_percent,
            timestamp=timestamp,
        )

        return report

    def check_single(
        self,
        result: BenchmarkResult,
        baseline: BenchmarkBaseline,
    ) -> RegressionResult:
        """Verifica regressão para um benchmark individual.

        Args:
            result: Resultado atual do benchmark.
            baseline: Baseline para comparação.

        Returns:
            RegressionResult com resultado da verificação.
        """
        return self._check_single(result, baseline)

    def _check_single(
        self,
        result: BenchmarkResult,
        baseline: BenchmarkBaseline,
    ) -> RegressionResult:
        """Método interno para verificar regressão individual.

        Args:
            result: Resultado atual do benchmark.
            baseline: Baseline para comparação.

        Returns:
            RegressionResult com resultado da verificação.
        """
        regression_ratio = result.mean / baseline.mean if baseline.mean > 0 else 1.0
        regression_percent = (regression_ratio - 1.0) * 100.0
        is_regression = regression_percent > (self.threshold * 100.0)

        return RegressionResult(
            name=result.name,
            baseline_mean=baseline.mean,
            current_mean=result.mean,
            regression_ratio=regression_ratio,
            regression_percent=regression_percent,
            is_regression=is_regression,
            threshold=self.threshold,
        )

    def format_report(self, report: RegressionReport, verbose: bool = False) -> str:
        """Formata relatório de regressões para exibição.

        Args:
            report: Relatório a ser formatado.
            verbose: Se True, inclui detalhes de cada benchmark.

        Returns:
            String formatada com o relatório.
        """
        lines = [
            f"Regression Check: {report.suite_name}",
            f"Threshold: {self.threshold * 100:.0f}%",
            f"Total benchmarks: {report.total_benchmarks}",
            f"Regressions found: {report.regressions_found}",
            "",
            report.get_summary(),
        ]

        if verbose and report.regression_results:
            lines.append("")
            lines.append("Details:")
            for r in sorted(report.regression_results, key=lambda x: -x.regression_percent):
                status = "FAIL" if r.is_regression else "PASS"
                lines.append(
                    f"  [{status}] {r.name}: {r.regression_percent:+.1f}% "
                    f"(baseline: {r.baseline_mean:.6f}s, "
                    f"current: {r.current_mean:.6f}s)"
                )

        return "\n".join(lines)

    def get_exit_code(self, report: RegressionReport) -> int:
        """Retorna código de saída para integração CI.

        Args:
            report: Relatório de regressões.

        Returns:
            0 se não há regressões, 1 se há regressões.
        """
        return 0 if not report.has_regressions else 1