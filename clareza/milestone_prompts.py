"""Gerador de prompts de reflexão guiada — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por gerar prompts de milestone para sessões de reflexão guiada.
Quando o usuário revisita uma sessão passada, o sistema superfíce prompts que
incentivam a reflexão sobre mudanças e evolução pessoal.

Princípios:
- Suporte e não-judgement: linguagem acolhedora e encorajadora
- Não-determinismo: reconhece que situações mudam com o tempo
- Reforço de crescimento: usa prompts para ativamente engajar o usuário
  em seu desenvolvimento pessoal

Recebe dados da sessão (tipos de src/types.py) e retorna prompts estruturados
em português brasileiro.
"""

import logging
from typing import Optional

from clareza.types import Session

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Templates de prompts de milestone (suporte, não-judgement)
# ----------------------------------------------------------------------

MILESTONE_PROMPT_TEMPLATE = """🌱 **Hora de Reflexão**

Olá! Você está revisitando uma sessão anterior sobre **{topic}**.

_Como está sua situação desde esta leitura?_ O tempo passou, você talvez tenha
vivido novas experiências, e as coisas podem ter mudado. Este é um momento para
observar como você se sente agora — sem pressões ou julgamentos.

Sua reflexão: """

FOLLOW_UP_TEMPLATES = {
    "trabalho": [
        "Como você tem se sentido em relação ao trabalho ultimamente?",
        "Alguma mudança significativa aconteceu na sua vida profissional desde então?",
        "Você conseguiu colocar em prática alguma das sugestões da leitura anterior?",
    ],
    "relação": [
        "Como está a situação relacional que você trouxe na última vez?",
        "Houve algum desenvolvimento novo no seus relacionamentos?",
        "Você conseguiu ter mais clareza sobre algum aspecto da relação?",
    ],
    "saúde": [
        "Como você está se sentindo em termos de bem-estar?",
        "Alguma mudança aconteceu na sua rotina de cuidado pessoal?",
        "Você tem dado mais atenção à sua saúde desde a última leitura?",
    ],
    "espiritual": [
        "Como você tem se sentido em termos de conexão interior?",
        "Alguma prática espiritual ou de autoconhecimento foi explorada?",
        "Você percebeu algum crescimento no seu caminho espiritual?",
    ],
    "dinheiro": [
        "Como está a situação financeira desde a última análise?",
        "Alguma decisão importante foi tomada em relação a dinheiro?",
        "Você sente mais clareza ou ainda há dúvidas sobre o aspecto financeiro?",
    ],
    "viagem": [
        "Alguma viagem ou mudança de cenário aconteceu?",
        "Como foi essa experiência de expansão de horizontes?",
        "Você descobriu algo novo sobre si mesmo através de mudanças?",
    ],
    "família": [
        "Como está o ambiente familiar desde a última vez?",
        "Alguma situação familiar evoluiu ou se transformou?",
        "Você conseguiu fortalecer os vínculos com pessoas próximas?",
    ],
}

FOLLOW_UP_GENERIC = [
    "Como você tem se sentido em relação a isso ultimamente?",
    "Algo mudou na sua perspectiva desde a última leitura?",
    "Você conseguiu aplicar alguma reflexão da análise anterior?",
    "Há algum aspecto que ainda gera dúvidas ou curiosidade?",
]

SKIP_MESSAGE = "Tudo bem! Sem pressões — você pode refletir quando sentir que é o momento certo. 🙏"

SKIP_CONFIRMATION = "Ok, pulamos esta reflexão. Volte quando quiser continuar sua jornada de autoconhecimento."

# ----------------------------------------------------------------------
# Gerador de prompts de milestone
# ----------------------------------------------------------------------


class MilestonePromptGenerator:
    """Gerador de prompts de reflexão guiada para milestones de sessão.

    Gera prompts que incentivam o usuário a refletir sobre mudanças desde
    a última análise, reforçando a filosofia não-determinista do sistema.

    Attributes:
        include_follow_ups: Se True, inclui perguntas de acompanhamento opcionais.
        language: Idioma dos prompts (default: "pt-BR").
    """

    def __init__(self, include_follow_ups: bool = True, language: str = "pt-BR") -> None:
        self.include_follow_ups = include_follow_ups
        self.language = language
        logger.debug(
            "MilestonePromptGenerator inicializado, follow-ups=%s, lang=%s",
            include_follow_ups,
            language,
        )

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generate_milestone_prompt(
        self,
        session: Optional[Session] = None,
        theme_hint: Optional[str] = None,
    ) -> str:
        """Gera o prompt de milestone principal para reflexão.

        O prompt é acolhedor, encoraja reflexão sem pressão, e reconhece
        que o tempo traz mudanças — princípio central do não-determinismo.

        Args:
            session: Sessão opcional para contexto (fornece tema automaticamente).
            theme_hint: Tema opcional explícito (sobrescreve session.themes).

        Returns:
            String com o prompt de milestone formatado em Markdown.
        """
        # Determinar tema para personalização
        topic = self._extract_topic(session, theme_hint)

        prompt = MILESTONE_PROMPT_TEMPLATE.format(topic=topic)

        logger.info(
            "Prompt de milestone gerado para tema: %s",
            topic,
        )

        return prompt

    def follow_up_questions(
        self,
        themes: Optional[list[str]] = None,
        count: int = 2,
    ) -> list[str]:
        """Gera perguntas de acompanhamento opcionais baseadas nos temas.

        As perguntas são selecionadas aleatoriamente dos templates por tema,
        proporcionando variety e não-determinismo na experiência.

        Args:
            themes: Lista de temas da sessão (opcional).
            count: Número de perguntas a gerar (default 2).

        Returns:
            Lista de perguntas de acompanhamento formatadas.
        """
        if not themes:
            # Fallback para perguntas genéricas
            import random

            selected = random.sample(FOLLOW_UP_GENERIC, min(count, len(FOLLOW_UP_GENERIC)))
            logger.debug("Follow-ups genéricos selecionados: %d", len(selected))
            return selected

        # Coletar perguntas por tema
        all_questions: list[str] = []
        for theme in themes:
            theme_lower = theme.lower().strip()
            if theme_lower in FOLLOW_UP_TEMPLATES:
                all_questions.extend(FOLLOW_UP_TEMPLATES[theme_lower])

        if not all_questions:
            # Nenhum tema encontrado, usar genéricos
            import random

            selected = random.sample(FOLLOW_UP_GENERIC, min(count, len(FOLLOW_UP_GENERIC)))
            logger.debug("Follow-ups genéricos (temas não encontrados): %d", len(selected))
            return selected

        # Selecionar aleatoriamente para não-determinismo
        import random

        selected = random.sample(all_questions, min(count, len(all_questions)))
        logger.debug("Follow-ups por tema selecionados: %d", len(selected))

        return selected

    def skip_prompt(self) -> str:
        """Retorna mensagem para quando o usuário escolhe pular o prompt.

        A mensagem é acolhedora e não-pressiva, mantendo o tom de suporte
        mesmo quando o usuário opta por não fazer a reflexão.

        Returns:
            String com mensagem de skip formatada.
        """
        logger.debug("Prompt de skip retornado")
        return SKIP_CONFIRMATION

    def format_follow_up_section(self, questions: list[str]) -> str:
        """Formata uma seção de perguntas de acompanhamento.

        Args:
            questions: Lista de perguntas a formatar.

        Returns:
            String formatada com as perguntas em formato Markdown.
        """
        if not questions:
            return ""

        lines = ["\n---\n**Perguntas para aprofundar (opcional):**\n"]
        for i, q in enumerate(questions, start=1):
            lines.append(f"{i}. {q}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Utilitários internos
    # ------------------------------------------------------------------

    def _extract_topic(
        self,
        session: Optional[Session],
        theme_hint: Optional[str],
    ) -> str:
        """Extrai o tema principal para personalização do prompt.

        Args:
            session: Sessão opcional.
            theme_hint: Tema explícito opcional.

        Returns:
            String com tema formatado para display.
        """
        if theme_hint:
            return theme_hint

        if session and session.analysis_result and session.analysis_result.themes:
            # Usar o primeiro tema da sessão
            return session.analysis_result.themes[0]

        # Tema genérico quando não há contexto
        return "sua jornada"

    def _get_timestamp(self) -> str:
        """Retorna timestamp formatado para logs."""
        from datetime import datetime

        return datetime.now().strftime("%d/%m/%Y às %H:%M")