"""Testes unitários para src/input_processor.py.

Cobertura:
- InputProcessor.parse() — validação de formato, truncagem, delegação
- InputProcessor._parse_free_text() — extração de keywords
- InputProcessor._parse_csv_spread() — parsing de tiragem
- InputProcessor._parse_symbols() — normalização de lista separada por vírgula
- InputProcessor._parse_csv_line() — múltiplos separadores
- InputProcessor._truncate() — limite de tamanho
"""

import pytest

from src.input_processor import (
    InputProcessor,
    ParseError,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def processor() -> InputProcessor:
    """Processor com configurações padrão."""
    return InputProcessor()


@pytest.fixture
def processor_small() -> InputProcessor:
    """Processor com limite de 50 caracteres."""
    return InputProcessor(max_length=50)


# ----------------------------------------------------------------------
# Testes — parse(): validação de formato
# ----------------------------------------------------------------------


class TestParseFormatValidation:
    def test_unknown_format_raises_value_error(self, processor: InputProcessor) -> None:
        with pytest.raises(ValueError) as exc_info:
            processor.parse("qualquer texto", "yaml")
        assert "Formato desconhecido" in str(exc_info.value)
        assert "yaml" in str(exc_info.value)

    def test_empty_format_raises_value_error(self, processor: InputProcessor) -> None:
        with pytest.raises(ValueError):
            processor.parse("texto", "")

    def test_case_sensitive_format(self, processor: InputProcessor) -> None:
        with pytest.raises(ValueError):
            processor.parse("texto", "TEXT")


# ----------------------------------------------------------------------
# Testes — parse(): truncagem
# ----------------------------------------------------------------------


class TestParseTruncation:
    def test_truncate_short_input(self, processor_small: InputProcessor) -> None:
        """Inputs curtos passam sem truncagem."""
        result = processor_small.parse("Bom dia claro", "text")
        assert result.raw_content == "Bom dia claro"
        assert "claro" in result.keywords

    def test_truncate_exceeds_limit(self, processor_small: InputProcessor) -> None:
        """Inputs longos são truncados ao limite e marcado como truncado."""
        long_text = "A" * 100
        result = processor_small.parse(long_text, "text")
        assert len(result.raw_content) == 50
        assert result.raw_content == "A" * 50

    def test_truncate_at_exact_limit(self, processor_small: InputProcessor) -> None:
        """Inputs exatamente no limite não são truncados."""
        exact_text = "B" * 50
        result = processor_small.parse(exact_text, "text")
        assert len(result.raw_content) == 50


# ----------------------------------------------------------------------
# Testes — _parse_free_text()
# ----------------------------------------------------------------------


class TestParseFreeText:
    def test_extracts_significant_keywords(self, processor: InputProcessor) -> None:
        result = processor.parse(
            "Tenho dúvidas sobre trabalho e dinheiro",
            "text",
        )
        assert result.format == "text"
        assert result.cards is None
        assert result.keywords is not None
        assert "trabalho" in result.keywords
        assert "dinheiro" in result.keywords

    def test_filters_portuguese_stop_words(self, processor: InputProcessor) -> None:
        result = processor.parse(
            "Eu estou pensando muito sobre a família",
            "text",
        )
        assert "eu" not in result.keywords
        assert "estou" not in result.keywords
        assert "sobre" not in result.keywords
        # "família" tem 7 letras e não é stop word
        assert "família" in result.keywords

    def test_filters_short_words(self, processor: InputProcessor) -> None:
        result = processor.parse("Eu te amo", "text")
        # "amo" tem 3 letras mas é stop word; "te" tem 2 < 3
        assert "te" not in result.keywords

    def test_removes_duplicates_preserving_order(self, processor: InputProcessor) -> None:
        result = processor.parse("casa casa casa estrela", "text")
        assert result.keywords == ["casa", "estrela"]

    def test_handles_special_characters(self, processor: InputProcessor) -> None:
        result = processor.parse(
            "Relação! Amição @trabalho #saúde$",
            "text",
        )
        assert result.format == "text"
        # caracteres especiais são removidos; palavras significativas permanecem
        assert "trabalho" in result.keywords
        # Verifica que não há tokens vazios
        assert "" not in result.keywords

    def test_empty_text_returns_empty_keywords(self, processor: InputProcessor) -> None:
        result = processor.parse("", "text")
        assert result.format == "text"
        assert result.keywords == []

    def test_only_stop_words(self, processor: InputProcessor) -> None:
        result = processor.parse("eu o a de para", "text")
        assert result.keywords == []

    def test_preserves_accents(self, processor: InputProcessor) -> None:
        result = processor.parse("relação saúde coração", "text")
        # "coração" tem acento e 7 letras
        assert any("coração" in kw for kw in result.keywords)

    def test_raw_content_preserved(self, processor: InputProcessor) -> None:
        original = "Texto com ACENTOS e maiúsculas"
        result = processor.parse(original, "text")
        assert result.raw_content == original


# ----------------------------------------------------------------------
# Testes — _parse_csv_spread()
# ----------------------------------------------------------------------


class TestParseCsvSpread:
    def test_valid_csv_with_header(self, processor: InputProcessor) -> None:
        csv_content = "pos,carta\n1,Cruz\n2,Estrela\n3,Café"
        result = processor.parse(csv_content, "spread")
        assert result.format == "spread"
        assert result.keywords is None
        assert result.cards is not None
        assert len(result.cards) == 3
        assert result.cards[0].position == 1
        assert result.cards[0].card_name == "Cruz"
        assert result.cards[1].position == 2
        assert result.cards[1].card_name == "Estrela"
        assert result.cards[2].position == 3
        assert result.cards[2].card_name == "Café"

    def test_valid_csv_without_header(self, processor: InputProcessor) -> None:
        csv_content = "1,Cruz\n2,Estrela"
        result = processor.parse(csv_content, "spread")
        assert result.format == "spread"
        assert len(result.cards) == 2
        assert result.cards[0].card_name == "Cruz"

    def test_csv_semicolon_delimiter(self, processor: InputProcessor) -> None:
        csv_content = "1;Cruz\n2;Estrela"
        result = processor.parse(csv_content, "spread")
        assert len(result.cards) == 2
        assert result.cards[0].card_name == "Cruz"

    def test_csv_tab_delimiter(self, processor: InputProcessor) -> None:
        csv_content = "1\tCruz\n2\tEstrela"
        result = processor.parse(csv_content, "spread")
        assert len(result.cards) == 2

    def test_csv_header_english(self, processor: InputProcessor) -> None:
        csv_content = "position,card\n1,Cruz\n2,Estrela"
        result = processor.parse(csv_content, "spread")
        assert len(result.cards) == 2

    def test_csv_empty_content_raises_parse_error(self, processor: InputProcessor) -> None:
        with pytest.raises(ParseError) as exc_info:
            processor.parse("", "spread")
        assert "vazio" in str(exc_info.value).lower()

    def test_csv_only_whitespace_raises_parse_error(self, processor: InputProcessor) -> None:
        with pytest.raises(ParseError) as exc_info:
            processor.parse("   \n  \n  ", "spread")
        assert "vazio" in str(exc_info.value).lower()

    def test_csv_only_header_no_data_raises_parse_error(
        self, processor: InputProcessor
    ) -> None:
        with pytest.raises(ParseError) as exc_info:
            processor.parse("pos,carta", "spread")
        assert "sem dados" in str(exc_info.value).lower() or "apenas" in str(exc_info.value).lower()

    def test_csv_invalid_position_non_numeric_raises_parse_error(
        self, processor: InputProcessor
    ) -> None:
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1,Cruz\ndois,Estrela", "spread")
        assert "inválida" in str(exc_info.value).lower() or "esperado" in str(exc_info.value).lower()

    def test_csv_position_zero_raises_parse_error(self, processor: InputProcessor) -> None:
        with pytest.raises(ParseError) as exc_info:
            processor.parse("0,Cruz", "spread")
        assert "zero" in str(exc_info.value).lower() or "maior" in str(exc_info.value).lower()

    def test_csv_negative_position_raises_parse_error(self, processor: InputProcessor) -> None:
        with pytest.raises(ParseError) as exc_info:
            processor.parse("-1,Cruz", "spread")
        assert "zero" in str(exc_info.value).lower() or "maior" in str(exc_info.value).lower()

    def test_csv_empty_card_name_raises_parse_error(self, processor: InputProcessor) -> None:
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1,\n2,Cruz", "spread")
        assert "ausente" in str(exc_info.value).lower() or "vazio" in str(exc_info.value).lower()

    def test_csv_all_lines_invalid_raises_parse_error(self, processor: InputProcessor) -> None:
        with pytest.raises(ParseError) as exc_info:
            processor.parse("abc\ndef\tghi", "spread")
        assert "inválida" in str(exc_info.value).lower() or "esperado" in str(exc_info.value).lower()

    def test_csv_skips_empty_lines(self, processor: InputProcessor) -> None:
        csv_content = "1,Cruz\n\n2,Estrela\n  \n3,Café"
        result = processor.parse(csv_content, "spread")
        assert len(result.cards) == 3

    def test_csv_fallback_no_separator(self, processor: InputProcessor) -> None:
        """Linha sem separador gera ParseError porque posição não é numérica."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1 Cruz", "spread")
        assert "inválida" in str(exc_info.value).lower() or "esperado" in str(exc_info.value).lower()

    def test_csv_raw_content_preserved(self, processor: InputProcessor) -> None:
        csv_content = "1,Cruz\n2,Estrela"
        result = processor.parse(csv_content, "spread")
        assert result.raw_content == csv_content


# ----------------------------------------------------------------------
# Testes — _parse_symbols()
# ----------------------------------------------------------------------


class TestParseSymbols:
    def test_basic_symbols(self, processor: InputProcessor) -> None:
        result = processor.parse("casa,estrela,café", "symbols")
        assert result.format == "symbols"
        assert result.cards is None
        assert result.keywords is not None
        assert "casa" in result.keywords
        assert "estrela" in result.keywords
        assert "café" in result.keywords

    def test_symbols_lowercased(self, processor: InputProcessor) -> None:
        result = processor.parse("CASA,Estrela,CAFÉ", "symbols")
        assert "casa" in result.keywords
        assert "estrela" in result.keywords
        assert "café" in result.keywords

    def test_symbols_strip_whitespace(self, processor: InputProcessor) -> None:
        result = processor.parse("  casa  ,  estrela  , café ", "symbols")
        assert "casa" in result.keywords
        assert "estrela" in result.keywords
        assert "café" in result.keywords
        # Sem espaços em branco nos tokens
        assert all(" " not in kw for kw in result.keywords)

    def test_symbols_filters_empty_tokens(self, processor: InputProcessor) -> None:
        result = processor.parse("casa,,estrela,,,café", "symbols")
        assert len(result.keywords) == 3
        assert "casa" in result.keywords
        assert "estrela" in result.keywords
        assert "café" in result.keywords

    def test_symbols_empty_string(self, processor: InputProcessor) -> None:
        result = processor.parse("", "symbols")
        assert result.format == "symbols"
        assert result.keywords is None or result.keywords == []

    def test_symbols_only_empty_commas(self, processor: InputProcessor) -> None:
        result = processor.parse(",,,", "symbols")
        assert result.format == "symbols"
        assert result.keywords == [] or result.keywords is None

    def test_symbols_preserves_raw_content(self, processor: InputProcessor) -> None:
        original = "Casa,  Estrela  ,Café"
        result = processor.parse(original, "symbols")
        assert result.raw_content == original


# ----------------------------------------------------------------------
# Testes — _parse_csv_line()
# ----------------------------------------------------------------------


class TestParseCsvLine:
    def test_comma_delimiter(self, processor: InputProcessor) -> None:
        result = processor._parse_csv_line("1,Cruz,Extra")
        assert result == ["1", "Cruz", "Extra"]

    def test_semicolon_delimiter(self, processor: InputProcessor) -> None:
        result = processor._parse_csv_line("1;Cruz;Extra")
        assert result == ["1", "Cruz", "Extra"]

    def test_tab_delimiter(self, processor: InputProcessor) -> None:
        result = processor._parse_csv_line("1\tCruz\tExtra")
        assert result == ["1", "Cruz", "Extra"]

    def test_no_separator_returns_single_field(self, processor: InputProcessor) -> None:
        result = processor._parse_csv_line("Cruz")
        assert result == ["Cruz"]

    def test_comma_takes_precedence(self, processor: InputProcessor) -> None:
        """Vírgula é testada primeiro."""
        result = processor._parse_csv_line("1,Cruz;Extra")
        assert result == ["1", "Cruz;Extra"]


# ----------------------------------------------------------------------
# Testes — _truncate()
# ----------------------------------------------------------------------


class TestTruncate:
    def test_within_limit(self, processor: InputProcessor) -> None:
        text = "Texto curto"
        result, was_truncated = processor._truncate(text)
        assert result == text
        assert was_truncated is False

    def test_exceeds_limit(self, processor_small: InputProcessor) -> None:
        text = "A" * 100
        result, was_truncated = processor_small._truncate(text)
        assert result == "A" * 50
        assert was_truncated is True

    def test_exactly_at_limit(self, processor_small: InputProcessor) -> None:
        text = "B" * 50
        result, was_truncated = processor_small._truncate(text)
        assert result == text
        assert was_truncated is False

    def test_empty_string(self, processor_small: InputProcessor) -> None:
        result, was_truncated = processor_small._truncate("")
        assert result == ""
        assert was_truncated is False


# ----------------------------------------------------------------------
# Testes — ParseError
# ----------------------------------------------------------------------


class TestParseError:
    def test_parse_error_message(self) -> None:
        err = ParseError("Erro de teste")
        assert "Erro de teste" in str(err)
        assert err.message == "Erro de teste"
        assert err.line is None
        assert err.details is None

    def test_parse_error_with_line(self) -> None:
        err = ParseError("Erro de teste", line=5)
        assert "linha 5" in str(err)

    def test_parse_error_with_details(self) -> None:
        err = ParseError("Erro de teste", details="info adicional")
        assert "info adicional" in str(err)

    def test_parse_error_with_line_and_details(self) -> None:
        err = ParseError("Erro", line=3, details="detalhes")
        err_str = str(err)
        assert "linha 3" in err_str
        assert "detalhes" in err_str

    def test_parse_error_with_recovery(self) -> None:
        """Testa que o campo recovery é exibido no erro com 'Dica:'."""
        err = ParseError(
            "Cartão desconhecido",
            details="'Cas' não encontrada",
            recovery="Cards válidos: Casa, Cobra, Forca",
        )
        err_str = str(err)
        assert "Dica:" in err_str
        assert "Casa, Cobra, Forca" in err_str

    def test_parse_error_recovery_not_shown_when_none(self) -> None:
        """Testa que Dica: não aparece quando não há recovery."""
        err = ParseError("Erro simples")
        err_str = str(err)
        assert "Dica:" not in err_str


# ----------------------------------------------------------------------
# Testes — Error messages com sugestões
# ----------------------------------------------------------------------


class TestErrorMessagesWithSuggestions:
    """Testes para mensagens de erro com sugestões 'Did you mean'."""

    def test_unknown_card_name_includes_suggestions(self, processor: InputProcessor) -> None:
        """Cartão desconhecido deve mostrar sugestão de nomes válidos."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1,Cas", "spread")
        err_str = str(exc_info.value)
        assert "Cartão desconhecido" in err_str
        assert "Cas" in err_str
        # Deve mostrar cards válidos como sugestão
        assert "Cards válidos:" in err_str or "Dica:" in err_str

    def test_typo_card_name_suggests_corrections(self, processor: InputProcessor) -> None:
        """Nome de carta com typo deve sugerir correção."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1,Estrelaa", "spread")
        err_str = str(exc_info.value)
        assert "Estrelaa" in err_str
        assert "Cards válidos:" in err_str or "Dica:" in err_str

    def test_unknown_card_shows_similar_names(self, processor: InputProcessor) -> None:
        """Cartão desconhecido deve listar nomes similares."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1,Cruzinha", "spread")
        err_str = str(exc_info.value)
        assert "Cruzinha" in err_str
        # Deve mostrar sugestões de nomes válidos
        assert "Cards válidos:" in err_str

    def test_error_message_recovery_field_contains_card_list(
        self, processor: InputProcessor
    ) -> None:
        """O campo recovery deve conter lista de cards válidos."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1,Xyz", "spread")
        err = exc_info.value
        assert err.recovery is not None
        # Recovery deve ter sugestões de cards
        assert "Cards válidos:" in err.recovery

    def test_parse_error_shows_line_number_for_csv_errors(
        self, processor: InputProcessor
    ) -> None:
        """Erros em CSV devem mostrar número da linha."""
        csv_with_error = "1,Cruz\ndois,Estrela\n3,Café"
        with pytest.raises(ParseError) as exc_info:
            processor.parse(csv_with_error, "spread")
        err_str = str(exc_info.value)
        # Deve indicar a linha com erro
        assert "linha" in err_str.lower()

    def test_invalid_csv_format_shows_expected_format(
        self, processor: InputProcessor
    ) -> None:
        """CSV mal formatado deve mostrar o formato esperado."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("abc\ndef", "spread")
        err_str = str(exc_info.value)
        # Deve mostrar formato esperado
        assert "POSITION,CARD" in err_str or "Formato esperado" in err_str

    def test_empty_csv_shows_recovery_hint(self, processor: InputProcessor) -> None:
        """CSV vazio deve mostrar hint de recuperação."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("", "spread")
        err = exc_info.value
        assert err.recovery is not None
        # Deve ter sugestões de formato
        assert "pos,carta" in err.recovery.lower() or "formato" in err.recovery.lower()

    def test_csv_without_separator_shows_format_hint(self, processor: InputProcessor) -> None:
        """Linha sem separador deve mostrar hint de formato."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1 Cruz", "spread")
        err_str = str(exc_info.value)
        # Deve sugerir o uso de separadores
        assert "vírgula" in err_str.lower() or "separador" in err_str.lower() or "POSITION,CARD" in err_str

    def test_negative_position_shows_recovery(self, processor: InputProcessor) -> None:
        """Posição negativa deve mostrar hint de valores válidos."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("-1,Cruz", "spread")
        err = exc_info.value
        assert err.recovery is not None
        # Deve sugerir valores válidos
        assert "1" in err.recovery or "positivo" in err.recovery.lower() or "maior" in err.recovery.lower()

    def test_zero_position_shows_recovery(self, processor: InputProcessor) -> None:
        """Posição zero deve mostrar hint de valores válidos."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("0,Cruz", "spread")
        err = exc_info.value
        assert err.recovery is not None
        # Deve indicar que posições começam em 1
        assert "1" in err.recovery or "positivo" in err.recovery.lower() or "maior" in err.recovery.lower()

    def test_missing_card_name_shows_example(self, processor: InputProcessor) -> None:
        """Nome de carta ausente deve mostrar exemplo."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1,", "spread")
        err_str = str(exc_info.value)
        # Deve mostrar exemplo de formato
        assert "exemplo" in err_str.lower() or "estrela" in err_str.lower()

    def test_file_not_found_error_has_recovery(self, processor: InputProcessor) -> None:
        """Erro de arquivo não encontrado deve ter hint de recuperação."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse_from_file("/caminho/inexistente.csv")
        err = exc_info.value
        assert err.recovery is not None
        # Deve verificar o caminho ou extensão
        assert ".csv" in err.recovery or ".txt" in err.recovery or "caminho" in err.recovery.lower()

    def test_template_not_found_error_has_recovery(self, processor: InputProcessor) -> None:
        """Erro de template não encontrado deve ter hint de valores válidos."""
        csv_content = "pos,carta\n1,A Cruz\n2,A Estrela"
        # Primeiro parsear o CSV para ter cards
        result = processor.parse(csv_content, "spread")
        assert result.cards is not None
        # Agora tentar aplicar template inexistente
        with pytest.raises(ParseError) as exc_info:
            processor._apply_template_context(result, "template-inexistente")
        err = exc_info.value
        assert err.recovery is not None
        # Deve listar templates válidos
        assert "3-card" in err.recovery or "celtic-cross" in err.recovery or "simple" in err.recovery

    def test_non_numeric_position_shows_format_hint(self, processor: InputProcessor) -> None:
        """Posição não-numérica deve mostrar hint de formato."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("abc,Cruz", "spread")
        err_str = str(exc_info.value)
        # Deve indicar que a primeira coluna deve ser numérica
        assert "número" in err_str.lower() or "inteiro" in err_str.lower() or "POSITION" in err_str

    def test_csv_without_data_after_header_shows_recovery(
        self, processor: InputProcessor
    ) -> None:
        """CSV com apenas cabeçalho sem dados deve mostrar recovery."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("pos,carta", "spread")
        err = exc_info.value
        assert err.recovery is not None
        # Deve indicar que precisa de dados
        assert "dados" in err.recovery.lower() or "linha" in err.recovery.lower()


# ----------------------------------------------------------------------
# Testes — Cross-validation de sugestões
# ----------------------------------------------------------------------


class TestSuggestionIntegration:
    """Testes de integração para verificar que sugestões funcionam corretamente."""

    def test_multiple_unknown_cards_each_get_suggestions(
        self, processor: InputProcessor
    ) -> None:
        """Cada carta desconhecida deve ter suas próprias sugestões."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1,Xyz\n2,Abc\n3,Cruz", "spread")
        err_str = str(exc_info.value)
        # Primeira carta desconhecida é 'Xyz'
        assert "Xyz" in err_str

    def test_partial_match_card_name_suggests_similar(
        self, processor: InputProcessor
    ) -> None:
        """Nome parcialmente correto deve sugerir matches similares."""
        with pytest.raises(ParseError) as exc_info:
            processor.parse("1,Cor", "spread")
        err_str = str(exc_info.value)
        # Deve mostrar cards que contém "Cor" como sugestão
        assert "Cards válidos:" in err_str

    def test_exact_card_name_no_error(self, processor: InputProcessor) -> None:
        """Nome de carta correto não deve gerar erro de desconhecido."""
        result = processor.parse("1,A Cruz\n2,A Estrela\n3,A Casa", "spread")
        assert len(result.cards) == 3
        assert result.cards[0].card_name == "A Cruz"

    def test_case_insensitive_card_name_gets_suggestion(
        self, processor: InputProcessor
    ) -> None:
        """Nome de carta com case diferente deve encontrar match."""
        result = processor.parse("1,A CRUZ\n2,a estrela\n3,a casa", "spread")
        assert len(result.cards) == 3
        assert result.cards[0].card_name == "A CRUZ"
        assert result.cards[1].card_name == "a estrela"

    def test_accented_card_name_works(self, processor: InputProcessor) -> None:
        """Nomes de cartas com acentos devem funcionar."""
        result = processor.parse("1,A Árvore\n2,A Casa\n3,A Estrela", "spread")
        # Deve funcionar com acentos
        assert len(result.cards) == 3
        assert result.cards[0].card_name == "A Árvore"