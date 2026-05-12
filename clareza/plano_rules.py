"""Estruturas de dados e carregamento de regras para o motor de recomendações do Plano Prático.

Define os dataclasses usados para representar regras configuráveis
e resultados de recomendações do sistema de plano prático, além de funções
de carga e validação das regras definidas em data/plano_rules.json.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from clareza.symbols import CiganoSymbol, get_symbol_by_name

logger = logging.getLogger(__name__)


@dataclass
class ActionTemplate:
    """Template de ação configurável do plano prático.

    Attributes:
        type: Identificador do tipo de ação.
        template: Template com marcadores para substituição.
        timeframe: Prazo sugerido (immediate, this_week, this_month).
        success_criterion: Critério para avaliar sucesso da ação.
    """

    type: str
    template: str
    timeframe: str
    success_criterion: str


@dataclass
class ThemeActions:
    """Conjunto de ações associated a um tema específico.

    Attributes:
        description: Descrição do tema.
        action_templates: Lista de templates de ação para este tema.
        card_ids: IDs das cartas que ativam este tema.
    """

    description: str
    action_templates: list[ActionTemplate]
    card_ids: list[int]


@dataclass
class EscalationLevel:
    """Nível de escalonamento de urgência.

    Attributes:
        description: Descrição do nível.
        multiplier: Multiplicador para ajuste de urgência.
        timeframe_adjustment: Como ajustar o prazo (no_change, immediate).
    """

    description: str
    multiplier: float
    timeframe_adjustment: str


@dataclass
class UrgencyEscalation:
    """Configurações de escalonamento de urgência.

    Attributes:
        description: Descrição das regras de escalonamento.
        danger_cards: IDs de cartas consideradas perigosas.
        danger_keywords: Keywords que indicam perigo.
        escalation_levels: Mapeamento de níveis para suas configs.
        default_level: Nível de urgência padrão.
    """

    description: str
    danger_cards: list[int]
    danger_keywords: list[str]
    escalation_levels: dict[str, EscalationLevel]
    default_level: str


@dataclass
class RecommendationTemplate:
    """Template de recomendação reutilizável.

    Attributes:
        id: Identificador único do template.
        template: Template formatado.
        examples: Exemplos de uso do template.
    """

    id: str
    template: str
    examples: list[str]


@dataclass
class TimeframeDefinition:
    """Definição de horizonte temporal.

    Attributes:
        label: Rótulo legível.
        horizon_days: Número de dias do horizonte.
        description: Descrição detalhada.
    """

    label: str
    horizon_days: int
    description: str


@dataclass
class SuccessCriterion:
    """Critério de sucesso por categoria.

    Attributes:
        label: Rótulo da categoria.
        criteria: Lista de critérios específicos.
    """

    label: str
    criteria: list[str]


@dataclass
class PlanoRules:
    """Estrutura principal que representa as regras configuráveis do motor de plano prático.

    Attributes:
        card_actions: Ações por tema de carta.
        urgency_escalation: Configurações de escalonamento de urgência.
        recommendation_templates: Templates reutilizáveis para recomendações.
        timeframes: Definições de horizontes temporais.
        success_criteria: Critérios de sucesso por categoria.
    """

    card_actions: dict[str, ThemeActions]
    urgency_escalation: UrgencyEscalation
    recommendation_templates: list[RecommendationTemplate]
    timeframes: dict[str, TimeframeDefinition]
    success_criteria: dict[str, SuccessCriterion]


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


# ----------------------------------------------------------------------
# Validação
# ----------------------------------------------------------------------


class PlanoRulesValidationError(Exception):
    """Raised when plano_rules.json fails validation."""

    pass


def _load_raw_json(path: Path) -> dict:
    """Carrega o arquivo JSON bruto sem validação.

    Args:
        path: Caminho para o arquivo plano_rules.json.

    Returns:
        Dicionário com os dados carregados.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        PlanoRulesValidationError: Se o JSON for inválido.
    """
    if not path.exists():
        raise FileNotFoundError(f"plano_rules.json não encontrado em {path}")

    import json

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise PlanoRulesValidationError(f"JSON inválido em {path}: {e}") from e

    return data


def _parse_action_template(raw: dict) -> ActionTemplate:
    """Parseia um template de ação individual.

    Args:
        raw: Dicionário representando um template de ação.

    Returns:
        ActionTemplate instanciado.

    Raises:
        PlanoRulesValidationError: Se campos obrigatórios faltarem.
    """
    required = ("type", "template", "timeframe", "success_criterion")
    for field_name in required:
        if field_name not in raw:
            raise PlanoRulesValidationError(
                f"Template de ação sem campo obrigatório: {field_name}"
            )

    return ActionTemplate(
        type=str(raw["type"]),
        template=str(raw["template"]),
        timeframe=str(raw["timeframe"]),
        success_criterion=str(raw["success_criterion"]),
    )


def _parse_theme_actions(theme: str, raw: dict) -> ThemeActions:
    """Parseia um bloco de ações por tema.

    Args:
        theme: Nome do tema (chave do dicionário).
        raw: Dicionário com description, action_templates e card_ids.

    Returns:
        ThemeActions instanciado.

    Raises:
        PlanoRulesValidationError: Se a estrutura for inválida.
    """
    if "action_templates" not in raw:
        raise PlanoRulesValidationError(f"Tema '{theme}' sem action_templates")
    if "card_ids" not in raw:
        raise PlanoRulesValidationError(f"Tema '{theme}' sem card_ids")

    action_templates = [_parse_action_template(t) for t in raw["action_templates"]]
    card_ids = [int(cid) for cid in raw["card_ids"]]

    return ThemeActions(
        description=raw.get("description", ""),
        action_templates=action_templates,
        card_ids=card_ids,
    )


def _parse_escalation_level(raw: dict) -> EscalationLevel:
    """Parseia um nível de escalonamento individual.

    Args:
        raw: Dicionário com description, multiplier e timeframe_adjustment.

    Returns:
        EscalationLevel instanciado.
    """
    return EscalationLevel(
        description=raw.get("description", ""),
        multiplier=float(raw.get("multiplier", 1.0)),
        timeframe_adjustment=str(raw.get("timeframe_adjustment", "no_change")),
    )


def _parse_urgency_escalation(raw: dict) -> UrgencyEscalation:
    """Parseia o bloco de escalonamento de urgência.

    Args:
        raw: Dicionário com description, danger_cards, danger_keywords,
             escalation_levels e default_level.

    Returns:
        UrgencyEscalation instanciado.
    """
    escalation_levels_raw = raw.get("escalation_levels", {})
    escalation_levels = {
        k: _parse_escalation_level(v) for k, v in escalation_levels_raw.items()
    }

    return UrgencyEscalation(
        description=raw.get("description", ""),
        danger_cards=[int(c) for c in raw.get("danger_cards", [])],
        danger_keywords=[str(k) for k in raw.get("danger_keywords", [])],
        escalation_levels=escalation_levels,
        default_level=str(raw.get("default_level", "low")),
    )


def _parse_recommendation_template(raw: dict) -> RecommendationTemplate:
    """Parseia um template de recomendação individual.

    Args:
        raw: Dicionário com id, template e examples.

    Returns:
        RecommendationTemplate instanciado.
    """
    return RecommendationTemplate(
        id=str(raw.get("id", "")),
        template=str(raw.get("template", "")),
        examples=[str(e) for e in raw.get("examples", [])],
    )


def _parse_timeframe_definition(raw: dict) -> TimeframeDefinition:
    """Parseia uma definição de horizonte temporal.

    Args:
        raw: Dicionário com label, horizon_days e description.

    Returns:
        TimeframeDefinition instanciado.
    """
    return TimeframeDefinition(
        label=str(raw.get("label", "")),
        horizon_days=int(raw.get("horizon_days", 0)),
        description=str(raw.get("description", "")),
    )


def _parse_success_criterion(raw: dict) -> SuccessCriterion:
    """Parseia um critério de sucesso por categoria.

    Args:
        raw: Dicionário com label e criteria.

    Returns:
        SuccessCriterion instanciado.
    """
    return SuccessCriterion(
        label=str(raw.get("label", "")),
        criteria=[str(c) for c in raw.get("criteria", [])],
    )


def _validate_plano_rules(rules: PlanoRules) -> None:
    """Valida a estrutura de um PlanoRules carregado.

    Args:
        rules: PlanoRules já instanciado para validar.

    Raises:
        PlanoRulesValidationError: Se a estrutura for inválida.
    """
    if not rules.card_actions:
        raise PlanoRulesValidationError("plano_rules.json sem card_actions")

    for theme, theme_actions in rules.card_actions.items():
        if not theme_actions.card_ids:
            raise PlanoRulesValidationError(
                f"Tema '{theme}' sem card_ids definidos"
            )

    required_timeframes = {"immediate", "this_week", "this_month"}
    for tf in required_timeframes:
        if tf not in rules.timeframes:
            raise PlanoRulesValidationError(
                f"timeframes: horizonte '{tf}' não definido"
            )


# ----------------------------------------------------------------------
# Gerador de recomendações práticas
# ----------------------------------------------------------------------


def _build_action(
    template: ActionTemplate,
    symbol: CiganoSymbol,
    urgency: str = "medium",
) -> str:
    """Constrói uma ação formatada a partir de um template.

    Args:
        template: Template de ação a ser preenchido.
        symbol: Símbolo que originou a ação.
        urgency: Nível de urgência atual.

    Returns:
        String com ação formatada.
    """
    # Substituições básicas com base no símbolo
    replacements = {
        "acao": symbol.advice if symbol.advice else "avalie esta situação",
        "foco": symbol.theme,
        "tema": symbol.theme,
        "assunto": symbol.interpretation[:50] if symbol.interpretation else "a situação",
        "pessoa": "quem está envolvido",
        "sentimento": "seus sentimentos",
        "tempo": "15 minutos",
        "recurso": "fontes confiáveis",
        "situacao": "a situação atual",
        "periodo": "este mês",
        "objetivo": "sua estabilidade",
        "area": symbol.theme,
        "projeto": "o projeto em questão",
        "mudanca": "a mudança identificada",
        "proposito": "fortalecer vínculos",
        "aspecto": "organização",
    }

    action_text = template.template
    for key, value in replacements.items():
        action_text = action_text.replace(f"{{{key}}}", value)

    # Adicionar indicação de urgência se aplicável
    if urgency == "high":
        action_text = f"[URGENTE] {action_text}"
    elif urgency == "low":
        action_text = f"[LONGO PRAZO] {action_text}"

    return action_text


def _determine_urgency(
    symbols: list[CiganoSymbol],
    risks: list[str],
    rules: PlanoRules,
) -> str:
    """Determina o nível de urgência baseado em símbolos e riscos.

    Args:
        symbols: Lista de símbolos presentes na análise.
        risks: Lista de riscos identificados.
        rules: Regras carregadas com configurações de urgência.

    Returns:
        Nível de urgência ("low", "medium", "high").
    """
    escalation = rules.urgency_escalation

    # Verificar se há cartas de perigo
    danger_ids = set(escalation.danger_cards)
    for symbol in symbols:
        if symbol.id in danger_ids:
            return "high"

    # Verificar palavras-chave de perigo nos riscos
    risk_text = " ".join(risks).lower()
    for keyword in escalation.danger_keywords:
        if keyword.lower() in risk_text:
            return "medium"

    return escalation.default_level


def generate_recommendations(
    symbols: list[CiganoSymbol],
    themes: list[str],
    risks: list[str],
) -> str:
    """Gera recomendações práticas de ação com base na análise simbólica.

    Usa as regras configuradas em data/plano_rules.json para gerar
    ações contextuais com prazos e critérios de sucesso.

    Args:
        symbols: Lista de símbolos predominantes do Baralho Cigano.
        themes: Lista de temas predominantes identificados.
        risks: Lista de riscos identificados.

    Returns:
        String com recomendações estruturadas em Markdown.
    """
    import re

    lines: list[str] = []

    # Se não há símbolos, retornar mensagem genérica
    if not symbols:
        lines.append("- Aprofundar a análise com mais contexto para gerar recomendações.")
        return "\n".join(lines)

    # Carregar regras
    try:
        rules = load_plano_rules()
    except (FileNotFoundError, PlanoRulesValidationError) as e:
        logger.warning("Não foi possível carregar regras: %s — usando fallback", e)
        # Fallback: usar advise do símbolo principal
        top = symbols[0]
        lines.append(f"**Foco principal ({top.name})**: {top.advice}")
        return "\n".join(lines)

    # Determinar urgência
    urgency = _determine_urgency(symbols, risks, rules)

    # Foco principal
    top_symbol = symbols[0]
    lines.append(f"**Foco principal ({top_symbol.name})**: {top_symbol.advice}")
    lines.append("")

    # Atenção temática
    if themes:
        theme = themes[0]
        if theme in rules.card_actions:
            theme_actions = rules.card_actions[theme]
            lines.append(f"**Atenção ao tema {theme}**: {theme_actions.description}")
            lines.append("")
    else:
        # Usar tema do símbolo principal
        theme = top_symbol.theme
        if theme in rules.card_actions:
            theme_actions = rules.card_actions[theme]
            lines.append(f"**Atenção ao tema {theme}**: {theme_actions.description}")
            lines.append("")

    # Cuidados necessários
    if risks:
        lines.append("**Cuidados necessários**:")
        for risk in risks[:3]:
            # Extrair texto após separador
            parts = re.split(r"—|-|\*", risk, maxsplit=1)
            risk_text = parts[-1].strip() if len(parts) > 1 else risk.strip()
            # Remover emoji inicial se houver
            risk_text = re.sub(r"^[\U0001F3FB-\U0001F3FF]\s*", "", risk_text)
            lines.append(f"- {risk_text}")
        lines.append("")

    # Ações práticas por tema
    actions_generated: list[str] = []
    themes_processed: set[str] = set()

    # Processar tema principal
    for theme in themes:
        if theme in themes_processed:
            continue
        themes_processed.add(theme)

        if theme in rules.card_actions:
            theme_actions = rules.card_actions[theme]
            for action_template in theme_actions.action_templates[:2]:
                action_text = _build_action(action_template, top_symbol, urgency)
                actions_generated.append(action_text)

    # Próximos passos baseados em símbolos restantes
    if len(symbols) > 1:
        lines.append("**Próximos passos**:")
        for symbol in symbols[1:4]:
            action_map = {
                "cigano": "Converse com alguém de perspectiva diferente.",
                "trevo": "Mantenha-se alerta a oportunidades inesperadas.",
                "navio": "Considere uma mudança de cenário.",
                "casa": "Cuide do seu ambiente e base.",
                "árvore": "Invista em crescimento sustentável.",
                "nuvens": "Aguarde clareza antes de decidir.",
                "cobra": "Avalie quem está ao seu redor com cuidado.",
                "caixão": "Permita que ciclos se encerrem.",
                "buquê": "Celebre conquistas, pequenas ou grandes.",
                "forca": "Mude sua perspectiva sobre a situação.",
                "serpente": "Busque conhecimento profundo.",
                "morte": "Permita que transformações ocorram.",
                "cegonha": "Prepare-se para receber algo novo.",
                "cão": "Valorize seus aliados leais.",
                "lobo": "Identifique ameaças e aja com firmeza.",
                "cabana": "Busque acolhimento e simplicidade.",
                "estrela": "Mantenha esperança e clareza.",
                "coruja": "Observe mais, fale menos.",
                "lua": "Confie na sua intuição.",
                "machado": "Avalie o que precisa ser cortado.",
                "facho": "Use sua energia para iluminar.",
                "cruz": "Peça apoio se precisar.",
                "cruz de são andré": "Escolha com consciência — ambas direções têm peso.",
                "urso": "Busque proteção e cuidado.",
                "estrelas": "Explore diferentes possibilidades.",
                "mercado": "Negocie com vantagem.",
                "beijo": "Exprima afeto e busque reconciliação.",
                "livro": "Busque conhecimento e informação.",
                "carta": "Fique atento a mensagens importantes.",
                "florista": "Cultive com paciência e cuidado.",
                "anel": "Avalie compromissos com seriedade.",
                "pompom": "Preste atenção a intermediários.",
                "peixe": "Siga sua intuição para prosperidade.",
                "âncora": "Consolide o que já tem.",
                "flecha": "Defina sua direção com precisão.",
                "cafezinho": "Reserve tempo para convívio social.",
            }
            step = action_map.get(symbol.name.lower())
            if step:
                if urgency == "high":
                    step = f"[URGENTE] {step}"
                lines.append(f"- {step}")

    # Se não gerou ações, usar fallback
    if not actions_generated and not any(lines):
        lines.append("**Próximos passos**:")
        lines.append("- Aguarde mais informações para detalhamento.")
    elif actions_generated:
        lines.append("**Ações sugeridas**:")
        for action in actions_generated[:3]:
            lines.append(f"- {action}")

    result = "\n".join(lines)
    logger.debug("Recomendações geradas: %d símbolos → %d linhas", len(symbols), len(lines))
    return result


def _is_danger_card(symbol: CiganoSymbol) -> bool:
    """Verifica se um símbolo é uma carta de perigo.

    Args:
        symbol: Símbolo CiganoSymbol a verificar.

    Returns:
        True se o símbolo for uma carta perigosa, False caso contrário.
    """
    try:
        rules = load_plano_rules()
        return symbol.id in rules.urgency_escalation.danger_cards
    except (FileNotFoundError, PlanoRulesValidationError):
        # Fallback: listas hardcoded baseadas no perigo comum do Baralho Cigano
        fallback_danger_ids = {7, 8, 12, 15, 20, 22}
        return symbol.id in fallback_danger_ids


def load_plano_rules() -> PlanoRules:
    """Carrega e valida as regras do plano prático de data/plano_rules.json.

    Returns:
        PlanoRules com todas as estruturas parseadas e validadas.

    Raises:
        PlanoRulesValidationError: Se a validação falhar.
    """
    # Tenta encontrar o arquivo no pacote data/
    import os

    data_dir = Path(__file__).parent / "data"
    json_path = data_dir / "plano_rules.json"

    if not json_path.exists():
        raise FileNotFoundError(
            f"plano_rules.json não encontrado em {json_path}"
        )

    raw = _load_raw_json(json_path)

    # Parseia card_actions
    card_actions_raw = raw.get("card_actions", {})
    card_actions: dict[str, ThemeActions] = {}
    for theme, theme_raw in card_actions_raw.items():
        card_actions[theme] = _parse_theme_actions(theme, theme_raw)

    # Parseia urgency_escalation
    urgency_raw = raw.get("urgency_escalation", {})
    urgency_escalation = _parse_urgency_escalation(urgency_raw)

    # Parseia recommendation_templates
    rec_templates_raw = raw.get("recommendation_templates", {})
    rec_templates = [
        _parse_recommendation_template(t)
        for t in rec_templates_raw.get("templates", [])
    ]

    # Parseia timeframes
    timeframes_raw = raw.get("timeframes", {})
    timeframes_defs_raw = timeframes_raw.get("definitions", {})
    timeframes = {
        k: _parse_timeframe_definition(v) for k, v in timeframes_defs_raw.items()
    }

    # Parseia success_criteria
    success_raw = raw.get("success_criteria", {})
    success_categories_raw = success_raw.get("categories", {})
    success_criteria = {
        k: _parse_success_criterion(v) for k, v in success_categories_raw.items()
    }

    # Monta o objeto completo
    rules = PlanoRules(
        card_actions=card_actions,
        urgency_escalation=urgency_escalation,
        recommendation_templates=rec_templates,
        timeframes=timeframes,
        success_criteria=success_criteria,
    )

    _validate_plano_rules(rules)

    return rules


