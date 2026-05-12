"""Benchmarks para AnalysisEngine — Sistema de Clareza Simbólico-Estratégica.

Fornece dados de exemplo e benchmarks para o módulo analysis_engine.py.
Executar com: python -m benchmarks.analysis_engine_bench
"""

from src.analysis_engine import AnalysisEngine
from src.input_processor import InputProcessor
from src.types import AnalysisResult, StructuredInput

# ----------------------------------------------------------------------
# Sample data para benchmarks
# ----------------------------------------------------------------------

# Texto complexo com múltiplos temas
ANALYSIS_TEXT_SAMPLE: str = (
    "Estou pasando por um momento difícil no trabalho. "
    "Minha vida amorosa está uma confusão e não sei o que fazer. "
    "Tenho pensado muito sobre meu futuro e minhas decisões. "
    "A saúde anda abalada mas preciso continuar lutando. "
    "Dinheiro está curto este mês e estou preocupado com contas. "
    "Quero melhorar minha situação profissional e crescer na carreira."
)

# Tiragem de 3 cartas (passado, presente, futuro)
ANALYSIS_SPREAD_SAMPLE: list[dict] = [
    {"position": 1, "card_name": "estrela", "context": "passado"},
    {"position": 2, "card_name": "casa", "context": "presente"},
    {"position": 3, "card_name": "cruz", "context": "futuro"},
]

# Keywords variadas
ANALYSIS_KEYWORDS_SAMPLE: list[str] = [
    "estrela", "casa", "cruz", "coelho", "montanha", "peixe"
]

# Tiragem grande (5+ cartas)
ANALYSIS_SPREAD_LARGE: list[dict] = [
    {"position": 1, "card_name": "sol", "context": "passado"},
    {"position": 2, "card_name": "lua", "context": "presente"},
    {"position": 3, "card_name": "estrela", "context": "futuro"},
    {"position": 4, "card_name": "casa", "context": "influência"},
    {"position": 5, "card_name": "cruz", "context": "ação"},
]

# Tiragem com cartas de risco
ANALYSIS_SPREAD_RISK: list[dict] = [
    {"position": 1, "card_name": "cruz", "context": "passado"},
    {"position": 2, "card_name": "nuvens", "context": "presente"},
    {"position": 3, "card_name": "forca", "context": "futuro"},
]

# Texto com palavras de risco
ANALYSIS_TEXT_RISK: str = (
    "Estou passando por um momento de muito perigo. "
    "Sinto que há uma ameaça no meu trabalho e medo de perder meu emprego. "
    "Há também traição na minha relação amorosa. "
    "Estou em risco financeiro e não sei como resolver minhas dívidas."
)

# Texto com palavras de decisão
ANALYSIS_TEXT_DECISION: str = (
    "Preciso escolher entre duas opções no meu trabalho. "
    "Estou em uma encruzilhada importante. "
    "Devo me comprometer com a nova proposta ou encerrar este ciclo? "
    "Quero tomar a decisão certa e mudar minha situação."
)

# Tiragem com decisões
ANALYSIS_SPREAD_DECISION: list[dict] = [
    {"position": 1, "card_name": "cruz de são andré", "context": "presente"},
    {"position": 2, "card_name": "ancora", "context": "passado"},
    {"position": 3, "card_name": "cegonha", "context": "futuro"},
]


# ----------------------------------------------------------------------
# StructuredInput samples (pré-processados)
# ----------------------------------------------------------------------

def get_input_text_sample() -> StructuredInput:
    """Retorna StructuredInput de texto."""
    processor = InputProcessor()
    return processor.parse(ANALYSIS_TEXT_SAMPLE, "text")


def get_input_spread_sample() -> StructuredInput:
    """Retorna StructuredInput de tiragem simples."""
    spread_csv = "\n".join([
        f"{c['position']},{c['card_name']}"
        for c in ANALYSIS_SPREAD_SAMPLE
    ])
    processor = InputProcessor()
    return processor.parse(spread_csv, "spread")


def get_input_spread_large() -> StructuredInput:
    """Retorna StructuredInput de tiragem grande."""
    spread_csv = "\n".join([
        f"{c['position']},{c['card_name']}"
        for c in ANALYSIS_SPREAD_LARGE
    ])
    processor = InputProcessor()
    return processor.parse(spread_csv, "spread")


def get_input_spread_risk() -> StructuredInput:
    """Retorna StructuredInput de tiragem com risco."""
    spread_csv = "\n".join([
        f"{c['position']},{c['card_name']}"
        for c in ANALYSIS_SPREAD_RISK
    ])
    processor = InputProcessor()
    return processor.parse(spread_csv, "spread")


def get_input_text_risk() -> StructuredInput:
    """Retorna StructuredInput de texto com risco."""
    processor = InputProcessor()
    return processor.parse(ANALYSIS_TEXT_RISK, "text")


def get_input_text_decision() -> StructuredInput:
    """Retorna StructuredInput de texto com decisão."""
    processor = InputProcessor()
    return processor.parse(ANALYSIS_TEXT_DECISION, "text")


def get_input_spread_decision() -> StructuredInput:
    """Retorna StructuredInput de tiragem com decisão."""
    spread_csv = "\n".join([
        f"{c['position']},{c['card_name']}"
        for c in ANALYSIS_SPREAD_DECISION
    ])
    processor = InputProcessor()
    return processor.parse(spread_csv, "spread")


# ----------------------------------------------------------------------
# Analysis samples (for direct analysis testing)
# ----------------------------------------------------------------------

ANALYSIS_SAMPLES: dict[str, StructuredInput] = {
    "text_sample": get_input_text_sample(),
    "spread_sample": get_input_spread_sample(),
    "spread_large": get_input_spread_large(),
}


# ----------------------------------------------------------------------
# Verificação de imports
# ----------------------------------------------------------------------

def verify_imports() -> bool:
    """Verifica se os dados de exemplo podem ser importados.

    Returns:
        True se os dados estão disponíveis corretamente.
    """
    try:
        from benchmarks.analysis_engine_bench import ANALYSIS_SAMPLES
        assert isinstance(ANALYSIS_SAMPLES, dict)
        return True
    except ImportError:
        return False


# ----------------------------------------------------------------------
# Tests rápidos de validação (sem timing)
# ----------------------------------------------------------------------


def test_analyze_text() -> AnalysisResult:
    """Testa análise de texto livre."""
    engine = AnalysisEngine()
    input_data = get_input_text_sample()
    return engine.analyze(input_data)


def test_analyze_spread() -> AnalysisResult:
    """Testa análise de tiragem."""
    engine = AnalysisEngine()
    input_data = get_input_spread_sample()
    return engine.analyze(input_data)


def test_analyze_spread_large() -> AnalysisResult:
    """Testa análise de tiragem grande."""
    engine = AnalysisEngine()
    input_data = get_input_spread_large()
    return engine.analyze(input_data)


def test_analyze_spread_risk() -> AnalysisResult:
    """Testa análise de tiragem com risco."""
    engine = AnalysisEngine()
    input_data = get_input_spread_risk()
    return engine.analyze(input_data)


def test_analyze_text_risk() -> AnalysisResult:
    """Testa análise de texto com risco."""
    engine = AnalysisEngine()
    input_data = get_input_text_risk()
    return engine.analyze(input_data)


def test_analyze_text_decision() -> AnalysisResult:
    """Testa análise de texto com decisão."""
    engine = AnalysisEngine()
    input_data = get_input_text_decision()
    return engine.analyze(input_data)


def test_analyze_spread_decision() -> AnalysisResult:
    """Testa análise de tiragem com decisão."""
    engine = AnalysisEngine()
    input_data = get_input_spread_decision()
    return engine.analyze(input_data)


# ----------------------------------------------------------------------
# Benchmarks
# ----------------------------------------------------------------------

def run_benchmarks() -> None:
    """Executa todos os benchmarks do AnalysisEngine."""
    from benchmarks.runner import BenchmarkRunner

    runner = BenchmarkRunner(default_iterations=100, warmup_iterations=5)

    benchmarks = [
        ("analyze_text", lambda: AnalysisEngine().analyze(get_input_text_sample())),
        ("analyze_spread_3cards", lambda: AnalysisEngine().analyze(get_input_spread_sample())),
        ("analyze_spread_5cards", lambda: AnalysisEngine().analyze(get_input_spread_large())),
        ("analyze_spread_risk", lambda: AnalysisEngine().analyze(get_input_spread_risk())),
        ("analyze_text_risk", lambda: AnalysisEngine().analyze(get_input_text_risk())),
        ("analyze_text_decision", lambda: AnalysisEngine().analyze(get_input_text_decision())),
        ("analyze_spread_decision", lambda: AnalysisEngine().analyze(get_input_spread_decision())),
    ]

    results = runner.run_suite("AnalysisEngine", benchmarks, iterations=100)

    print("\n=== Benchmark Results: AnalysisEngine ===\n")
    for result in results.results:
        print(f"{result.name}:")
        print(f"  Mean:   {result.mean * 1000:.4f} ms")
        print(f"  Median: {result.median * 1000:.4f} ms")
        print(f"  Ops/s:  {result.ops_per_second:.2f}")
        print()


if __name__ == "__main__":
    print("AnalysisEngine Benchmark Module")
    print("=" * 40)

    # Verificar imports
    if verify_imports():
        print("Imports OK")
    else:
        print("Import verification failed")

    # Testes de validação
    print("\nRunning validation tests...")

    try:
        result = test_analyze_text()
        print(f"  analyze_text: OK (themes={len(result.themes)}, risks={len(result.risks)})")
    except Exception as e:
        print(f"  analyze_text: FAIL ({e})")

    try:
        result = test_analyze_spread()
        print(f"  analyze_spread: OK (themes={len(result.themes)}, cards={len(result.card_interpretations) if result.card_interpretations else 0})")
    except Exception as e:
        print(f"  analyze_spread: FAIL ({e})")

    try:
        result = test_analyze_spread_large()
        print(f"  analyze_spread_large: OK (themes={len(result.themes)}, patterns={len(result.cross_card_patterns)})")
    except Exception as e:
        print(f"  analyze_spread_large: FAIL ({e})")

    try:
        result = test_analyze_spread_risk()
        print(f"  analyze_spread_risk: OK (risks={len(result.risks)})")
    except Exception as e:
        print(f"  analyze_spread_risk: FAIL ({e})")

    try:
        result = test_analyze_text_risk()
        print(f"  analyze_text_risk: OK (risks={len(result.risks)})")
    except Exception as e:
        print(f"  analyze_text_risk: FAIL ({e})")

    try:
        result = test_analyze_text_decision()
        print(f"  analyze_text_decision: OK (decisions={len(result.decisions)})")
    except Exception as e:
        print(f"  analyze_text_decision: FAIL ({e})")

    try:
        result = test_analyze_spread_decision()
        print(f"  analyze_spread_decision: OK (decisions={len(result.decisions)})")
    except Exception as e:
        print(f"  analyze_spread_decision: FAIL ({e})")

    # Executar benchmarks
    print("\nRunning benchmarks...")
    run_benchmarks()
