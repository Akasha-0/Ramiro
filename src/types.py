"""Tipos compartilhados — Sistema de Clareza Simbólico-Estratégica.

Todas as estruturas de dados usadas na comunicação entre módulos
são definidas aqui como dataclasses. Nenhum dicionário solto
deve circular entre módulos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


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
class SessionRecord:
    """Registro de uma sessão individual de reflexão.

    Attributes:
        session_id: Identificador único da sessão (UUID).
        timestamp: Data e hora da sessão.
        arc_name: Nome do arco de reflexão ao qual esta sessão pertence.
        input_content: Conteúdo de input original.
        format: Formato do input ("text", "spread", "symbols").
        keywords: Lista de palavras-chave identificadas.
        themes: Lista de temas identificados.
        cards: Lista de nomes das cartas (para tiragens).
        diagnosis: Diagnóstico gerado.
        risks: Lista de riscos identificados.
        decisions: Lista de decisões sugeridas.
    """

    session_id: str
    timestamp: datetime
    arc_name: Optional[str] = None
    input_content: str = ""
    format: str = "text"
    keywords: list[str] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    cards: list[str] = field(default_factory=list)
    diagnosis: str = ""
    risks: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)


@dataclass
class ArcSummary:
    """Sumário de um arco de reflexão completo.

    Attributes:
        arc_name: Nome do arco de reflexão.
        total_sessions: Número total de sessões no arco.
        date_range: Tupla (início, fim) das datas das sessões.
        top_themes: Lista dos 3 temas mais recorrentes.
        top_cards: Lista das 3 cartas mais recorrentes.
        session_ids: Lista de IDs de sessão neste arco.
    """

    arc_name: str
    total_sessions: int = 0
    date_range: Optional[tuple[datetime, datetime]] = None
    top_themes: list[str] = field(default_factory=list)
    top_cards: list[str] = field(default_factory=list)
    session_ids: list[str] = field(default_factory=list)


@dataclass
class ReflectionArc:
    """Arco de reflexão com múltiplas sessões.

    Attributes:
        name: Nome do arco de reflexão.
        description: Descrição opcional do arco.
        sessions: Lista de registros de sessão.
        created_at: Data de criação do arco.
        updated_at: Data da última atualização.
    """

    name: str
    description: Optional[str] = None
    sessions: list[SessionRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)