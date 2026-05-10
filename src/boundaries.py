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

from src.types import AnalysisResult, InputGuardrailsResult, ValidatedOutput

logger = logging.getLogger(__name__)

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

# ----------------------------------------------------------------------
# Palavras-chave sensíveis para scan de input (case-insensitive)
# ----------------------------------------------------------------------

# Categorias de risco para detecção de input sensível:
# - mental_health: depressão, ansiedade, ideação suicida
# - physical_health: doença, diagnóstico, tratamento médico
# - financial_risk: dívida, falência, perda financeira grave
# - relationship_crisis: separação, divórcio, traição, abuso
# - self_harm: automutilação, ideação de morte

SENSITIVE_KEYWORDS: list[str] = [
    # Saúde mental — depressão, ansiedade, ideação suicida
    "depressão",
    "depressivo",
    "deprimido",
    "ansiedade",
    "ansioso",
    "suicídio",
    "suicidio",
    "ideação suicida",
    "pensamentos de morte",
    "matar a si mesmo",
    "automutilação",
    "corte",
    "ferir a si mesmo",
    "crise de pânico",
    "ataque de pânico",
    "transtorno",
    "psicose",
    "psicótico",
    "internação",
    "hospitalização",
    # Saúde física — doença grave, diagnóstico
    "câncer",
    "tumor",
    "diagnóstico grave",
    "doença crônica",
    "terminal",
    "HIV",
    "AIDS",
    "enfermidade",
    # Risco financeiro — endividamento, falência
    "falência",
    "falência pessoal",
    "dívida insustentável",
    "não tenho dinheiro",
    "sem dinheiro",
    "não consigo pagar",
    "ruína financeira",
    "perdi tudo",
    "sem recursos",
    # Crise relacional — separação, abuso, traição
    "separação",
    "divórcio",
    "traição",
    "infidelidade",
    "abuso",
    "violência doméstica",
    "abuso emocional",
    "abuso físico",
    "relação tóxica",
    "manipulação",
    "controle",
    # Risco auto-lesivo
    "automutilação",
    "ferir-se",
    "cortar-se",
]

# Padrão regex pré-compilado para busca case-insensitive
# Cada keyword é escapada para безопасность em regex
_BLOCKED_PATTERN: re.Pattern[str] = re.compile(
    "|".join(re.escape(kw.lower()) for kw in BLOCKED_KEYWORDS),
    re.IGNORECASE,
)

# Padrão pré-compilado para SENSITIVE_KEYWORDS (mesmo padrão de segurança)
_SENSITIVE_PATTERN: re.Pattern[str] = re.compile(
    "|".join(re.escape(kw.lower()) for kw in SENSITIVE_KEYWORDS),
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# Detecção de input sensível
# ----------------------------------------------------------------------


def detect_sensitive_input(text: str) -> tuple[bool, list[str]]:
    """Detecta temas sensíveis no input do usuário.

    Escaneia o texto de entrada em busca de palavras-chave que indicam
    vulnerabilidade ou risco, incluindo:
    - Saúde mental (depressão, ansiedade, ideação suicida)
    - Saúde física (doença grave, diagnóstico)
    - Risco financeiro (dívida, falência)
    - Crise relacional (separação, abuso)
    - Risco auto-lesivo

    A busca é case-insensitive e normaliza caracteres especiais
    (acentos, cedilha) para evitar bypass por variação ortográfica.

    Args:
        text: Texto de input do usuário a escanear.

    Returns:
        Tupla (is_sensitive, flags) onde:
        - is_sensitive: True se pelo menos uma keyword sensível foi encontrada
        - flags: Lista de keywords sensíveis detectadas (vazia se safe)

    Examples:
        >>> is_sensitive, flags = detect_sensitive_input("texto normal sobre trabalho")
        >>> assert is_sensitive == False
        >>> assert flags == []

        >>> is_sensitive, flags = detect_sensitive_input("estou com depressão e problemas financeiros")
        >>> assert is_sensitive == True
        >>> assert "depressão" in flags
    """
    if not text:
        return (False, [])

    # Normalizar: lowercase + remover acentos para comparação robusta
    normalized = _normalize_text(text)

    flags: list[str] = []
    for keyword in SENSITIVE_KEYWORDS:
        kw_normalized = _normalize_text(keyword)
        if kw_normalized in normalized:
            flags.append(keyword)
            logger.debug(
                "Keyword sensível detectada: %r em input de %d chars",
                keyword,
                len(text),
            )

    is_sensitive = len(flags) > 0

    if is_sensitive:
        logger.info(
            "Input sensível detectado: %d keywords encontradas",
            len(flags),
        )

    return (is_sensitive, flags)


def apply_input_guardrails(text: str) -> InputGuardrailsResult:
    """Aplica guardrails de input e retorna resultado estruturado.

    Wrapper que converte o resultado de detect_sensitive_input
    no dataclass InputGuardrailsResult para uso uniforme no pipeline.

    Args:
        text: Texto de input do usuário a escanear.

    Returns:
        InputGuardrailsResult com is_sensitive e flags.

    Examples:
        >>> result = apply_input_guardrails("texto normal sobre trabalho")
        >>> assert result.is_sensitive == False
        >>> assert result.flags == []

        >>> result = apply_input_guardrails("estou com depressão")
        >>> assert result.is_sensitive == True
        >>> assert "depressão" in result.flags
    """
    is_sensitive, flags = detect_sensitive_input(text)

    return InputGuardrailsResult(
        is_sensitive=is_sensitive,
        flags=flags,
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
# Disclaimer de cabeçalho (posicionamento proeminente no topo)
# ----------------------------------------------------------------------

# Header disclaimer com texto em português e posição proeminente
# Inclui chamada para ajuda especializada em destaque
_HEADER_DISCLAIMER: str = """
---

# ⚠️ AVISO IMPORTANTE — LEIA ANTES DE CONTINUAR

**Esta análise é uma ferramenta de organização e reflexão pessoal.**

- Não constitui previsão determinista ou garantia de resultados
- Não substitui acompanhamento de profissionais de saúde, direito ou finanças
- Simbolismo do Baralho Cigano não possui base científica comprovada

**Se você estiver em sofrimento emocional, procure/ procure ajuda especializada
   e se necessitar de apoio imediato, procure ajuda especializada. Procure
   ou procure ajuda especializada quando necessário. Se já procurou
   ou procured ajuda especializada anteriormente, continue buscando suporte:**

- **CVV** — Centro de Valorização da Vida: 188 (24h, gratuito)
- **CAPS** — Centro de Atenção Psicossocial mais próximo
- **SAMU** — Emergências: 192

---

"""


# ----------------------------------------------------------------------
# Validação de output
# ----------------------------------------------------------------------


def validate_output(text: str) -> tuple[bool, list[str]]:
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
        Tupla (is_valid, flags) onde:
        - is_valid: True se nenhuma keyword bloqueada foi encontrada
        - flags: Lista de keywords detectadas (vazia se safe)

    Examples:
        >>> is_valid, flags = validate_output("Texto normal sobre trabalho")
        >>> assert is_valid == True
        >>> assert flags == []

        >>> is_valid, flags = validate_output("Isso indica morte iminente")
        >>> assert is_valid == False
        >>> assert "morte" in flags
    """
    if not text:
        return (True, [])

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

    return (is_valid, flags)


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


# ----------------------------------------------------------------------
# Injeção de disclaimer ético
# ----------------------------------------------------------------------


def inject_header_disclaimer(report_md: str) -> str:
    """Insere disclaimer de cabeçalho proeminente no início do relatório.

    O header disclaimer é inserido no topo do relatório para alertar
    o usuário sobre limitações antes de ler a análise. Inclui números
    de emergência e recursos de ajuda especializada.

    Args:
        report_md: Conteúdo do relatório em Markdown.

    Returns:
        Relatório com disclaimer de cabeçalho prependido, ou texto original
        se o relatório estiver vazio.

    Examples:
        >>> result = inject_header_disclaimer("# Relatório\\n\\nConteúdo")
        >>> assert "AVISO IMPORTANTE" in result
        >>> assert result.startswith("\\n---")
        >>> assert "CVV" in result
        >>> assert "188" in result
    """
    if not report_md or not report_md.strip():
        logger.debug("inject_header_disclaimer: relatório vazio, retornando original")
        return report_md

    result = _HEADER_DISCLAIMER + report_md

    logger.debug(
        "Header disclaimer injetado em relatório de %d chars",
        len(report_md),
    )

    return result


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

    # Validar
    is_safe, flags = validate_output(report_md)
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

    def validate(self, text: str) -> tuple[bool, list[str]]:
        """Valida texto usando configuração customizada.

        Args:
            text: Texto a validar.

        Returns:
            Tupla (is_valid, flags) com keywords bloqueadas detectadas.
        """
        if not text:
            return (True, [])

        normalized = _normalize_text(text)

        flags: list[str] = []
        for keyword in self._all_blocked:
            if keyword in self._disabled:
                continue
            kw_norm = _normalize_text(keyword)
            if kw_norm in normalized:
                flags.append(keyword)

        return (len(flags) == 0, flags)

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
        is_safe, flags = self.validate(report_md)
        needs_disclaimer = not is_safe
        final_content = self.inject(report_md) if needs_disclaimer else report_md

        return ValidatedOutput(
            content=final_content,
            disclaimer_flags=flags,
            needs_disclaimer=needs_disclaimer,
            is_safe=is_safe,
        )