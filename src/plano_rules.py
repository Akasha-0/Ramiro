"""Estruturas de dados para o motor de recomendações do Plano Prático.

Define os dataclasses usados para representar regras configuráveis
e resultados de recomendações do sistema de plano prático.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RecommendationResult:
    """Resultado de uma recomendação individual do Plano Prático.

    Attributes:
        action: Descrição da ação recomendada.
        time_frame: Prazo sugerido (immediate, this_week, this_month).
        success_criteria: Critério claro para avaliar se a ação foi bem-sucedida.
        urgency: Nível de urgência (low, medium, high, critical).
        card_themes: Lista de temas das cartas que geraram esta recomendação.
        source_rules: Lista de IDs das regras que geraram esta recomendação.
    """

    action: str
    time_frame: str
    success_criteria: str
    urgency: str = "medium"
    card_themes: list[str] = field(default_factory=list)
    source_rules: list[str] = field(default_factory=list)


@dataclass
class PlanoRules:
    """Estrutura que representa uma regra configurável do motor de plano prático.

    Attributes:
        rule_id: Identificador único da regra (ex: "work_urgency_high").
        themes: Lista de temas de cartas que ativam esta regra.
        keywords: Palavras-chave que também podem ativar esta regra.
        min_urgency: Nível mínimo de urgência das cartas para ativar a regra.
        actions: Lista de ações recomendadas quando a regra é ativada.
        conditions: Condições que precisam ser verdadeiras para a regra ativar.
        priority: Prioridade da regra (maior = aplicada primeiro).
        description: Descrição legível da regra para documentação.
    """

    rule_id: str
    themes: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    min_urgency: str = "low"
    actions: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    priority: int = 0
    description: str = ""


@dataclass
class PlanoContext:
    """Contexto de uma sessão para geração de plano prático.

    Attributes:
        detected_themes: Temas identificados nas cartas ou texto do usuário.
        card_themes: Lista de temas das cartas na tiragem (trabalho, relação, etc.).
        user_goal: Objetivo declarado pelo usuário (se disponível).
        urgency_level: Nível de urgência detectado (low, medium, high, critical).
        past_actions: Ações já recomendadas em sessões anteriores (para evitar repetição).
        keywords: Palavras-chave relevantes extraídas do input.
    """

    detected_themes: list[str] = field(default_factory=list)
    card_themes: list[str] = field(default_factory=list)
    user_goal: Optional[str] = None
    urgency_level: str = "medium"
    past_actions: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)