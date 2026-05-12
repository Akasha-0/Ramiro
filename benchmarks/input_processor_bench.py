"""Benchmarks para InputProcessor — Sistema de Clareza Simbólico-Estratégica.

Fornece dados de exemplo e benchmarks para o módulo input_processor.py.
Executar com: python -m benchmarks.input_processor_bench
"""

from src.input_processor import InputProcessor
from src.types import StructuredInput

# ----------------------------------------------------------------------
# Sample data para benchmarks
# ----------------------------------------------------------------------

INPUT_TEXT_SAMPLE: str = (
    "Estou passando por um momento difícil no trabalho. "
    "Minha vida amorosa está uma confusão e não sei o que fazer. "
    "Tenho pensado muito sobre meu futuro e minhas decisões. "
    "A saúde anda abalada mas preciso continuar lutando. "
    "Dinheiro está curto este mês e estou preocupado com contas. "
    "Quero melhorar minha situação profissional e crescer na carreira."
)

INPUT_SPREAD_SAMPLE: str = (
    "1,estrela\n"
    "2,casa\n"
    "3,cruz\n"
    "4,coelho\n"
    "5,montanha\n"
)

INPUT_SPREAD_CSV_SAMPLE: str = (
    "pos,card\n"
    "1,estrela\n"
    "2,casa\n"
    "3,cruz\n"
)

INPUT_SYMBOLS_SAMPLE: str = "estrela,casa,cruz,coelho,montanha,peixe,cão,flor"

INPUT_TEXT_LARGE: str = (
    "Estou muito preocupado com minha situação financeira. "
) * 100

INPUT_SYMBOLS_LARGE: str = ",".join([
    "estrela", "casa", "cruz", "coelho", "montanha", "peixe",
    "cão", "flor", "sol", "lua", "mar", "montanha", "vale",
    "floresta", "rio", "caminho", "porta", "janela", "teto",
    "chão", "parede", "portão", "ponte", "estrada", "rua",
    "praça", "jardim", "horta", "campo", "fazenda", "sitio",
    "cidade", "vilarejo", "bairro", "avenida", "alameda",
    "travessa", "beco", "largo", "ladeIRAL", "escada", "rampa",
] * 10)


# ----------------------------------------------------------------------
# Verificação de imports
# ----------------------------------------------------------------------

def verify_imports() -> bool:
    """Verifica se os dados de exemplo podem ser importados.

    Returns:
        True se os dados estão disponíveis corretamente.
    """
    try:
        from benchmarks.input_processor_bench import (
            INPUT_TEXT_SAMPLE,
            INPUT_SPREAD_SAMPLE,
        )
        assert isinstance(INPUT_TEXT_SAMPLE, str)
        assert isinstance(INPUT_SPREAD_SAMPLE, str)
        return True
    except ImportError:
        return False


# ----------------------------------------------------------------------
# Tests rápidos de validação (sem timing)
# ----------------------------------------------------------------------

def test_parse_text() -> StructuredInput:
    """Testa parse de texto livre."""
    processor = InputProcessor()
    return processor.parse(INPUT_TEXT_SAMPLE, "text")


def test_parse_spread() -> StructuredInput:
    """Testa parse de tiragem CSV."""
    processor = InputProcessor()
    return processor.parse(INPUT_SPREAD_SAMPLE, "spread")


def test_parse_spread_with_header() -> StructuredInput:
    """Testa parse de tiragem CSV com cabeçalho."""
    processor = InputProcessor()
    return processor.parse(INPUT_SPREAD_CSV_SAMPLE, "spread")


def test_parse_symbols() -> StructuredInput:
    """Testa parse de símbolos."""
    processor = InputProcessor()
    return processor.parse(INPUT_SYMBOLS_SAMPLE, "symbols")


def test_parse_text_large() -> StructuredInput:
    """Testa parse de texto grande (truncamento)."""
    processor = InputProcessor()
    return processor.parse(INPUT_TEXT_LARGE, "text")


def test_parse_symbols_large() -> StructuredInput:
    """Testa parse de símbolos grande."""
    processor = InputProcessor()
    return processor.parse(INPUT_SYMBOLS_LARGE, "symbols")


# ----------------------------------------------------------------------
# Benchmarks
# ----------------------------------------------------------------------

def run_benchmarks() -> None:
    """Executa todos os benchmarks do InputProcessor."""
    from benchmarks.runner import BenchmarkRunner

    runner = BenchmarkRunner(default_iterations=100, warmup_iterations=5)

    benchmarks = [
        ("parse_text_small", lambda: InputProcessor().parse(INPUT_TEXT_SAMPLE, "text")),
        ("parse_spread_small", lambda: InputProcessor().parse(INPUT_SPREAD_SAMPLE, "spread")),
        ("parse_spread_with_header", lambda: InputProcessor().parse(INPUT_SPREAD_CSV_SAMPLE, "spread")),
        ("parse_symbols_small", lambda: InputProcessor().parse(INPUT_SYMBOLS_SAMPLE, "symbols")),
        ("parse_text_large", lambda: InputProcessor().parse(INPUT_TEXT_LARGE, "text")),
        ("parse_symbols_large", lambda: InputProcessor().parse(INPUT_SYMBOLS_LARGE, "symbols")),
    ]

    results = runner.run_suite("InputProcessor", benchmarks, iterations=100)

    print("\n=== Benchmark Results: InputProcessor ===\n")
    for result in results.results:
        print(f"{result.name}:")
        print(f"  Mean:   {result.mean * 1000:.4f} ms")
        print(f"  Median: {result.median * 1000:.4f} ms")
        print(f"  Ops/s:  {result.ops_per_second:.2f}")
        print()


if __name__ == "__main__":
    print("InputProcessor Benchmark Module")
    print("=" * 40)

    # Verificar imports
    if verify_imports():
        print("Imports OK")
    else:
        print("Import verification failed")

    # Testes de validação
    print("\nRunning validation tests...")

    try:
        result = test_parse_text()
        print(f"  parse_text: OK (keywords={len(result.keywords or [])})")
    except Exception as e:
        print(f"  parse_text: FAIL ({e})")

    try:
        result = test_parse_spread()
        print(f"  parse_spread: OK (cards={len(result.cards or [])})")
    except Exception as e:
        print(f"  parse_spread: FAIL ({e})")

    try:
        result = test_parse_symbols()
        print(f"  parse_symbols: OK (keywords={len(result.keywords or [])})")
    except Exception as e:
        print(f"  parse_symbols: FAIL ({e})")

    try:
        result = test_parse_text_large()
        print(f"  parse_text_large: OK (truncated={len(result.raw_content) <= 5000})")
    except Exception as e:
        print(f"  parse_text_large: FAIL ({e})")

    # Executar benchmarks
    print("\nRunning benchmarks...")
    run_benchmarks()