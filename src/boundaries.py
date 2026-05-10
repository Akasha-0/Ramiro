"""Guardrails éticos — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por:
- Definir palavras-chave bloqueadas ( BLOCKED_KEYWORDS )
- Validar output contra afirmações deterministas ( validate_output )
- Injetar disclaimer ético quando necessário ( inject_disclaimer )

O BoundariesValidator é chamado entre analysis_engine.py e report_generator.py.
"""

import logging
import re
from typing import Optional

from src.types import AnalysisResult, ValidatedOutput

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Mensagens de erro detalhadas em português com orientação de ação
# ----------------------------------------------------------------------

# Mensagens por categoria de erro (fornecem contexto e orientação)
VALIDATION_MESSAGES: dict[str, dict[str, str]] = {
    "blocked_keyword": {
        "title": "⚠️ Conteúdo Bloqueado pelos Guardrails Éticos",
        "message": (
            "O relatório contém palavras ou frases que violam nossas "
            "diretrizes éticas e não podem ser exibidas."
        ),
        "action": (
            "O sistema gerou automaticamente um aviso ético. "
            "Analise o conteúdo com perspectiva reflexiva, não determinista."
        ),
        "recovery": (
            "Dica: Reformule sua pergunta para focar em reflexão e organização "
            "em vez de previsões específicas."
        ),
    },
    "multiple_flags": {
        "title": "⚠️ Múltiplas Restrições Detectadas",
        "message": (
            "Várias palavras-chave restritas foram identificadas no relatório. "
            "O conteúdo foi sinalizado para revisão ética."
        ),
        "action": (
            "Um aviso ético foi adicionado automaticamente. "
            "Use o relatório como ferramenta de reflexão, não de previsão."
        ),
        "recovery": (
            "Dica: Tente perguntas mais abertas como 'como posso refletir sobre...' "
            "em vez de 'o que vai acontecer com...'"
        ),
    },
    "disclaimer_injected": {
        "title": "ℹ️ Aviso Ético Adicionado",
        "message": (
            "Um aviso ético foi inserido automaticamente no final do relatório."
        ),
        "action": (
            "Este aviso garante que a análise seja usada como ferramenta "
            "de reflexão, não como verdade absoluta."
        ),
        "recovery": None,
    },
    "empty_report": {
        "title": "ℹ️ Relatório Vazio",
        "message": (
            "Não foi possível processar o relatório ou ele está vazio."
        ),
        "action": (
            "Verifique se o texto de entrada contém informações suficientes "
            "para análise."
        ),
        "recovery": (
            "Dica: Forneça uma descrição mais detalhada do contexto ou "
            "escolha símbolos específicos do Baralho Cigano."
        ),
    },
}

# Códigos de erro para identificação programática
ERROR_CODES: dict[str, str] = {
    "ETH001": "Palavra-chave bloqueada detectada",
    "ETH002": "Múltiplas restrições identificadas",
    "ETH003": "Disclaimer ético injetado",
    "ETH004": "Relatório vazio ou inválido",
    "ETH005": "Validação concluída - conteúdo seguro",
}

# ----------------------------------------------------------------------
# Palavras-chave bloqueadas (case-insensitive, normalização aplicada)
# ----------------------------------------------------------------------

# Categorias de risco:
# - deterministic_prediction: previsões sobre morte, destino, futuro fixo
# - spiritual_authority:claims de poder sobre entidades/espiritualidade
# - health_advice: orientações que substituem acompanhamento médico
# - financial_guarantee: garantias financeiras sem base factual

BLOCKED_KEYWORDS: list[str] = [
    # Predição determinista — morte, saúde, destino
    "morte",
    "morrer",
    "morre",
    "fatal",
    "terminal",
    "doença terminal",
    "destino fixo",
    "destino determinado",
    "profecia",
    "você vai morrer",
    "você vai ficar doente",
    "prevendo sua morte",
    "data da sua morte",
    "quando vai morrer",
    # Entidades espirituais e práticas mágicas
    "obsessor",
    "atar",
    "mal olhado",
    "poderes mágicos",
    "cura espiritual",
    "feitiço",
    "macumba",
    "guerra espiritual",
    "demônio",
    "exorcismo",
    "entity attached",
    "entity attachment",
    "spiritual entity",
    "curse removal",
    "curse",
    # Autoridade espiritual indevida
    "médium",
    "canal spiritual",
    "eu sou seu guia",
    "eu sou seu anjo",
    "sua alma é minha",
    # Afirmações deterministas
    "certamente vai",
    "com certeza vai",
    "garantia de",
    "isso vai acontecer",
    "isso vai ocorrer",
    "inevitável",
]

# Padrão regex pré-compilado para busca case-insensitive
# Cada keyword é escapada para безопасность em regex
_BLOCKED_PATTERN: re.Pattern[str] = re.compile(
    "|".join(re.escape(kw.lower()) for kw in BLOCKED_KEYWORDS),
    re.IGNORECASE,
)

# Disclaimer ético padrão (inserido quando needs_disclaimer=True)
_ETHICAL_DISCLAIMER: str = """
---

**Aviso Ético:** Esta análise é uma ferramenta de organização e reflexão,
não constitui previsão determinista. Não substitui orientação profissional
de saúde, jurídica ou financeira. Se você estiver em sofrimento, procure
ajuda especializada.
"""


# ----------------------------------------------------------------------
# Validação de output
# ----------------------------------------------------------------------


def validate_output(text: str) -> tuple[bool, list[str], Optional[dict[str, str]]]:
    """Valida texto do relatório contra guardrails éticos.

    Detecta palavras-chave bloqueadas que indicam:
    - Afirmações deterministas (morte, destino, profecia)
    - Práticas espirituais potencialmente nocivas
    - Autoridade espiritual indevida

    A busca é case-insensitive e normaliza caracteres especiais
    (acentos, cedilha) para evitar bypass por variação ortográfica.

    Args:
        text: Texto do relatório a validar.

    Returns:
        Tupla (is_valid, flags, error_message) onde:
        - is_valid: True se nenhuma keyword bloqueada foi encontrada
        - flags: Lista de keywords detectadas (vazia se safe)
        - error_message: Mensagem detalhada em português se bloqueado (None se válido)

    Examples:
        >>> is_valid, flags, _ = validate_output("Texto normal sobre trabalho")
        >>> assert is_valid == True
        >>> assert flags == []

        >>> is_valid, flags, msg = validate_output("Isso indica morte iminente")
        >>> assert is_valid == False
        >>> assert "morte" in flags
        >>> assert msg is not None
    """
    if not text:
        return (True, [], None)

    # Normalizar: lowercase + remover acentos para comparação robusta
    normalized = _normalize_text(text)

    flags: list[str] = []
    for keyword in BLOCKED_KEYWORDS:
        kw_normalized = _normalize_text(keyword)
        if kw_normalized in normalized:
            flags.append(keyword)
            logger.debug(
                "Keyword bloqueada detectada: %r em texto de %d chars",
                keyword,
                len(text),
            )

    is_valid = len(flags) == 0

    if not is_valid:
        logger.warning(
            "Output bloqueado por guardrails: %d keywords detectadas",
            len(flags),
        )
        # Construir mensagem de erro detalhada em português
        if len(flags) == 1:
            error_msg = _build_blocked_keyword_message(flags[0])
        else:
            error_msg = _build_multiple_flags_message(flags)
    else:
        error_msg = None

    return (is_valid, flags, error_msg)


def _normalize_text(text: str) -> str:
    """Normaliza texto para comparação case-insensitive e sem acentos.

    Args:
        text: Texto a normalizar.

    Returns:
        Texto em lowercase com acentos/cedilha substituídos por equivalente ASCII.
    """
    import unicodedata

    # NFD decompõe caracteres com acento em base + combining marks
    # encode('ascii', 'ignore') remove os combining marks
    normalized = unicodedata.normalize("NFD", text.lower())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text


def _build_blocked_keyword_message(keyword: str) -> dict[str, str]:
    """Constrói mensagem de erro detalhada para uma keyword bloqueada.

    Args:
        keyword: A palavra-chave bloqueada detectada.

    Returns:
        Dicionário com título, mensagem, ação e recuperação.
    """
    templates = VALIDATION_MESSAGES["blocked_keyword"].copy()
    templates["detail"] = f"Palavra detectada: '{keyword}'"
    templates["code"] = ERROR_CODES["ETH001"]
    return templates


def _build_multiple_flags_message(flags: list[str]) -> dict[str, str]:
    """Constrói mensagem de erro para múltiplas keywords bloqueadas.

    Args:
        flags: Lista de palavras-chave bloqueadas detectadas.

    Returns:
        Dicionário com título, mensagem, ação e recuperação.
    """
    templates = VALIDATION_MESSAGES["multiple_flags"].copy()
    templates["detail"] = f"Palavras detectadas: {', '.join(flags[:5])}"
    if len(flags) > 5:
        templates["detail"] += f" (e mais {len(flags) - 5} outras)"
    templates["code"] = ERROR_CODES["ETH002"]
    return templates


# ----------------------------------------------------------------------
# Injeção de disclaimer ético
# ----------------------------------------------------------------------


def inject_disclaimer(report_md: str) -> str:
    """Insere disclaimer ético no relatório Markdown.

    O disclaimer é inserido ao final do relatório quando o parâmetro
    needs_disclaimer é True. O texto segue o formato Markdown e
    é separado do conteúdo por uma regra horizontal (---).

    Args:
        report_md: Conteúdo do relatório em Markdown.

    Returns:
        Relatório com disclaimer ético appended, ou texto original
        se o relatório estiver vazio.

    Examples:
        >>> result = inject_disclaimer("# Relatório\\n\\nConteúdo do relatório")
        >>> assert "Aviso Ético" in result
        >>> assert result.endswith(_ETHICAL_DISCLAIMER.strip())
    """
    if not report_md or not report_md.strip():
        logger.debug("inject_disclaimer: relatório vazio, retornando original")
        return report_md

    # Remover múltiplos newlines finais para append limpo
    trimmed = report_md.rstrip()

    result = trimmed + _ETHICAL_DISCLAIMER

    logger.debug(
        "Disclaimer ético injetado em relatório de %d chars",
        len(report_md),
    )

    return result


# ----------------------------------------------------------------------
# Ativador completo (valida + injeta se necessário)
# ----------------------------------------------------------------------


def apply_guardrails(
    report_md: str,
    analysis_result: Optional[AnalysisResult] = None,
) -> ValidatedOutput:
    """Aplica guardrails completos: validação + injeção de disclaimer.

    Este é o ponto de entrada principal para o pipeline.
    Recebe o relatório gerado e aplica:
    1. Validação contra keywords bloqueadas
    2. Injeção de disclaimer se necessário

    Args:
        report_md: Conteúdo do relatório em Markdown.
        analysis_result: AnalysisResult opcional para contexto adicional.

    Returns:
        ValidatedOutput com content (possivelmente modificado),
        disclaimer_flags, needs_disclaimer e is_safe.

    Examples:
        >>> result = apply_guardrails("# Relatório\\n\\nTexto normal")
        >>> assert result.is_safe == True
        >>> assert result.needs_disclaimer == False

        >>> result = apply_guardrails("# Relatório\\n\\nTexto com morte iminente")
        >>> assert result.is_safe == False
        >>> assert result.needs_disclaimer == True
    """
    logger.info("Aplicando guardrails éticos a relatório de %d chars", len(report_md))

    # Validar (agora com mensagem de erro detalhada)
    is_safe, flags, error_msg = validate_output(report_md)
    needs_disclaimer = not is_safe

    # Injetar disclaimer se necessário
    final_content = inject_disclaimer(report_md) if needs_disclaimer else report_md

    output = ValidatedOutput(
        content=final_content,
        disclaimer_flags=flags,
        needs_disclaimer=needs_disclaimer,
        is_safe=is_safe,
    )

    logger.info(
        "Guardrails aplicados: safe=%s, flags=%s, disclaimer=%s",
        is_safe,
        flags,
        needs_disclaimer,
    )

    return output


# ----------------------------------------------------------------------
# Validador de boundaries (classe — padrão opcional)
# ----------------------------------------------------------------------


class BoundariesValidator:
    """Validador de guardrails éticos com configuração customizável.

    Permite configurar palavras-chave adicionais ou desativar
    palavras específicas via __init__.

    Attributes:
        extra_blocked: Lista de keywords adicionais a bloquear.
        disabled_keywords: Keywords de BLOCKED_KEYWORDS a desativar.
    """

    def __init__(
        self,
        extra_blocked: Optional[list[str]] = None,
        disabled_keywords: Optional[list[str]] = None,
    ) -> None:
        self._extra_blocked = extra_blocked or []
        self._disabled = set(disabled_keywords or [])
        self._all_blocked = BLOCKED_KEYWORDS + self._extra_blocked

        # Compilar padrão com todas as keywords ativas
        self._pattern = re.compile(
            "|".join(re.escape(kw.lower()) for kw in self._all_blocked),
            re.IGNORECASE,
        )

        logger.debug(
            "BoundariesValidator inicializado: %d keywords ativas",
            len(self._all_blocked),
        )

    def validate(self, text: str) -> tuple[bool, list[str], Optional[dict[str, str]]]:
        """Valida texto usando configuração customizada.

        Args:
            text: Texto a validar.

        Returns:
            Tupla (is_valid, flags, error_msg) com keywords bloqueadas detectadas
            e mensagem de erro detalhada em português.
        """
        if not text:
            return (True, [], None)

        normalized = _normalize_text(text)

        flags: list[str] = []
        for keyword in self._all_blocked:
            if keyword in self._disabled:
                continue
            kw_norm = _normalize_text(keyword)
            if kw_norm in normalized:
                flags.append(keyword)

        is_valid = len(flags) == 0

        if not is_valid:
            if len(flags) == 1:
                error_msg = _build_blocked_keyword_message(flags[0])
            else:
                error_msg = _build_multiple_flags_message(flags)
        else:
            error_msg = None

        return (is_valid, flags, error_msg)

    def inject(self, report_md: str) -> str:
        """Injeta disclaimer ético (mesmo comportamento de inject_disclaimer).

        Args:
            report_md: Conteúdo do relatório.

        Returns:
            Relatório com disclaimer appended.
        """
        return inject_disclaimer(report_md)

    def apply(self, report_md: str) -> ValidatedOutput:
        """Aplica validação e injeção usando configuração customizada.

        Args:
            report_md: Conteúdo do relatório.

        Returns:
            ValidatedOutput com content, flags e status.
        """
        is_safe, flags, _ = self.validate(report_md)
        needs_disclaimer = not is_safe
        final_content = self.inject(report_md) if needs_disclaimer else report_md

        return ValidatedOutput(
            content=final_content,
            disclaimer_flags=flags,
            needs_disclaimer=needs_disclaimer,
            is_safe=is_safe,
        )