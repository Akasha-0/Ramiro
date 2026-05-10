"""Tipos compartilhados — Sistema de Clareza Simbólico-Estratégica.

Todas as estruturas de dados usadas na comunicação entre módulos
são definidas aqui como dataclasses. Nenhum dicionário solto
deve circular entre módulos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from typing import Any


@dataclass
class CardPosition:
    """Representa uma carta do Baralho Cigano em uma posição específica.

    Attributes:
        position: Índice da posição na tiragem (1-based).
        card_name: Nome da carta (ex: "Cruz", "Estrela", "Café").
        interpretation: Interpretação gerada pela análise (opcional).
    """

    position: int
    card_name: str
    interpretation: Optional[str] = None


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
    """

    diagnosis: str
    themes: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    practical_plan: str = ""
    card_interpretations: Optional[list[str]] = None
    symbolic_mappings: Optional[dict[str, str]] = None


@dataclass
class ValidatedOutput:
    """Output validado pelos guardrails éticos.

    Attributes:
        content: Conteúdo do relatório em Markdown.
        disclaimer_flags: Lista de palavras-chave bloqueadas detectadas.
        needs_disclaimer: Indica se um disclaimer ético deve ser inserido.
        is_safe: Indica se o output passou na validação ética.
    """

    content: str
    disclaimer_flags: list[str] = field(default_factory=list)
    needs_disclaimer: bool = False
    is_safe: bool = True


@dataclass
class SessionSummary:
    """Resumo de uma sessão para listagem no histórico.

    Attributes:
        session_id: ID único da sessão (formato UUID).
        created_at: Data e hora de criação da sessão.
        input_format: Formato do input original ("text", "spread", "symbols").
        summary: Resumo da sessão (diagnóstico ou palavras-chave).
        themes: Lista de temas identificados.
    """

    session_id: str
    created_at: datetime
    input_format: str
    summary: str
    themes: list[str] = field(default_factory=list)


@dataclass
class SessionData:
    """Dados completos de uma sessão armazenada.

    Attributes:
        session_id: ID único da sessão (formato UUID).
        created_at: Data e hora de criação da sessão.
        input_format: Formato do input original ("text", "spread", "symbols").
        raw_input: Input bruto fornecido pelo usuário.
        structured_input: Input estruturado após parsing.
        analysis_result: Resultado da análise simbólico-estratégica.
        validated_output: Output validado pelos guardrails.
        metadata: Metadados adicionais da sessão.
    """

    session_id: str
    created_at: datetime
    input_format: str
    raw_input: str
    structured_input: Optional[dict[str, Any]] = None
    analysis_result: Optional[dict[str, Any]] = None
    validated_output: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = field(default_factory=dict)
