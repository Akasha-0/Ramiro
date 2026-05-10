"""Tipos compartilhados — Sistema de Clareza Simbólico-Estratégica.

Todas as estruturas de dados usadas na comunicação entre módulos
são definidas aqui como dataclasses. Nenhum dicionário solto
deve circular entre módulos.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CardPosition:
    """Representa uma carta do Baralho Cigano em uma posição específica.

    Attributes:
        position: Índice da posição na tiragem (1-based).
        card_name: Nome da carta (ex: "Cruz", "Estrela", "Café").
        interpretation: Interpretação gerada pela análise (opcional).
        position_context: Contexto da posição na tiragem (ex: "passado", "presente", "futuro") (opcional).
    """

    position: int
    card_name: str
    interpretation: Optional[str] = None
    position_context: Optional[str] = None


@dataclass
class StructuredInput:
    """Input estruturado após parse pelo InputProcessor.

    Attributes:
        format: Formato original ("text", "spread", "symbols").
        raw_content: Conteúdo bruto original.
        cards: Lista de CardPosition (para format="spread").
        keywords: Lista de palavras-chave detectadas (para format="text" e "symbols").
    """

    format: str
    raw_content: str
    cards: Optional[list[CardPosition]] = None
    keywords: Optional[list[str]] = None


@dataclass
class CrossCardPattern:
    """Padrão detectado entre múltiplas cartas na tiragem.

    Attributes:
        pattern_type: Tipo do padrão detectado
            ("numeric_repeat", "numeric_sequence", "theme_cluster",
             "elemental_imbalance", "conflict").
        card_ids: IDs das cartas que formam o padrão.
        interpretation: Interpretação simbólica do padrão cruzado.
        strength: Intensidade/significância do padrão (opcional).
    """

    pattern_type: str
    card_ids: list[int]
    interpretation: str
    strength: Optional[str] = None


@dataclass
class AnalysisResult:
    """Resultado da análise simbólico-estratégica.

    Attributes:
        diagnosis: Diagnóstico central da situação descrita.
        themes: Lista de temas identificados (trabalho, relação, saúde, etc.).
        risks: Lista de riscos identificados.
        decisions: Lista de caminhos de decisão possíveis.
        practical_plan: Plano prático de ação.
        card_interpretations: Interpretações por carta (para tiragens).
        symbolic_mappings: Mapeamentos simbólicos individuais.
        cross_card_patterns: Padrões detectados entre múltiplas cartas.
    """

    diagnosis: str
    themes: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    practical_plan: str = ""
    card_interpretations: Optional[list[str]] = None
    symbolic_mappings: Optional[dict[str, str]] = None
    cross_card_patterns: list[CrossCardPattern] = field(default_factory=list)


@dataclass
class ValidatedOutput:
    """Output validado pelos guardrails éticos.

    Attributes:
        content: Conteúdo do relatório em Markdown.
        disclaimer_flags: Lista de palavras-chave bloqueadas detectadas.
        sensitive_flags: Lista de flags de sensibilidade detectados no output.
        needs_disclaimer: Indica se um disclaimer ético deve ser inserido.
        is_safe: Indica se o output passou na validação ética.
    """

    content: str
    disclaimer_flags: list[str] = field(default_factory=list)
    sensitive_flags: list[str] = field(default_factory=list)
    needs_disclaimer: bool = False
    is_safe: bool = True


@dataclass
class InputGuardrailsResult:
    """Resultado da detecção de sensibilidade no input do usuário.

    Attributes:
        is_sensitive: Indica se o input contém temas sensíveis.
        flags: Lista de palavras-chave sensíveis detectadas.
    """

    is_sensitive: bool
    flags: list[str] = field(default_factory=list)