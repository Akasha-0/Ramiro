"""Baseline management for performance benchmarks.

Fornece funcionalidades para armazenar e carregar dados de baseline,
permitindo comparação de performance entre execuções e detecção
de regressões.
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Diretório padrão para baselines
DEFAULT_BASELINE_DIR = Path(__file__).parent
DEFAULT_BASELINE_FILE = DEFAULT_BASELINE_DIR / "baseline.json"


@dataclass
class BenchmarkBaseline:
    """Dados de baseline para um benchmark individual.

    Attributes:
        name: Nome do benchmark.
        mean: Tempo médio de execução (em segundos).
        median: Tempo mediano de execução (em segundos).
        std_dev: Desvio padrão das execuções (em segundos).
        min_time: Tempo mínimo registrado (em segundos).
        max_time: Tempo máximo registrado (em segundos).
        ops_per_second: Taxa de operações por segundo.
        iterations: Número de iterações usadas na medição.
        timestamp: Timestamp ISO da captura do baseline.
    """

    name: str
    mean: float
    median: float
    std_dev: float
    min_time: float
    max_time: float
    ops_per_second: float
    iterations: int
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Converte baseline para dicionário para serialização JSON."""
        return {
            "name": self.name,
            "mean": round(self.mean, 6),
            "median": round(self.median, 6),
            "std_dev": round(self.std_dev, 6),
            "min_time": round(self.min_time, 6),
            "max_time": round(self.max_time, 6),
            "ops_per_second": round(self.ops_per_second, 2),
            "iterations": self.iterations,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkBaseline":
        """Cria BenchmarkBaseline a partir de dicionário."""
        return cls(
            name=data["name"],
            mean=float(data["mean"]),
            median=float(data["median"]),
            std_dev=float(data["std_dev"]),
            min_time=float(data["min_time"]),
            max_time=float(data["max_time"]),
            ops_per_second=float(data["ops_per_second"]),
            iterations=int(data["iterations"]),
            timestamp=data["timestamp"],
        )


@dataclass
class BaselineCollection:
    """Coleção de baselines para uma suite de benchmarks.

    Attributes:
        suite_name: Nome da suite de benchmarks.
        baselines: Lista de baselines individuais.
        version: Versão do formato de baseline.
        created_at: Timestamp de criação do arquivo.
    """

    suite_name: str
    baselines: list[BenchmarkBaseline] = field(default_factory=list)
    version: str = "1.0"
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Converte coleção para dicionário para serialização JSON."""
        return {
            "suite_name": self.suite_name,
            "version": self.version,
            "created_at": self.created_at,
            "baselines": [b.to_dict() for b in self.baselines],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaselineCollection":
        """Cria BaselineCollection a partir de dicionário."""
        baselines = [BenchmarkBaseline.from_dict(b) for b in data.get("baselines", [])]
        return cls(
            suite_name=data["suite_name"],
            baselines=baselines,
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", ""),
        )

    def get_baseline(self, name: str) -> Optional[BenchmarkBaseline]:
        """Retorna baseline pelo nome do benchmark.

        Args:
            name: Nome do benchmark.

        Returns:
            BenchmarkBaseline ou None se não encontrado.
        """
        for baseline in self.baselines:
            if baseline.name == name:
                return baseline
        return None

    def update_baseline(self, baseline: BenchmarkBaseline) -> None:
        """Atualiza ou adiciona um baseline na coleção.

        Args:
            baseline: Baseline a ser atualizado/adicionado.
        """
        for i, existing in enumerate(self.baselines):
            if existing.name == baseline.name:
                self.baselines[i] = baseline
                logger.debug(f"Baseline '{baseline.name}' updated")
                return
        self.baselines.append(baseline)
        logger.debug(f"Baseline '{baseline.name}' added")


class BaselineManager:
    """Gerenciador de baselines para benchmarks.

    Fornece métodos para carregar, salvar e comparar baselines
    de performance, facilitando a detecção de regressões.

    Example:
        >>> manager = BaselineManager()
        >>> baselines = manager.load()
        >>> baseline = baselines.get_baseline("parse_text")
        >>> if baseline:
        ...     print(f"Mean: {baseline.mean:.6f}s")
    """

    def __init__(
        self,
        baseline_file: Optional[Path] = None,
        suite_name: str = "clareza-benchmarks",
    ) -> None:
        """Inicializa o BaselineManager.

        Args:
            baseline_file: Caminho para arquivo de baseline (default: baseline.json).
            suite_name: Nome da suite de benchmarks.
        """
        self.baseline_file = baseline_file or DEFAULT_BASELINE_FILE
        self.suite_name = suite_name

    def load(self) -> BaselineCollection:
        """Carrega baselines do arquivo.

        Returns:
            BaselineCollection com baselines carregados.
            Retorna coleção vazia se arquivo não existir.
        """
        if not self.baseline_file.exists():
            logger.info(f"Baseline file not found: {self.baseline_file}")
            return BaselineCollection(suite_name=self.suite_name)

        try:
            with open(self.baseline_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            collection = BaselineCollection.from_dict(data)
            logger.info(f"Loaded {len(collection.baselines)} baselines from {self.baseline_file}")
            return collection
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse baseline file: {e}")
            return BaselineCollection(suite_name=self.suite_name)

    def save(self, collection: BaselineCollection) -> None:
        """Salva baselines no arquivo.

        Args:
            collection: BaselineCollection a ser salva.
        """
        import datetime

        if not collection.created_at:
            collection.created_at = datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat()

        try:
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.baseline_file, "w", encoding="utf-8") as f:
                json.dump(collection.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(collection.baselines)} baselines to {self.baseline_file}")
        except OSError as e:
            logger.error(f"Failed to save baseline file: {e}")
            raise

    def save_baseline(self, baseline: BenchmarkBaseline) -> None:
        """Salva um baseline individual, mantendo os existentes.

        Args:
            baseline: Baseline a ser salvo.
        """
        collection = self.load()
        collection.update_baseline(baseline)
        self.save(collection)

    def get_baseline(self, name: str) -> Optional[BenchmarkBaseline]:
        """Retorna baseline específico pelo nome.

        Args:
            name: Nome do benchmark.

        Returns:
            BenchmarkBaseline ou None se não encontrado.
        """
        collection = self.load()
        return collection.get_baseline(name)

    def clear(self) -> None:
        """Remove todos os baselines salvos."""
        if self.baseline_file.exists():
            self.baseline_file.unlink()
            logger.info(f"Cleared baseline file: {self.baseline_file}")


def load_baseline(baseline_file: Optional[Path] = None) -> BaselineCollection:
    """Função de conveniência para carregar baselines.

    Args:
        baseline_file: Caminho opcional para arquivo de baseline.

    Returns:
        BaselineCollection com baselines carregados.
    """
    manager = BaselineManager(baseline_file=baseline_file)
    return manager.load()