"""Benchmarks para Symbols — Sistema de Clareza Simbólico-Estratégica.

Fornece dados de exemplo e benchmarks para o módulo symbols.py.
Executar com: python -m benchmarks.symbols_bench
"""

from src.symbols import (
    CiganoSymbol,
    get_all_symbols,
    get_symbol_by_id,
    get_symbol_by_name,
    match_keyword,
    get_themes,
    get_symbols_by_theme,
    get_symbol_count,
    get_deck_source,
    reload_deck,
)

# ----------------------------------------------------------------------
# Sample data para benchmarks
# ----------------------------------------------------------------------

# Keywords variadas para busca
KEYWORD_SAMPLES: list[str] = [
    "casa",
    "amor",
    "trabalho",
    "saúde",
    "dinheiro",
    "viagem",
    "família",
    "espiritual",
    "transformação",
    "sorte",
    "morte",
    "cruz",
    "estrela",
    "cigano",
    "futuro",
]

# Keywords parciais para busca fuzzy
KEYWORD_PARTIAL_SAMPLES: list[str] = [
    "cas",
    "amo",
    "trab",
    "saúd",
    "dinhe",
    "viage",
    "famil",
    "espiri",
]

# Nomes de cartas para busca direta
CARD_NAME_SAMPLES: list[str] = [
    "A Estrela",
    "A Casa",
    "A Cruz",
    "O Cigano",
    "O Trevo",
    "O Navio",
    "A Morte",
    "O Cão",
    "A Lua",
    "O Peixe",
]

# IDs de cartas válidos
CARD_ID_SAMPLES: list[int] = [1, 5, 10, 15, 20, 25, 30, 36]

# IDs de cartas inválidos
INVALID_CARD_ID_SAMPLES: list[int] = [0, 37, 100, -1, 999]

# Temas válidos
THEME_SAMPLES: list[str] = [
    "trabalho",
    "relação",
    "saúde",
    "espiritual",
    "dinheiro",
    "viagem",
    "família",
]

# Keywords para match exato
KEYWORD_EXACT_SAMPLES: list[str] = [
    "casa",
    "lar",
    "família",
    "cruz",
    "estrela",
    "amor",
    "dinheiro",
    "saúde",
]

# Keywords para match parcial
KEYWORD_FUZZY_SAMPLES: list[str] = [
    "cigano",
    "nômade",
    "peregrino",
    "trevo",
    "fortuna",
    "sorte",
    "navio",
    "jornada",
]


# ----------------------------------------------------------------------
# Verificação de imports
# ----------------------------------------------------------------------

def verify_imports() -> bool:
    """Verifica se os dados de exemplo podem ser importados.

    Returns:
        True se os dados estão disponíveis corretamente.
    """
    try:
        from benchmarks.symbols_bench import KEYWORD_SAMPLES
        assert isinstance(KEYWORD_SAMPLES, list)
        assert len(KEYWORD_SAMPLES) > 0
        return True
    except ImportError:
        return False


# ----------------------------------------------------------------------
# Tests rápidos de validação (sem timing)
# ----------------------------------------------------------------------


def test_get_all_symbols() -> list[CiganoSymbol]:
    """Testa recuperação de todas as cartas."""
    return get_all_symbols()


def test_get_symbol_count() -> int:
    """Testa contagem de símbolos."""
    return get_symbol_count()


def test_get_symbol_by_id_valid() -> CiganoSymbol | None:
    """Testa busca por ID válido."""
    return get_symbol_by_id(1)


def test_get_symbol_by_id_invalid() -> CiganoSymbol | None:
    """Testa busca por ID inválido."""
    return get_symbol_by_id(999)


def test_get_symbol_by_name_valid() -> CiganoSymbol | None:
    """Testa busca por nome válido."""
    return get_symbol_by_name("Estrela")


def test_get_symbol_by_name_case_insensitive() -> CiganoSymbol | None:
    """Testa busca por nome case-insensitive."""
    return get_symbol_by_name("A ESTRELA")


def test_get_symbol_by_name_not_found() -> CiganoSymbol | None:
    """Testa busca por nome não encontrado."""
    return get_symbol_by_name("Inexistente")


def test_match_keyword_exact() -> list[CiganoSymbol]:
    """Testa match exato de keyword."""
    return match_keyword("casa")


def test_match_keyword_partial() -> list[CiganoSymbol]:
    """Testa match parcial de keyword."""
    return match_keyword("cas")


def test_match_keyword_not_found() -> list[CiganoSymbol]:
    """Testa match de keyword não encontrada."""
    return match_keyword("xyznonexistent")


def test_get_themes() -> list[str]:
    """Testa recuperação de temas."""
    return get_themes()


def test_get_symbols_by_theme() -> list[CiganoSymbol]:
    """Testa busca por tema."""
    return get_symbols_by_theme("trabalho")


def test_get_symbols_by_theme_not_found() -> list[CiganoSymbol]:
    """Testa busca por tema não encontrado."""
    return get_symbols_by_theme("inexistente")


def test_get_deck_source() -> str:
    """Testa recuperação da fonte do catálogo."""
    return get_deck_source()


def test_reload_deck() -> bool:
    """Testa recarregamento do catálogo."""
    return reload_deck()


# ----------------------------------------------------------------------
# Benchmarks
# ----------------------------------------------------------------------


def run_benchmarks() -> None:
    """Executa todos os benchmarks do Symbols."""
    from benchmarks.runner import BenchmarkRunner

    runner = BenchmarkRunner(default_iterations=100, warmup_iterations=5)

    benchmarks = [
        # get_all_symbols
        ("get_all_symbols", lambda: get_all_symbols()),
        # get_symbol_count
        ("get_symbol_count", lambda: get_symbol_count()),
        # get_symbol_by_id
        ("get_symbol_by_id_valid", lambda: get_symbol_by_id(17)),
        ("get_symbol_by_id_invalid", lambda: get_symbol_by_id(999)),
        # get_symbol_by_name
        ("get_symbol_by_name_valid", lambda: get_symbol_by_name("Estrela")),
        ("get_symbol_by_name_case", lambda: get_symbol_by_name("A ESTRELA")),
        ("get_symbol_by_name_not_found", lambda: get_symbol_by_name("Inexistente")),
        # match_keyword
        ("match_keyword_exact", lambda: match_keyword("casa")),
        ("match_keyword_partial", lambda: match_keyword("cas")),
        ("match_keyword_not_found", lambda: match_keyword("xyznonexistent")),
        # get_themes
        ("get_themes", lambda: get_themes()),
        # get_symbols_by_theme
        ("get_symbols_by_theme_valid", lambda: get_symbols_by_theme("trabalho")),
        ("get_symbols_by_theme_not_found", lambda: get_symbols_by_theme("inexistente")),
        # get_deck_source
        ("get_deck_source", lambda: get_deck_source()),
        # reload_deck
        ("reload_deck", lambda: reload_deck()),
        # Iteration over all symbols (simula análise completa)
        ("iterate_all_symbols", lambda: [s for s in get_all_symbols()]),
        ("find_symbols_by_keyword", lambda: match_keyword("estrela")),
    ]

    results = runner.run_suite("Symbols", benchmarks, iterations=100)

    print("\n=== Benchmark Results: Symbols ===\n")
    for result in results.results:
        print(f"{result.name}:")
        print(f"  Mean:   {result.mean * 1000:.4f} ms")
        print(f"  Median: {result.median * 1000:.4f} ms")
        print(f"  Ops/s:  {result.ops_per_second:.2f}")
        print()


def run_keyword_benchmarks() -> None:
    """Executa benchmarks de keywords individually."""
    from benchmarks.runner import BenchmarkRunner

    runner = BenchmarkRunner(default_iterations=50, warmup_iterations=3)

    benchmarks = [
        (f"match_keyword_{kw}", lambda kw=kw: match_keyword(kw))
        for kw in KEYWORD_SAMPLES
    ]

    results = runner.run_suite("Symbols_Keywords", benchmarks, iterations=50)

    print("\n=== Benchmark Results: Symbols Keywords ===\n")
    for result in results.results:
        print(f"{result.name}:")
        print(f"  Mean:   {result.mean * 1000:.4f} ms")
        print(f"  Median: {result.median * 1000:.4f} ms")
        print(f"  Ops/s:  {result.ops_per_second:.2f}")
        print()


def run_card_name_benchmarks() -> None:
    """Executa benchmarks de busca por nome de carta."""
    from benchmarks.runner import BenchmarkRunner

    runner = BenchmarkRunner(default_iterations=50, warmup_iterations=3)

    benchmarks = [
        (f"get_by_name_{name.replace(' ', '_').lower()}", lambda name=name: get_symbol_by_name(name))
        for name in CARD_NAME_SAMPLES
    ]

    results = runner.run_suite("Symbols_CardNames", benchmarks, iterations=50)

    print("\n=== Benchmark Results: Symbols Card Names ===\n")
    for result in results.results:
        print(f"{result.name}:")
        print(f"  Mean:   {result.mean * 1000:.4f} ms")
        print(f"  Median: {result.median * 1000:.4f} ms")
        print(f"  Ops/s:  {result.ops_per_second:.2f}")
        print()


if __name__ == "__main__":
    print("Symbols Benchmark Module")
    print("=" * 40)

    # Verificar imports
    if verify_imports():
        print("Imports OK")
    else:
        print("Import verification failed")

    # Testes de validação
    print("\nRunning validation tests...")

    try:
        symbols = test_get_all_symbols()
        print(f"  get_all_symbols: OK (count={len(symbols)})")
    except Exception as e:
        print(f"  get_all_symbols: FAIL ({e})")

    try:
        count = test_get_symbol_count()
        print(f"  get_symbol_count: OK (count={count})")
    except Exception as e:
        print(f"  get_symbol_count: FAIL ({e})")

    try:
        symbol = test_get_symbol_by_id_valid()
        print(f"  get_symbol_by_id_valid: OK (name={symbol.name if symbol else 'None'})")
    except Exception as e:
        print(f"  get_symbol_by_id_valid: FAIL ({e})")

    try:
        symbol = test_get_symbol_by_id_invalid()
        print(f"  get_symbol_by_id_invalid: OK (result={symbol})")
    except Exception as e:
        print(f"  get_symbol_by_id_invalid: FAIL ({e})")

    try:
        symbol = test_get_symbol_by_name_valid()
        print(f"  get_symbol_by_name_valid: OK (id={symbol.id if symbol else 'None'})")
    except Exception as e:
        print(f"  get_symbol_by_name_valid: FAIL ({e})")

    try:
        symbol = test_get_symbol_by_name_case_insensitive()
        print(f"  get_symbol_by_name_case_insensitive: OK (id={symbol.id if symbol else 'None'})")
    except Exception as e:
        print(f"  get_symbol_by_name_case_insensitive: FAIL ({e})")

    try:
        symbol = test_get_symbol_by_name_not_found()
        print(f"  get_symbol_by_name_not_found: OK (result={symbol})")
    except Exception as e:
        print(f"  get_symbol_by_name_not_found: FAIL ({e})")

    try:
        results = test_match_keyword_exact()
        print(f"  match_keyword_exact: OK (matches={len(results)})")
    except Exception as e:
        print(f"  match_keyword_exact: FAIL ({e})")

    try:
        results = test_match_keyword_partial()
        print(f"  match_keyword_partial: OK (matches={len(results)})")
    except Exception as e:
        print(f"  match_keyword_partial: FAIL ({e})")

    try:
        results = test_match_keyword_not_found()
        print(f"  match_keyword_not_found: OK (matches={len(results)})")
    except Exception as e:
        print(f"  match_keyword_not_found: FAIL ({e})")

    try:
        themes = test_get_themes()
        print(f"  get_themes: OK (themes={themes})")
    except Exception as e:
        print(f"  get_themes: FAIL ({e})")

    try:
        symbols = test_get_symbols_by_theme()
        print(f"  get_symbols_by_theme: OK (count={len(symbols)})")
    except Exception as e:
        print(f"  get_symbols_by_theme: FAIL ({e})")

    try:
        symbols = test_get_symbols_by_theme_not_found()
        print(f"  get_symbols_by_theme_not_found: OK (count={len(symbols)})")
    except Exception as e:
        print(f"  get_symbols_by_theme_not_found: FAIL ({e})")

    try:
        source = test_get_deck_source()
        print(f"  get_deck_source: OK (source={source})")
    except Exception as e:
        print(f"  get_deck_source: FAIL ({e})")

    try:
        result = test_reload_deck()
        print(f"  reload_deck: OK (result={result})")
    except Exception as e:
        print(f"  reload_deck: FAIL ({e})")

    # Executar benchmarks
    print("\nRunning benchmarks...")
    run_benchmarks()

    print("\nRunning keyword benchmarks...")
    run_keyword_benchmarks()

    print("\nRunning card name benchmarks...")
    run_card_name_benchmarks()
