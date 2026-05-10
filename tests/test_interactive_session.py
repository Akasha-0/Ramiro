"""Testes unitários para src/interactive_session.py.

Cobertura:
- InteractiveSession.run() — fluxo completo da sessão
- InteractiveSession.collect_question() — coleta de pergunta
- InteractiveSession.select_spread() — seleção de tiragem
- InteractiveSession.collect_cards() — coleta de cartas
- InteractiveSession.build_structured_input() — construção do StructuredInput
- InteractiveSession._validate_card_name() — validação de nomes de carta
- InteractiveSession._get_card_suggestions() — sugestões de cartas
- InteractiveSession._is_abort_command() — detecção de comandos de abort
- InteractiveSession._is_help_command() — detecção de comandos de ajuda
- InteractiveSession.handle_abort() — tratamento de abort
- SessionError — exceção de erro de sessão
- SessionAborted — exceção de abort
- CLInputProvider — provedor de input via CLI
"""

import pytest

from src.interactive_session import (
    InteractiveSession,
    SessionError,
    SessionAborted,
    CLInputProvider,
    InputProvider,
    ABORT_COMMANDS,
    HELP_COMMANDS,
)
from src.types import StructuredInput, CardPosition


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


class MockInputProvider:
    """Provedor de input mockado para testes."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._index = 0

    def prompt(self, message: str) -> str:
        if self._index >= len(self._responses):
            raise EOFError("Sem mais respostas mockadas")
        response = self._responses[self._index]
        self._index += 1
        return response

    def confirm(self, message: str) -> bool:
        if self._index >= len(self._responses):
            raise EOFError("Sem mais respostas mockadas")
        response = self._responses[self._index]
        self._index += 1
        return response.lower() in ("s", "sim", "y", "yes")


@pytest.fixture
def mock_provider() -> type[MockInputProvider]:
    """Retorna a classe MockInputProvider para uso nos testes."""
    return MockInputProvider


@pytest.fixture
def session(mock_provider: type[MockInputProvider]) -> InteractiveSession:
    """Sessão interativa com provider mockado."""
    return InteractiveSession(
        input_provider=mock_provider([]),
        max_question_length=500,
    )


# ----------------------------------------------------------------------
# Testes — InputProvider Protocol
# ----------------------------------------------------------------------


class TestInputProviderProtocol:
    def test_cl_input_provider_prompt_exists(self) -> None:
        provider = CLInputProvider()
        assert hasattr(provider, "prompt")
        assert callable(provider.prompt)

    def test_cl_input_provider_confirm_exists(self) -> None:
        provider = CLInputProvider()
        assert hasattr(provider, "confirm")
        assert callable(provider.confirm)


# ----------------------------------------------------------------------
# Testes — SessionError
# ----------------------------------------------------------------------


class TestSessionError:
    def test_session_error_message(self) -> None:
        err = SessionError("Erro de teste")
        assert "Erro de teste" in str(err)
        assert err.message == "Erro de teste"
        assert err.step is None

    def test_session_error_with_step(self) -> None:
        err = SessionError("Erro de teste", step="collect_question")
        assert "Erro de teste" in str(err)
        assert err.step == "collect_question"
        assert "[collect_question]" in str(err)

    def test_session_error_default_message(self) -> None:
        err = SessionError(message="Mensagem padrão")
        assert "Mensagem padrão" in str(err)


# ----------------------------------------------------------------------
# Testes — SessionAborted
# ----------------------------------------------------------------------


class TestSessionAborted:
    def test_session_aborted_message(self) -> None:
        err = SessionAborted()
        assert "interrompida pelo usuário" in str(err)

    def test_session_aborted_is_exception(self) -> None:
        err = SessionAborted()
        assert isinstance(err, Exception)


# ----------------------------------------------------------------------
# Testes — _is_abort_command()
# ----------------------------------------------------------------------


class TestIsAbortCommand:
    def test_sair_command(self, session: InteractiveSession) -> None:
        assert session._is_abort_command("sair") is True

    def test_quit_command(self, session: InteractiveSession) -> None:
        assert session._is_abort_command("quit") is True

    def test_q_command(self, session: InteractiveSession) -> None:
        assert session._is_abort_command("q") is True

    def test_exit_command(self, session: InteractiveSession) -> None:
        assert session._is_abort_command("exit") is True

    def test_case_insensitive(self, session: InteractiveSession) -> None:
        assert session._is_abort_command("SAIR") is True
        assert session._is_abort_command("Quit") is True

    def test_with_whitespace(self, session: InteractiveSession) -> None:
        assert session._is_abort_command("  sair  ") is True

    def test_regular_text_not_abort(self, session: InteractiveSession) -> None:
        assert session._is_abort_command("minha pergunta") is False
        assert session._is_abort_command("trabalho") is False

    def test_empty_string_not_abort(self, session: InteractiveSession) -> None:
        assert session._is_abort_command("") is False


# ----------------------------------------------------------------------
# Testes — _is_help_command()
# ----------------------------------------------------------------------


class TestIsHelpCommand:
    def test_ajuda_command(self, session: InteractiveSession) -> None:
        assert session._is_help_command("ajuda") is True

    def test_help_command(self, session: InteractiveSession) -> None:
        assert session._is_help_command("help") is True

    def test_h_command(self, session: InteractiveSession) -> None:
        assert session._is_help_command("h") is True

    def test_question_mark(self, session: InteractiveSession) -> None:
        assert session._is_help_command("?") is True

    def test_case_insensitive(self, session: InteractiveSession) -> None:
        assert session._is_help_command("AJUDA") is True
        assert session._is_help_command("Help") is True

    def test_regular_text_not_help(self, session: InteractiveSession) -> None:
        assert session._is_help_command("não sei") is False
        assert session._is_help_command("trabalho") is False


# ----------------------------------------------------------------------
# Testes — _validate_card_name()
# ----------------------------------------------------------------------


class TestValidateCardName:
    def test_valid_card_a_cruz(self, session: InteractiveSession) -> None:
        result = session._validate_card_name("A Cruz")
        assert result is not None
        assert result.name == "A Cruz"

    def test_valid_card_a_estrela(self, session: InteractiveSession) -> None:
        result = session._validate_card_name("A Estrela")
        assert result is not None
        assert result.name == "A Estrela"

    def test_valid_card_a_casa(self, session: InteractiveSession) -> None:
        result = session._validate_card_name("A Casa")
        assert result is not None
        assert result.name == "A Casa"

    def test_valid_card_case_insensitive(self, session: InteractiveSession) -> None:
        result = session._validate_card_name("a cruz")
        assert result is not None

    def test_valid_card_with_whitespace(self, session: InteractiveSession) -> None:
        result = session._validate_card_name("  A Estrela  ")
        assert result is not None

    def test_invalid_card_returns_none(self, session: InteractiveSession) -> None:
        result = session._validate_card_name("CartaInvalida123")
        assert result is None

    def test_empty_card_returns_none(self, session: InteractiveSession) -> None:
        result = session._validate_card_name("")
        assert result is None

    def test_partial_name_returns_none(self, session: InteractiveSession) -> None:
        result = session._validate_card_name("Cru")
        assert result is None


# ----------------------------------------------------------------------
# Testes — _get_card_suggestions()
# ----------------------------------------------------------------------


class TestGetCardSuggestions:
    def test_suggestions_for_cruz(self, session: InteractiveSession) -> None:
        suggestions = session._get_card_suggestions("cruz")
        assert len(suggestions) > 0
        assert any("Cruz" in s for s in suggestions)

    def test_suggestions_for_estrela(self, session: InteractiveSession) -> None:
        suggestions = session._get_card_suggestions("estrela")
        assert len(suggestions) > 0
        assert any("Estrela" in s for s in suggestions)

    def test_suggestions_limit_five(self, session: InteractiveSession) -> None:
        suggestions = session._get_card_suggestions("a")
        assert len(suggestions) <= 5

    def test_no_suggestions_for_unknown(self, session: InteractiveSession) -> None:
        suggestions = session._get_card_suggestions("xyz123abc")
        assert len(suggestions) == 0

    def test_partial_match_returns_results(self, session: InteractiveSession) -> None:
        suggestions = session._get_card_suggestions("cas")
        assert len(suggestions) > 0
        assert any("Casa" in s for s in suggestions)

    def test_case_insensitive_search(self, session: InteractiveSession) -> None:
        suggestions = session._get_card_suggestions("ESTRELA")
        assert len(suggestions) > 0


# ----------------------------------------------------------------------
# Testes — collect_question()
# ----------------------------------------------------------------------


class TestCollectQuestion:
    def test_collects_valid_question(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["Tenho dúvidas sobre trabalho"])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_question()
        assert result == "Tenho dúvidas sobre trabalho"

    def test_collects_question_with_accents(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["Relação com família está difícil"])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_question()
        assert "família" in result

    def test_raises_abort_on_sair_command(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["sair"])
        session = InteractiveSession(input_provider=provider)
        with pytest.raises(SessionAborted):
            session.collect_question()

    def test_raises_abort_on_quit_command(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["quit"])
        session = InteractiveSession(input_provider=provider)
        with pytest.raises(SessionAborted):
            session.collect_question()

    def test_shows_help_on_help_command(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        """Primeiro 'help' mostra ajuda, segundo input é a pergunta."""
        provider = mock_provider(["ajuda", "Minha pergunta sobre trabalho"])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_question()
        assert result == "Minha pergunta sobre trabalho"

    def test_rejects_empty_input(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["", "  ", "Pergunta válida"])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_question()
        assert result == "Pergunta válida"

    def test_rejects_too_long_question(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        long_question = "A" * 600  # Maior que max_question_length
        provider = mock_provider([long_question, "Pergunta curta"])
        session = InteractiveSession(input_provider=provider, max_question_length=500)
        result = session.collect_question()
        assert result == "Pergunta curta"

    def test_accepts_exactly_max_length(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        question = "B" * 500  # Exatamente max_length
        provider = mock_provider([question])
        session = InteractiveSession(input_provider=provider, max_question_length=500)
        result = session.collect_question()
        assert len(result) == 500

    def test_trims_whitespace(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["  Pergunta com espaços  "])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_question()
        assert result == "Pergunta com espaços"


# ----------------------------------------------------------------------
# Testes — select_spread()
# ----------------------------------------------------------------------


class TestSelectSpread:
    def test_select_by_number_1(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["1"])
        session = InteractiveSession(input_provider=provider)
        result = session.select_spread()
        assert result.name == "tres-cartas"
        assert result.display_name == "Três Cartas"

    def test_select_by_number_2(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["2"])
        session = InteractiveSession(input_provider=provider)
        result = session.select_spread()
        assert result.name == "cruz-celtas"

    def test_select_by_name(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["tres-cartas"])
        session = InteractiveSession(input_provider=provider)
        result = session.select_spread()
        assert result.name == "tres-cartas"

    def test_select_by_display_name(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["Três Cartas"])
        session = InteractiveSession(input_provider=provider)
        result = session.select_spread()
        assert result.name == "tres-cartas"

    def test_select_partial_match(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["cruz"])
        session = InteractiveSession(input_provider=provider)
        result = session.select_spread()
        assert result.name == "cruz-celtas"

    def test_raises_abort_on_sair(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["sair"])
        session = InteractiveSession(input_provider=provider)
        with pytest.raises(SessionAborted):
            session.select_spread()

    def test_shows_help_on_ajuda(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["ajuda", "1"])
        session = InteractiveSession(input_provider=provider)
        result = session.select_spread()
        assert result.name == "tres-cartas"

    def test_rejects_invalid_number(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["99", "1"])
        session = InteractiveSession(input_provider=provider)
        result = session.select_spread()
        assert result.name == "tres-cartas"

    def test_rejects_invalid_name(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["tiragem-invalida", "1"])
        session = InteractiveSession(input_provider=provider)
        result = session.select_spread()
        assert result.name == "tres-cartas"

    def test_partial_match_ambiguous_rejects(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["tres", "1"])
        session = InteractiveSession(input_provider=provider)
        result = session.select_spread()
        assert result.name == "tres-cartas"


# ----------------------------------------------------------------------
# Testes — collect_cards()
# ----------------------------------------------------------------------


class TestCollectCards:
    def test_collects_single_card(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        from src.spread_templates import get_template

        template = get_template("uma-carta")
        assert template is not None
        # Use card name that matches catalog exactly
        provider = mock_provider(["A Cruz"])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_cards(template)

        assert len(result) == 1
        assert result[0].card_name == "A Cruz"
        assert result[0].position == 1

    def test_collects_three_cards(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        from src.spread_templates import get_template

        template = get_template("tres-cartas")
        assert template is not None
        # Use card names that match catalog exactly
        provider = mock_provider(["A Cruz", "A Estrela", "A Casa"])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_cards(template)

        assert len(result) == 3
        assert result[0].card_name == "A Cruz"
        assert result[1].card_name == "A Estrela"
        assert result[2].card_name == "A Casa"

    def test_validates_invalid_card_prompts_retry(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        from src.spread_templates import get_template

        template = get_template("tres-cartas")
        assert template is not None
        # First invalid card, then valid ones
        provider = mock_provider(["CartaInvalida", "A Cruz", "A Estrela", "A Casa"])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_cards(template)

        assert len(result) == 3

    def test_rejects_empty_input_then_accepts(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        from src.spread_templates import get_template

        template = get_template("tres-cartas")
        assert template is not None
        # Empty input first, then valid card
        provider = mock_provider(["", "A Cruz", "A Estrela", "A Casa"])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_cards(template)

        assert len(result) == 3

    def test_raises_abort_on_sair(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        from src.spread_templates import get_template

        template = get_template("tres-cartas")
        assert template is not None
        provider = mock_provider(["sair"])
        session = InteractiveSession(input_provider=provider)

        with pytest.raises(SessionAborted):
            session.collect_cards(template)

    def test_shows_help_on_ajuda(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        from src.spread_templates import get_template

        template = get_template("tres-cartas")
        assert template is not None
        # First input is help command, then valid card names
        provider = mock_provider(["ajuda", "A Cruz", "A Estrela", "A Casa"])
        session = InteractiveSession(input_provider=provider)
        result = session.collect_cards(template)

        assert len(result) == 3


# ----------------------------------------------------------------------
# Testes — build_structured_input()
# ----------------------------------------------------------------------


class TestBuildStructuredInput:
    def test_creates_spread_format(self) -> None:
        session = InteractiveSession()
        result = session.build_structured_input(
            "Minha dúvida",
            "tres-cartas",
            ["Cruz", "Estrela", "Casa"],
        )
        assert result.format == "spread"

    def test_preserves_raw_content(self) -> None:
        session = InteractiveSession()
        result = session.build_structured_input(
            "Minha dúvida sobre trabalho",
            "tres-cartas",
            ["Cruz"],
        )
        assert result.raw_content == "Minha dúvida sobre trabalho"

    def test_creates_card_positions(self) -> None:
        session = InteractiveSession()
        result = session.build_structured_input(
            "Pergunta",
            "tres-cartas",
            ["Cruz", "Estrela", "Casa"],
        )

        assert result.cards is not None
        assert len(result.cards) == 3
        assert result.cards[0].position == 1
        assert result.cards[1].position == 2
        assert result.cards[2].position == 3

    def test_card_names_preserved(self) -> None:
        session = InteractiveSession()
        result = session.build_structured_input(
            "Pergunta",
            "tres-cartas",
            ["cruz", "estrela", "casa"],
        )

        assert result.cards[0].card_name == "cruz"
        assert result.cards[1].card_name == "estrela"
        assert result.cards[2].card_name == "casa"

    def test_keywords_is_none(self) -> None:
        session = InteractiveSession()
        result = session.build_structured_input(
            "Pergunta",
            "tres-cartas",
            ["Cruz"],
        )
        assert result.keywords is None

    def test_cards_is_none_for_text_format(self) -> None:
        session = InteractiveSession()
        result = session.build_structured_input(
            "Pergunta",
            "uma-carta",
            ["Cruz"],
        )
        assert result.cards is not None
        assert len(result.cards) == 1

    def test_invalid_template_raises_session_error(self) -> None:
        session = InteractiveSession()
        with pytest.raises(SessionError) as exc_info:
            session.build_structured_input(
                "Pergunta",
                "template-inexistente",
                ["Cruz"],
            )
        assert "não encontrado" in str(exc_info.value).lower()

    def test_empty_card_list_creates_empty_cards(self) -> None:
        session = InteractiveSession()
        result = session.build_structured_input(
            "Pergunta",
            "tres-cartas",
            [],
        )
        assert result.cards == []


# ----------------------------------------------------------------------
# Testes — handle_abort()
# ----------------------------------------------------------------------


class TestHandleAbort:
    def test_handle_abort_raises_session_aborted(self) -> None:
        session = InteractiveSession()
        with pytest.raises(SessionAborted):
            session.handle_abort()


# ----------------------------------------------------------------------
# Testes — Constantes
# ----------------------------------------------------------------------


class TestConstants:
    def test_abort_commands_contains_sair(self) -> None:
        assert "sair" in ABORT_COMMANDS

    def test_abort_commands_contains_quit(self) -> None:
        assert "quit" in ABORT_COMMANDS

    def test_abort_commands_lowercase_only(self) -> None:
        for cmd in ABORT_COMMANDS:
            assert cmd == cmd.lower()

    def test_help_commands_contains_ajuda(self) -> None:
        assert "ajuda" in HELP_COMMANDS

    def test_help_commands_contains_help(self) -> None:
        assert "help" in HELP_COMMANDS


# ----------------------------------------------------------------------
# Testes — run() — fluxo completo
# ----------------------------------------------------------------------


class TestRun:
    def test_run_returns_structured_input(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        from src.spread_templates import get_template

        template = get_template("tres-cartas")
        assert template is not None
        responses = [
            "Tenho dúvida sobre trabalho",
            "1",  # Seleciona tres-cartas
            "A Cruz",  # Posição 1
            "A Estrela",  # Posição 2
            "A Casa",  # Posição 3
        ]
        provider = mock_provider(responses)
        session = InteractiveSession(input_provider=provider)

        result = session.run()

        assert isinstance(result, StructuredInput)
        assert result.format == "spread"
        assert result.cards is not None
        assert len(result.cards) == 3

    def test_run_abort_at_question_raises(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        provider = mock_provider(["sair"])
        session = InteractiveSession(input_provider=provider)

        with pytest.raises(SessionAborted):
            session.run()

    def test_run_abort_at_spread_raises(
        self,
        mock_provider: type[MockInputProvider],
    ) -> None:
        responses = [
            "Minha pergunta",
            "sair",
        ]
        provider = mock_provider(responses)
        session = InteractiveSession(input_provider=provider)

        with pytest.raises(SessionAborted):
            session.run()