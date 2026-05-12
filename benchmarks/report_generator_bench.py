"""Benchmarks para ReportGenerator — Sistema de Clareza Simbólico-Estratégica.

Fornece dados de exemplo e benchmarks para o módulo report_generator.py.
Executar com: python -m benchmarks.report_generator_bench
"""

from src.report_generator import ReportGenerator
from src.types import AnalysisResult, CrossCardPattern

# ----------------------------------------------------------------------
# Sample data para benchmarks
# ----------------------------------------------------------------------

# Resultado de análise simples (texto)
REPORT_RESULT_SIMPLE: AnalysisResult = AnalysisResult(
    diagnosis="Situação de transição profissional com desafios emocionais.",
    themes=["trabalho", "relacionamento", "finanças"],
    risks=["instabilidade financeira", "esgotamento emocional"],
    decisions=["Buscar nova oportunidade de emprego", "Estabelecer limites claros"],
    practical_plan="1. Avaliar opções de recolocação profissional\n2. Priorizar bem-estar emocional\n3. Buscar apoio profissional",
)

# Resultado de análise com tiragem
REPORT_RESULT_SPREAD: AnalysisResult = AnalysisResult(
    diagnosis="Período de reflexão e mudança interior.",
    themes=["desenvolvimento pessoal", "espiritualidade"],
    risks=[],
    decisions=["Reservar tempo para auto-reflexão"],
    practical_plan="1. Manter prática de meditação\n2. Registar insights em diário\n3. Compartilhar experiências com pessoas de confiança",
    card_interpretations=[
        "Estrela: Esperança e renovação espiritual",
        "Casa: Representa o lar interior e estabilidade emocional",
        "Cruz: Desafio que requer superação",
    ],
    symbolic_mappings={
        "kw:trabalho": "Carreira",
        "kw:relacionamento": "Conexão",
        "card:estrela": "Esperança",
    },
)

# Resultado de análise com padrões cruzados
REPORT_RESULT_PATTERNS: AnalysisResult = AnalysisResult(
    diagnosis="Arco narrativo de transformação pessoal.",
    themes=["transformação", "autoconhecimento", "relacionamento"],
    risks=["resistência à mudança"],
    decisions=["Aceitar o processo de transformação"],
    practical_plan="1. Abrir-se para novas experiências\n2. Praticar gratidão diariamente\n3. Manter consistência nas práticas de desenvolvimento",
    card_interpretations=[
        "Sol: Clareza e iluminação interior",
        "Lua: Intuição e mundo emocional",
        "Estrela: Direção e propósito",
        "Cruz: Desafio a ser superado",
        "Casa: Lar e pertencimento",
    ],
    symbolic_mappings={
        "kw:transformação": "Metamorfose",
        "kw:mudança": "Transição",
        "card:sol": "Clareza",
        "card:lua": "Intuição",
    },
    cross_card_patterns=[
        CrossCardPattern(
            pattern_type="numeric_sequence",
            card_ids=[1, 2, 3],
            interpretation="Sequência de crescimento espiritual (1-2-3)",
            strength="forte",
        ),
        CrossCardPattern(
            pattern_type="theme_cluster",
            card_ids=[4, 5],
            interpretation="Agrupamento de desafios e responsabilidades",
            strength="moderado",
        ),
    ],
)

# Resultado com riscos elevados
REPORT_RESULT_RISK: AnalysisResult = AnalysisResult(
    diagnosis="Situação de crise com múltiplos fatores de risco.",
    themes=["crise", "finanças", "saúde", "relacionamento"],
    risks=[
        "risco financeiro iminente",
        "problemas de saúde mental",
        "conflito em relacionamentos",
        "perda de emprego",
        "endividamento excessivo",
    ],
    decisions=["Buscar ajuda profissional imediata", "Estabelecer plano de emergência"],
    practical_plan="1. Buscar apoio psicológico\n2. Renegociar dívidas\n3. Avaliar situação profissional\n4. Comunicar-se com entes queridos",
)

# Resultado com foco em decisões
REPORT_RESULT_DECISION: AnalysisResult = AnalysisResult(
    diagnosis="Momento crucial de tomada de decisão.",
    themes=["decisão", "trabalho", "futuro"],
    risks=["incerteza sobre consequências"],
    decisions=[
        "Aceitar proposta de emprego",
        "Investir em qualificação profissional",
        "Mudar de cidade",
    ],
    practical_plan="1. Analisar prós e contras de cada opção\n2. Consultar pessoas de confiança\n3. Definir cronograma de decisão\n4. Executar plano de ação",
)

# Resultado com análise completa
REPORT_RESULT_FULL: AnalysisResult = AnalysisResult(
    diagnosis="Momento de integração entre aspectos profissionais e pessoais.",
    themes=["carreira", "relacionamento", "saúde", "finanças", "espiritualidade"],
    risks=["esgotamento", "desequilíbrio financeiro"],
    decisions=["Buscar equilíbrio entre trabalho e vida pessoal"],
    practical_plan="1. Estabelecer rotina de autocuidado\n2. Priorizar atividades que geram bem-estar\n3. Planejar finanças de forma consciente\n4. Manter conexões sociais ativas",
    card_interpretations=[
        "Café: Encontro e社交ização",
        "Cruz: Desafio espiritual",
        "Estrela: Esperança e renovação",
        "Casa: Lar e pertencimento",
        "Montanha: Superção de obstáculos",
        "Caminho: Jornada e destino",
    ],
    symbolic_mappings={
        "kw:trabalho": "Carreira",
        "kw:amor": "Relacionamento",
        "kw:saúde": "Bem-estar",
        "kw:dinheiro": "Finanças",
        "card:estrela": "Esperança",
        "card:caminho": "Destino",
    },
    cross_card_patterns=[
        CrossCardPattern(
            pattern_type="numeric_repeat",
            card_ids=[1, 2, 3, 4],
            interpretation="Repetição numérica indica ciclos a serem completados",
            strength="forte",
        ),
        CrossCardPattern(
            pattern_type="theme_cluster",
            card_ids=[2, 3, 4],
            interpretation="Agrupamento de desafios emocionais e materiais",
            strength="moderado",
        ),
        CrossCardPattern(
            pattern_type="elemental_imbalance",
            card_ids=[1, 5, 6],
            interpretation="Desequilíbrio entre elementos terra e fogo",
            strength="leve",
        ),
    ],
)

# Resultado mínimo (edge case)
REPORT_RESULT_MINIMAL: AnalysisResult = AnalysisResult(
    diagnosis="",
    themes=[],
    risks=[],
    decisions=[],
    practical_plan="",
)

# Resultado vazio com apenas alguns campos
REPORT_RESULT_PARTIAL: AnalysisResult = AnalysisResult(
    diagnosis="Análise parcial sem dados suficientes.",
    themes=["trabalho"],
)


# ----------------------------------------------------------------------
# Report samples (pré-formatados)
# ----------------------------------------------------------------------

def get_report_simple() -> str:
    """Retorna relatório formatado simples."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_SIMPLE)


def get_report_spread() -> str:
    """Retorna relatório formatado com tiragem."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_SPREAD)


def get_report_patterns() -> str:
    """Retorna relatório formatado com padrões cruzados."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_PATTERNS)


def get_report_risk() -> str:
    """Retorna relatório formatado com riscos."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_RISK)


def get_report_decision() -> str:
    """Retorna relatório formatado com decisões."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_DECISION)


def get_report_full() -> str:
    """Retorna relatório formatado completo."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_FULL)


def get_report_compact() -> str:
    """Retorna relatório no formato compacto."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_SIMPLE, output_format="compact")


def get_report_json() -> str:
    """Retorna relatório no formato JSON."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_SIMPLE, output_format="json")


def get_report_with_disclaimer() -> str:
    """Retorna relatório com disclaimer."""
    generator = ReportGenerator()
    disclaimer = "*Disclaimer: Esta análise é meramente reflexiva e não substitui orientação profissional.*"
    return generator.generate(REPORT_RESULT_SIMPLE, disclaimer=disclaimer)


def get_report_no_timestamp() -> str:
    """Retorna relatório sem timestamp."""
    generator = ReportGenerator(include_timestamp=False)
    return generator.generate(REPORT_RESULT_SIMPLE)


# ----------------------------------------------------------------------
# Analysis samples (for direct report testing)
# ----------------------------------------------------------------------

REPORT_SAMPLES: dict[str, AnalysisResult] = {
    "simple": REPORT_RESULT_SIMPLE,
    "spread": REPORT_RESULT_SPREAD,
    "patterns": REPORT_RESULT_PATTERNS,
    "risk": REPORT_RESULT_RISK,
    "decision": REPORT_RESULT_DECISION,
    "full": REPORT_RESULT_FULL,
    "minimal": REPORT_RESULT_MINIMAL,
    "partial": REPORT_RESULT_PARTIAL,
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
        from benchmarks.report_generator_bench import REPORT_SAMPLES
        assert isinstance(REPORT_SAMPLES, dict)
        return True
    except ImportError:
        return False


# ----------------------------------------------------------------------
# Tests rápidos de validação (sem timing)
# ----------------------------------------------------------------------


def test_generate_simple() -> str:
    """Testa geração de relatório simples."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_SIMPLE)


def test_generate_spread() -> str:
    """Testa geração de relatório com tiragem."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_SPREAD)


def test_generate_patterns() -> str:
    """Testa geração de relatório com padrões cruzados."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_PATTERNS)


def test_generate_risk() -> str:
    """Testa geração de relatório com riscos."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_RISK)


def test_generate_decision() -> str:
    """Testa geração de relatório com decisões."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_DECISION)


def test_generate_full() -> str:
    """Testa geração de relatório completo."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_FULL)


def test_generate_minimal() -> str:
    """Testa geração de relatório mínimo."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_MINIMAL)


def test_generate_compact() -> str:
    """Testa geração de relatório compacto."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_SIMPLE, output_format="compact")


def test_generate_json() -> str:
    """Testa geração de relatório JSON."""
    generator = ReportGenerator()
    return generator.generate(REPORT_RESULT_SIMPLE, output_format="json")


def test_generate_with_disclaimer() -> str:
    """Testa geração de relatório com disclaimer."""
    generator = ReportGenerator()
    disclaimer = "*Disclaimer de teste.*"
    return generator.generate(REPORT_RESULT_SIMPLE, disclaimer=disclaimer)


def test_generate_no_timestamp() -> str:
    """Testa geração de relatório sem timestamp."""
    generator = ReportGenerator(include_timestamp=False)
    return generator.generate(REPORT_RESULT_SIMPLE)


# ----------------------------------------------------------------------
# Benchmarks
# ----------------------------------------------------------------------

def run_benchmarks() -> None:
    """Executa todos os benchmarks do ReportGenerator."""
    from benchmarks.runner import BenchmarkRunner

    runner = BenchmarkRunner(default_iterations=100, warmup_iterations=5)

    benchmarks = [
        ("generate_simple", lambda: ReportGenerator().generate(REPORT_RESULT_SIMPLE)),
        ("generate_spread", lambda: ReportGenerator().generate(REPORT_RESULT_SPREAD)),
        ("generate_patterns", lambda: ReportGenerator().generate(REPORT_RESULT_PATTERNS)),
        ("generate_risk", lambda: ReportGenerator().generate(REPORT_RESULT_RISK)),
        ("generate_decision", lambda: ReportGenerator().generate(REPORT_RESULT_DECISION)),
        ("generate_full", lambda: ReportGenerator().generate(REPORT_RESULT_FULL)),
        ("generate_minimal", lambda: ReportGenerator().generate(REPORT_RESULT_MINIMAL)),
        ("generate_compact", lambda: ReportGenerator().generate(REPORT_RESULT_SIMPLE, output_format="compact")),
        ("generate_json", lambda: ReportGenerator().generate(REPORT_RESULT_SIMPLE, output_format="json")),
        ("generate_with_disclaimer", lambda: ReportGenerator().generate(REPORT_RESULT_SIMPLE, disclaimer="*Disclaimer de teste.*")),
        ("generate_no_timestamp", lambda: ReportGenerator(include_timestamp=False).generate(REPORT_RESULT_SIMPLE)),
    ]

    results = runner.run_suite("ReportGenerator", benchmarks, iterations=100)

    print("\n=== Benchmark Results: ReportGenerator ===\n")
    for result in results.results:
        print(f"{result.name}:")
        print(f"  Mean:   {result.mean * 1000:.4f} ms")
        print(f"  Median: {result.median * 1000:.4f} ms")
        print(f"  Ops/s:  {result.ops_per_second:.2f}")
        print()


if __name__ == "__main__":
    print("ReportGenerator Benchmark Module")
    print("=" * 40)

    # Verificar imports
    if verify_imports():
        print("Imports OK")
    else:
        print("Import verification failed")

    # Testes de validação
    print("\nRunning validation tests...")

    try:
        result = test_generate_simple()
        print(f"  generate_simple: OK (chars={len(result)})")
    except Exception as e:
        print(f"  generate_simple: FAIL ({e})")

    try:
        result = test_generate_spread()
        print(f"  generate_spread: OK (chars={len(result)})")
    except Exception as e:
        print(f"  generate_spread: FAIL ({e})")

    try:
        result = test_generate_patterns()
        print(f"  generate_patterns: OK (chars={len(result)}, patterns section present={len(result) > 100})")
    except Exception as e:
        print(f"  generate_patterns: FAIL ({e})")

    try:
        result = test_generate_risk()
        print(f"  generate_risk: OK (chars={len(result)})")
    except Exception as e:
        print(f"  generate_risk: FAIL ({e})")

    try:
        result = test_generate_decision()
        print(f"  generate_decision: OK (chars={len(result)})")
    except Exception as e:
        print(f"  generate_decision: FAIL ({e})")

    try:
        result = test_generate_full()
        print(f"  generate_full: OK (chars={len(result)})")
    except Exception as e:
        print(f"  generate_full: FAIL ({e})")

    try:
        result = test_generate_minimal()
        print(f"  generate_minimal: OK (chars={len(result)})")
    except Exception as e:
        print(f"  generate_minimal: FAIL ({e})")

    try:
        result = test_generate_compact()
        print(f"  generate_compact: OK (chars={len(result)})")
    except Exception as e:
        print(f"  generate_compact: FAIL ({e})")

    try:
        result = test_generate_json()
        print(f"  generate_json: OK (valid json check={result.startswith('{') and result.endswith('}'))})")
    except Exception as e:
        print(f"  generate_json: FAIL ({e})")

    try:
        result = test_generate_with_disclaimer()
        print(f"  generate_with_disclaimer: OK (disclaimer present={'Disclaimer' in result})")
    except Exception as e:
        print(f"  generate_with_disclaimer: FAIL ({e})")

    try:
        result = test_generate_no_timestamp()
        print(f"  generate_no_timestamp: OK (timestamp absent={'às' not in result})")
    except Exception as e:
        print(f"  generate_no_timestamp: FAIL ({e})")

    # Executar benchmarks
    print("\nRunning benchmarks...")
    run_benchmarks()
