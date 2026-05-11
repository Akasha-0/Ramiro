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
        cards: Lista de CardPosition da tiragem (opcional).
    """

    diagnosis: str
    themes: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    practical_plan: str = ""
    card_interpretations: Optional[list[str]] = None
    symbolic_mappings: Optional[dict[str, str]] = None
    cross_card_patterns: list["CrossCardPattern"] = field(default_factory=list)
    cards: Optional[list["CardPosition"]] = None


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
class InputGuardrailsResult:
    """Resultado da detecção de sensibilidade no input do usuário.

    Attributes:
        is_sensitive: Indica se o input contém temas sensíveis.
        flags: Lista de palavras-chave sensíveis detectadas.
    """

    is_sensitive: bool
    flags: list[str] = field(default_factory=list)


@dataclass
class SessionContext:
    """Contexto de sessão para rastreamento de histórico e evitar repetições.

    Attributes:
        session_id: Identificador único da sessão.
        recommendations_history: Lista de recomendações já dadas nesta sessão (para evitar repetição).
        analyzed_inputs: Lista de inputs já analisados nesta sessão.
        timestamps: Lista de timestamps de análises realizadas (ordem cronológica).
    """

    session_id: str
    recommendations_history: list[str] = field(default_factory=list)
    analyzed_inputs: list[str] = field(default_factory=list)
    timestamps: list[str] = field(default_factory=list)


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
class Session:
    """Uma sessão individual de reflexão.

    Attributes:
        session_id: Identificador único da sessão.
        timestamp: Timestamp ISO da sessão.
        input_format: Formato do input ("text", "spread", "symbols").
        raw_content: Conteúdo bruto original.
        analysis_result: Resultado da análise (opcional).
        unresolved_threads: Lista de IDs de threads não resolvidas desta sessão.
    """

    session_id: str
    timestamp: str
    input_format: str
    raw_content: str
    analysis_result: Optional[AnalysisResult] = None
    unresolved_threads: list[str] = field(default_factory=list)


@dataclass
class NarrativeThread:
    """Uma linha narrativa que atravessa múltiplas sessões.

    Attributes:
        thread_id: Identificador único da thread.
        name: Nome descritivo da thread (ex: "Carreira", "Relacionamento").
        theme: Tema central identificado.
        session_ids: Lista de IDs das sessões onde esta thread apareceu.
        status: Status atual ("active", "resolved", "escalated").
        first_mention: Timestamp da primeira menção.
        last_mention: Timestamp da última menção.
        progression: Lista de descrições da progressão ao longo das sessões.
    """

    thread_id: str
    name: str
    theme: str
    session_ids: list[str] = field(default_factory=list)
    status: str = "active"
    first_mention: Optional[str] = None
    last_mention: Optional[str] = None
    progression: list[str] = field(default_factory=list)


@dataclass
class Arc:
    """Um arco narrativo conectando múltiplas sessões.

    Attributes:
        arc_id: Identificador único do arco.
        name: Nome descritivo do arco (ex: "Jornada de 2024").
        sessions: Lista de sessões ordenadas por timestamp.
        threads: Lista de threads narrativas identificadas.
        start_date: Data de início do arco.
        end_date: Data de fim do arco (opcional).
        dominant_themes: Temas dominantes do arco.
    """

    arc_id: str
    name: str
    sessions: list[Session] = field(default_factory=list)
    threads: list[NarrativeThread] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    dominant_themes: list[str] = field(default_factory=list)


@dataclass
class ChapterSummary:
    """Sumário de um capítulo narrativo do arco.

    Attributes:
        chapter_number: Número do capítulo.
        title: Título do capítulo.
        arc_id: ID do arco ao qual este capítulo pertence.
        sessions_covered: Lista de IDs das sessões cobertas.
        narrative_summary: Resumo narrativo conectando as sessões.
        unresolved_threads: Threads identificadas como não resolvidas.
        escalation_detected: Indica se escalada foi detectada.
        resolution_detected: Indica se resolução foi detectada.
        key_insight: Principais insights do capítulo.
    """

    chapter_number: int
    title: str
    arc_id: str
    sessions_covered: list[str] = field(default_factory=list)
    narrative_summary: str = ""
    unresolved_threads: list[str] = field(default_factory=list)
    escalation_detected: bool = False
    resolution_detected: bool = False
    key_insight: str = ""