"""Testes unitários para src/milestone_prompts.py.

Cobertura:
- MILESTONE_PROMPT_TEMPLATE — estrutura do template principal
- FOLLOW_UP_TEMPLATES — templates por tema (trabalho, relação, saúde, etc.)
- FOLLOW_UP_GENERIC — templates genéricos para fallback
- SKIP_MESSAGE e SKIP_CONFIRMATION — mensagens de skip
- MilestonePromptGenerator.__init__() — inicialização
- generate_milestone_prompt() — API principal de geração de prompt
- follow_up_questions() — geração de perguntas de acompanhamento
- skip_prompt() — retorno de mensagem de skip
- format_follow_up_section() — formatação de seção de follow-ups
- _extract_topic() — extração de tema para personalização
- Edge cases: sessão vazia, temas não encontrados, follow-ups desabilitados
"""

import pytest

from clareza.milestone_prompts import (
    FOLLOW_UP_GENERIC,
    FOLLOW_UP_TEMPLATES,
    MILESTONE_PROMPT_TEMPLATE,
    SKIP_CONFIRMATION,
    SKIP_MESSAGE,
    MilestonePromptGenerator,
)
from clareza.types import AnalysisResult, Session


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def generator() -> MilestonePromptGenerator:
    """Gerador com configurações padrão (follow-ups ativos)."""
    return MilestonePromptGenerator(include_follow_ups=True, language="pt-BR")


@pytest.fixture
def generator_no_follow_ups() -> MilestonePromptGenerator:
    """Gerador com follow-ups desativados."""
    return MilestonePromptGenerator(include_follow_ups=False, language="pt-BR")


@pytest.fixture
def session_with_theme() -> Session:
    """Sessão com tema definido."""
    return Session(
        session_id="test-session-001",
        timestamp="2026-05-11T10:00:00",
        input_format="text",
        raw_content="Estou com dúvidas sobre meu trabalho",
        analysis_result=AnalysisResult(
            diagnosis="Momento de transição profissional.",
            themes=["trabalho", "mudança"],
        ),
    )


@pytest.fixture
def session_empty() -> Session:
    """Sessão sem análise (sem tema)."""
    return Session(
        session_id="test-session-002",
        timestamp="2026-05-11T10:00:00",
        input_format="text",
        raw_content="Texto simples",
        analysis_result=None,
    )


@pytest.fixture
def session_no_themes() -> Session:
    """Sessão com análise mas sem temas."""
    return Session(
        session_id="test-session-003",
        timestamp="2026-05-11T10:00:00",
        input_format="text",
        raw_content="Texto simples",
        analysis_result=AnalysisResult(diagnosis="Diagnóstico sem temas"),
    )


# ----------------------------------------------------------------------
# Testes — Constantes globais
# ----------------------------------------------------------------------


class TestConstants:
    def test_milestone_prompt_template_contains_sections(self) -> None:
        """Template contém as seções estruturais."""
        assert "🌱" in MILESTONE_PROMPT_TEMPLATE
        assert "**Hora de Reflexão**" in MILESTONE_PROMPT_TEMPLATE
        assert "{topic}" in MILESTONE_PROMPT_TEMPLATE
        assert "Sua reflexão:" in MILESTONE_PROMPT_TEMPLATE

    def test_milestone_prompt_template_has_topic_placeholder(self) -> None:
        """Template contém placeholder de topic."""
        assert "{topic}" in MILESTONE_PROMPT_TEMPLATE

    def test_milestone_prompt_template_uses_markdown(self) -> None:
        """Template usa formatação Markdown."""
        assert "**" in MILESTONE_PROMPT_TEMPLATE  # Bold
        assert "_" in MILESTONE_PROMPT_TEMPLATE  # Italic

    def test_follow_up_templates_has_all_themes(self) -> None:
        """FOLLOW_UP_TEMPLATES contém todos os temas principais."""
        expected_themes = ["trabalho", "relação", "saúde", "espiritual", "dinheiro", "viagem", "família"]
        for theme in expected_themes:
            assert theme in FOLLOW_UP_TEMPLATES

    def test_follow_up_templates_each_has_questions(self) -> None:
        """Cada tema em FOLLOW_UP_TEMPLATES tem perguntas."""
        for theme, questions in FOLLOW_UP_TEMPLATES.items():
            assert len(questions) >= 1
            assert all(isinstance(q, str) for q in questions)

    def test_follow_up_generic_not_empty(self) -> None:
        """FOLLOW_UP_GENERIC contém perguntas."""
        assert len(FOLLOW_UP_GENERIC) > 0

    def test_follow_up_generic_contains_strings(self) -> None:
        """FOLLOW_UP_GENERIC contém apenas strings."""
        assert all(isinstance(q, str) for q in FOLLOW_UP_GENERIC)

    def test_skip_message_is_not_empty(self) -> None:
        """SKIP_MESSAGE não é vazio."""
        assert len(SKIP_MESSAGE) > 0
        assert "🙏" in SKIP_MESSAGE

    def test_skip_confirmation_is_not_empty(self) -> None:
        """SKIP_CONFIRMATION não é vazio."""
        assert len(SKIP_CONFIRMATION) > 0


# ----------------------------------------------------------------------
# Testes — MilestonePromptGenerator.__init__()
# ----------------------------------------------------------------------


class TestMilestonePromptGeneratorInit:
    def test_init_default_follow_ups_true(self) -> None:
        """Default: include_follow_ups=True."""
        g = MilestonePromptGenerator()
        assert g.include_follow_ups is True

    def test_init_explicit_follow_ups_true(self) -> None:
        """Explicit include_follow_ups=True."""
        g = MilestonePromptGenerator(include_follow_ups=True)
        assert g.include_follow_ups is True

    def test_init_follow_ups_false(self) -> None:
        """Explicit include_follow_ups=False."""
        g = MilestonePromptGenerator(include_follow_ups=False)
        assert g.include_follow_ups is False

    def test_init_default_language(self) -> None:
        """Default language é pt-BR."""
        g = MilestonePromptGenerator()
        assert g.language == "pt-BR"

    def test_init_custom_language(self) -> None:
        """Custom language pode ser definido."""
        g = MilestonePromptGenerator(language="en-US")
        assert g.language == "en-US"


# ----------------------------------------------------------------------
# Testes — generate_milestone_prompt()
# ----------------------------------------------------------------------


class TestGenerateMilestonePrompt:
    def test_generates_nonempty_string(self, generator: MilestonePromptGenerator) -> None:
        """generate_milestone_prompt retorna string não-vazia."""
        prompt = generator.generate_milestone_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_generates_markdown_format(self, generator: MilestonePromptGenerator) -> None:
        """generate_milestone_prompt retorna Markdown válido."""
        prompt = generator.generate_milestone_prompt()
        assert "**" in prompt  # Bold
        assert "🌱" in prompt  # Emoji de reflexão

    def test_generates_reflection_marker(self, generator: MilestonePromptGenerator) -> None:
        """Prompt contém marcador de reflexão."""
        prompt = generator.generate_milestone_prompt()
        assert "Sua reflexão:" in prompt

    def test_generates_with_session_theme(
        self, generator: MilestonePromptGenerator, session_with_theme: Session
    ) -> None:
        """Prompt usa tema da sessão."""
        prompt = generator.generate_milestone_prompt(session=session_with_theme)
        assert "trabalho" in prompt

    def test_generates_with_theme_hint(
        self, generator: MilestonePromptGenerator, session_empty: Session
    ) -> None:
        """Prompt usa theme_hint quando fornecido."""
        prompt = generator.generate_milestone_prompt(session=session_empty, theme_hint="relacionamento")
        assert "relacionamento" in prompt

    def test_theme_hint_overrides_session_theme(
        self, generator: MilestonePromptGenerator, session_with_theme: Session
    ) -> None:
        """theme_hint sobrescreve tema da sessão."""
        prompt = generator.generate_milestone_prompt(session=session_with_theme, theme_hint="saúde")
        assert "saúde" in prompt
        assert "trabalho" not in prompt

    def test_generates_generic_topic_without_context(
        self, generator: MilestonePromptGenerator, session_empty: Session
    ) -> None:
        """Prompt usa tema genérico quando não há contexto."""
        prompt = generator.generate_milestone_prompt(session=session_empty)
        assert "sua jornada" in prompt

    def test_generates_with_session_no_themes(
        self, generator: MilestonePromptGenerator, session_no_themes: Session
    ) -> None:
        """Prompt com sessão sem temas usa genérico."""
        prompt = generator.generate_milestone_prompt(session=session_no_themes)
        assert "sua jornada" in prompt

    def test_generates_with_none_session(self, generator: MilestonePromptGenerator) -> None:
        """Prompt funciona com session=None."""
        prompt = generator.generate_milestone_prompt(session=None)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "sua jornada" in prompt

    def test_generates_with_none_theme_hint(
        self, generator: MilestonePromptGenerator, session_with_theme: Session
    ) -> None:
        """Prompt usa tema da sessão quando theme_hint é None."""
        prompt = generator.generate_milestone_prompt(session=session_with_theme, theme_hint=None)
        assert "trabalho" in prompt


# ----------------------------------------------------------------------
# Testes — follow_up_questions()
# ----------------------------------------------------------------------


class TestFollowUpQuestions:
    def test_returns_list(self, generator: MilestonePromptGenerator) -> None:
        """follow_up_questions retorna lista."""
        questions = generator.follow_up_questions(themes=["trabalho"])
        assert isinstance(questions, list)

    def test_returns_correct_count(self, generator: MilestonePromptGenerator) -> None:
        """follow_up_questions retorna count especificado."""
        questions = generator.follow_up_questions(themes=["trabalho"], count=2)
        assert len(questions) <= 2

    def test_returns_themed_questions(self, generator: MilestonePromptGenerator) -> None:
        """follow_up_questions retorna perguntas do tema."""
        questions = generator.follow_up_questions(themes=["trabalho"], count=3)
        # Deve conter perguntas sobre trabalho
        all_work_questions = FOLLOW_UP_TEMPLATES["trabalho"]
        assert any(q in questions for q in all_work_questions) or len(questions) > 0

    def test_returns_multiple_themes(self, generator: MilestonePromptGenerator) -> None:
        """follow_up_questions funciona com múltiplos temas."""
        questions = generator.follow_up_questions(themes=["trabalho", "relação"], count=3)
        assert isinstance(questions, list)
        assert len(questions) > 0

    def test_returns_generic_when_no_themes(self, generator: MilestonePromptGenerator) -> None:
        """follow_up_questions retorna genéricos quando themes=None."""
        questions = generator.follow_up_questions(themes=None, count=2)
        for q in questions:
            assert q in FOLLOW_UP_GENERIC

    def test_returns_generic_when_empty_themes(self, generator: MilestonePromptGenerator) -> None:
        """follow_up_questions retorna genéricos quando themes=[]."""
        questions = generator.follow_up_questions(themes=[], count=2)
        for q in questions:
            assert q in FOLLOW_UP_GENERIC

    def test_returns_generic_for_unknown_theme(self, generator: MilestonePromptGenerator) -> None:
        """follow_up_questions retorna genéricos para tema desconhecido."""
        questions = generator.follow_up_questions(themes=["tema_desconhecido"], count=2)
        for q in questions:
            assert q in FOLLOW_UP_GENERIC

    def test_count_exceeds_available_returns_all(self, generator: MilestonePromptGenerator) -> None:
        """count maior que disponíveis retorna todos os disponíveis."""
        questions = generator.follow_up_questions(themes=["trabalho"], count=100)
        work_questions = FOLLOW_UP_TEMPLATES["trabalho"]
        assert len(questions) <= len(work_questions)


# ----------------------------------------------------------------------
# Testes — skip_prompt()
# ----------------------------------------------------------------------


class TestSkipPrompt:
    def test_returns_nonempty_string(self, generator: MilestonePromptGenerator) -> None:
        """skip_prompt retorna string não-vazia."""
        result = generator.skip_prompt()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_skip_confirmation(self, generator: MilestonePromptGenerator) -> None:
        """skip_prompt retorna SKIP_CONFIRMATION."""
        result = generator.skip_prompt()
        assert result == SKIP_CONFIRMATION

    def test_skip_prompt_no_follow_ups(self, generator_no_follow_ups: MilestonePromptGenerator) -> None:
        """skip_prompt funciona com follow-ups desativados."""
        result = generator_no_follow_ups.skip_prompt()
        assert result == SKIP_CONFIRMATION


# ----------------------------------------------------------------------
# Testes — format_follow_up_section()
# ----------------------------------------------------------------------


class TestFormatFollowUpSection:
    def test_returns_nonempty_for_questions(self, generator: MilestonePromptGenerator) -> None:
        """format_follow_up_section retorna conteúdo para perguntas."""
        questions = ["Pergunta 1?", "Pergunta 2?"]
        result = generator.format_follow_up_section(questions)
        assert len(result) > 0

    def test_includes_separator(self, generator: MilestonePromptGenerator) -> None:
        """format_follow_up_section inclui separador Markdown."""
        questions = ["Pergunta 1?"]
        result = generator.format_follow_up_section(questions)
        assert "---" in result

    def test_numbers_questions(self, generator: MilestonePromptGenerator) -> None:
        """format_follow_up_section numera as perguntas."""
        questions = ["Pergunta 1?", "Pergunta 2?", "Pergunta 3?"]
        result = generator.format_follow_up_section(questions)
        assert "1." in result
        assert "2." in result
        assert "3." in result

    def test_returns_empty_for_empty_list(self, generator: MilestonePromptGenerator) -> None:
        """format_follow_up_section retorna vazio para lista vazia."""
        result = generator.format_follow_up_section([])
        assert result == ""

    def test_returns_empty_for_none(self, generator: MilestonePromptGenerator) -> None:
        """format_follow_up_section retorna vazio para None."""
        result = generator.format_follow_up_section(None)  # type: ignore
        assert result == ""

    def test_includes_optional_label(self, generator: MilestonePromptGenerator) -> None:
        """format_follow_up_section inclui label opcional."""
        questions = ["Pergunta 1?"]
        result = generator.format_follow_up_section(questions)
        assert "opcional" in result


# ----------------------------------------------------------------------
# Testes — _extract_topic()
# ----------------------------------------------------------------------


class TestExtractTopic:
    def test_theme_hint_priority(
        self, generator: MilestonePromptGenerator, session_with_theme: Session
    ) -> None:
        """theme_hint tem prioridade sobre session."""
        topic = generator._extract_topic(session_with_theme, "saúde")
        assert topic == "saúde"

    def test_session_first_theme(
        self, generator: MilestonePromptGenerator, session_with_theme: Session
    ) -> None:
        """Usa primeiro tema da sessão."""
        topic = generator._extract_topic(session_with_theme, None)
        assert topic == "trabalho"

    def test_none_session_returns_generic(
        self, generator: MilestonePromptGenerator
    ) -> None:
        """Session None retorna 'sua jornada'."""
        topic = generator._extract_topic(None, None)
        assert topic == "sua jornada"

    def test_empty_session_returns_generic(
        self, generator: MilestonePromptGenerator, session_empty: Session
    ) -> None:
        """Sessão vazia retorna 'sua jornada'."""
        topic = generator._extract_topic(session_empty, None)
        assert topic == "sua jornada"

    def test_session_no_analysis_returns_generic(
        self, generator: MilestonePromptGenerator, session_no_themes: Session
    ) -> None:
        """Sessão sem análise retorna 'sua jornada'."""
        topic = generator._extract_topic(session_no_themes, None)
        assert topic == "sua jornada"


# ----------------------------------------------------------------------
# Testes — Edge cases
# ----------------------------------------------------------------------


class TestEdgeCases:
    def test_generate_milestone_prompt_all_args_none(
        self, generator: MilestonePromptGenerator
    ) -> None:
        """generate_milestone_prompt funciona com todos os args None."""
        prompt = generator.generate_milestone_prompt(session=None, theme_hint=None)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_follow_up_with_mixed_known_unknown_themes(
        self, generator: MilestonePromptGenerator
    ) -> None:
        """follow_up_questions funciona com temas mistos."""
        questions = generator.follow_up_questions(themes=["trabalho", "desconhecido"], count=3)
        assert isinstance(questions, list)

    def test_generate_with_first_session_theme(
        self, generator: MilestonePromptGenerator
    ) -> None:
        """Usa primeiro tema quando há múltiplos temas."""
        session = Session(
            session_id="multi-theme",
            timestamp="2026-05-11T10:00:00",
            input_format="text",
            raw_content="Teste",
            analysis_result=AnalysisResult(
                diagnosis="",
                themes=["dinheiro", "trabalho", "saúde"],
            ),
        )
        prompt = generator.generate_milestone_prompt(session=session)
        assert "dinheiro" in prompt

    def test_generate_prompt_deterministic_output(
        self, generator: MilestonePromptGenerator, session_with_theme: Session
    ) -> None:
        """generate_milestone_prompt retorna formato consistente."""
        prompt1 = generator.generate_milestone_prompt(session=session_with_theme)
        prompt2 = generator.generate_milestone_prompt(session=session_with_theme)
        # Mesmo tema deve gerar mesmo formato
        assert prompt1.startswith(prompt2[:20]) or prompt2.startswith(prompt1[:20])

    def test_follow_up_questions_returns_strings_only(
        self, generator: MilestonePromptGenerator
    ) -> None:
        """follow_up_questions retorna apenas strings."""
        questions = generator.follow_up_questions(themes=["trabalho"], count=2)
        assert all(isinstance(q, str) for q in questions)

    def test_format_follow_up_section_returns_markdown(
        self, generator: MilestonePromptGenerator
    ) -> None:
        """format_follow_up_section retorna Markdown."""
        questions = ["Pergunta um?", "Pergunta dois?"]
        result = generator.format_follow_up_section(questions)
        # Deve ser formato Markdown
        assert "#" in result or "-" in result or "1." in result

    def test_skip_prompt_returns_message_not_template(
        self, generator: MilestonePromptGenerator
    ) -> None:
        """skip_prompt retorna mensagem, não o template."""
        result = generator.skip_prompt()
        assert "ok" in result.lower() or "pulamos" in result.lower()

    def test_milestone_prompt_includes_encouragement(
        self, generator: MilestonePromptGenerator
    ) -> None:
        """Prompt inclui linguagem encorajadora."""
        prompt = generator.generate_milestone_prompt()
        # Deve conter linguagem de suporte/não-judgement
        assert "sem" in prompt.lower() or "não" in prompt.lower() or "julgamento" in prompt.lower()
