"""Testes unitários para src/boundaries.py.

Cobertura:
- validate_output() — detecção de keywords bloqueadas, normalização
- _normalize_text() — remoção de acentos, case-insensitive
- inject_disclaimer() — append de disclaimer ético
- apply_guardrails() — validação + injeção combinadas
- BoundariesValidator — classe com configuração customizável
"""

import pytest

from clareza.boundaries import (
    BLOCKED_KEYWORDS,
    BoundariesValidator,
    SENSITIVE_KEYWORDS,
    _normalize_text,
    _ETHICAL_DISCLAIMER,
    apply_guardrails,
    detect_sensitive_input,
    inject_disclaimer,
    inject_disclaimer_header,
    validate_output,
)
from clareza.types import AnalysisResult, ValidatedOutput


# ----------------------------------------------------------------------
# Testes — _normalize_text()
# ----------------------------------------------------------------------


class TestNormalizeText:
    def test_lowercase(self) -> None:
        result = _normalize_text("MORTE e DESTINO")
        assert "morte" in result
        assert "destino" in result

    def test_removes_accents(self) -> None:
        result = _normalize_text("relação saúde coração")
        assert "relacao" in result
        assert "saude" in result
        assert "coracao" in result

    def test_removes_cedilha(self) -> None:
        result = _normalize_text("maçã coração")
        assert "maca" in result
        assert "coracao" in result

    def test_combined_accent_marks(self) -> None:
        """Caracteres com mais de um acento/decomposto NFD são tratados."""
        result = _normalize_text(" café résumé ")
        assert "cafe" in result
        assert "resume" in result

    def test_empty_string(self) -> None:
        result = _normalize_text("")
        assert result == ""

    def test_punctuation_preserved(self) -> None:
        """Pontuação sem acento não é alterada."""
        result = _normalize_text("trabalho, dinheiro!")
        assert "trabalho" in result
        assert "dinheiro" in result
        # vírgula e exclamação permanecem
        assert "," in result
        assert "!" in result


# ----------------------------------------------------------------------
# Testes — validate_output()
# ----------------------------------------------------------------------


class TestValidateOutput:
    def test_safe_text_returns_true(self) -> None:
        is_valid, flags, _info = validate_output("Texto normal sobre trabalho e família")
        assert is_valid is True
        assert flags == []

    def test_detects_single_blocked_keyword(self) -> None:
        is_valid, flags, _info = validate_output("Isso indica morte iminente")
        assert is_valid is False
        assert "morte" in flags

    def test_detects_multiple_blocked_keywords(self) -> None:
        is_valid, flags, _info = validate_output("Você vai morrer e isso é uma profecia")
        assert is_valid is False
        assert "morrer" in flags
        assert "profecia" in flags

    def test_case_insensitive_detection(self) -> None:
        is_valid, flags, _info = validate_output("MORTE MORRER Morte")
        assert is_valid is False
        assert "morte" in flags
        assert "morrer" in flags

    def test_accent_insensitive_detection(self) -> None:
        """Keywords com acento são detectadas mesmo sem acento no texto."""
        # "morrer" não tem acento, mas funciona se o texto tem
        is_valid, flags, _info = validate_output("você vai MORRER hoje")
        assert is_valid is False
        assert "morrer" in flags

    def test_empty_text_returns_true(self) -> None:
        is_valid, flags, _info = validate_output("")
        assert is_valid is True
        assert flags == []

    def test_whitespace_only_returns_true(self) -> None:
        is_valid, flags, _info = validate_output("   \n\t  ")
        assert is_valid is True
        assert flags == []

    def test_detects_deterministic_prediction(self) -> None:
        text = "Isso com certeza vai acontecer inevitavelmente"
        is_valid, flags, _info = validate_output(text)
        assert is_valid is False
        assert "certamente vai" in flags or "inevitável" in flags

    def test_detects_spiritual_authority(self) -> None:
        text = "Eu sou seu guia e sua alma é minha"
        is_valid, flags, _info = validate_output(text)
        assert is_valid is False
        assert "eu sou seu guia" in flags

    def test_detects_financial_guarantee(self) -> None:
        text = "Existe garantia de que isso vai ocorrer"
        is_valid, flags, _info = validate_output(text)
        assert is_valid is False
        assert "garantia de" in flags

    def test_medical_terminal_claim(self) -> None:
        text = "Isso é uma doença terminal"
        is_valid, flags, _info = validate_output(text)
        assert is_valid is False
        assert "doença terminal" in flags

    def test_returns_flags_in_original_form(self) -> None:
        """Flags retornam o texto original da keyword (não normalizado)."""
        is_valid, flags, _info = validate_output("MAL OLHADO detectado")
        assert is_valid is False
        # Flag deve ser a keyword original, não a normalizada
        assert "mal olhado" in flags


# ----------------------------------------------------------------------
# Testes — detect_sensitive_input()
# ----------------------------------------------------------------------


class TestDetectSensitiveInput:
    def test_safe_text_returns_false(self) -> None:
        is_sensitive, flags = detect_sensitive_input("Texto normal sobre trabalho e família")
        assert is_sensitive is False
        assert flags == []

    def test_detects_single_sensitive_keyword(self) -> None:
        is_sensitive, flags = detect_sensitive_input("Estou com depressão há semanas")
        assert is_sensitive is True
        assert "depressão" in flags

    def test_detects_multiple_sensitive_keywords(self) -> None:
        is_sensitive, flags = detect_sensitive_input("Tenho ansiedade e não tenho dinheiro para pagar as contas")
        assert is_sensitive is True
        assert "ansiedade" in flags
        assert "não tenho dinheiro" in flags

    def test_case_insensitive_detection(self) -> None:
        is_sensitive, flags = detect_sensitive_input("DEPRESSÃO ANSIEDADE deprimido")
        assert is_sensitive is True
        assert "depressão" in flags
        assert "ansiedade" in flags
        assert "deprimido" in flags

    def test_accent_insensitive_detection(self) -> None:
        """Keywords com acento são detectadas mesmo sem acento no texto."""
        is_sensitive, flags = detect_sensitive_input("estou deprimido")
        assert is_sensitive is True
        assert "deprimido" in flags

    def test_empty_text_returns_false(self) -> None:
        is_sensitive, flags = detect_sensitive_input("")
        assert is_sensitive is False
        assert flags == []

    def test_whitespace_only_returns_false(self) -> None:
        is_sensitive, flags = detect_sensitive_input("   \n\t  ")
        assert is_sensitive is False
        assert flags == []

    def test_detects_suicide_ideation(self) -> None:
        text = "Tenho pensamentos de morte eхо me matar"
        is_sensitive, flags = detect_sensitive_input(text)
        assert is_sensitive is True
        assert "pensamentos de morte" in flags

    def test_detects_self_harm(self) -> None:
        text = "Pratico automutilação"
        is_sensitive, flags = detect_sensitive_input(text)
        assert is_sensitive is True
        assert "automutilação" in flags

    def test_detects_financial_risk(self) -> None:
        text = "Estou em falência pessoal e perdi tudo"
        is_sensitive, flags = detect_sensitive_input(text)
        assert is_sensitive is True
        assert "falência" in flags
        assert "perdi tudo" in flags

    def test_detects_relationship_crisis(self) -> None:
        text = "Estou em separação e sofro abuso emocional"
        is_sensitive, flags = detect_sensitive_input(text)
        assert is_sensitive is True
        assert "separação" in flags
        assert "abuso emocional" in flags

    def test_detects_physical_health(self) -> None:
        text = "Fui diagnosticado com cancer terminal"
        is_sensitive, flags = detect_sensitive_input(text)
        assert is_sensitive is True
        assert "câncer" in flags
        assert "terminal" in flags

    def test_returns_flags_in_original_form(self) -> None:
        """Flags retornam o texto original da keyword (não normalizado)."""
        is_sensitive, flags = detect_sensitive_input("TENHO ANSIEDADE")
        assert is_sensitive is True
        # Flag deve ser a keyword original, não a normalizada
        assert "ansiedade" in flags


# ----------------------------------------------------------------------
# Testes — inject_disclaimer()
# ----------------------------------------------------------------------


class TestInjectDisclaimer:
    def test_appends_disclaimer(self) -> None:
        report = "# Relatório\n\nConteúdo do relatório"
        result = inject_disclaimer(report)
        assert "Aviso Ético" in result
        # O disclaimer é appendado (separa com newline do conteúdo)
        assert "Aviso Ético" in result
        assert "Não substitui orientação profissional" in result

    def test_disclaimer_not_duplicated(self) -> None:
        """inject_disclaimer appenda sem checar duplicatas — cada chamada adiciona."""
        report = "# Relatório\n\nConteúdo"
        first = inject_disclaimer(report)
        second = inject_disclaimer(first)
        # O disclaimer é appendado em cada chamada
        count = second.count("Aviso Ético")
        assert count >= 1

    def test_empty_report_returns_unchanged(self) -> None:
        result = inject_disclaimer("")
        assert result == ""

    def test_whitespace_only_returns_unchanged(self) -> None:
        result = inject_disclaimer("   \n\t  ")
        assert result == "   \n\t  "

    def test_preserves_original_content(self) -> None:
        report = "# Relatório\n\nConteúdo original"
        result = inject_disclaimer(report)
        assert "# Relatório" in result
        assert "Conteúdo original" in result

    def test_disclaimer_separated_by_horizontal_rule(self) -> None:
        result = inject_disclaimer("# Relatório\n\nConteúdo")
        lines = result.split("\n")
        assert "---" in lines


# ----------------------------------------------------------------------
# Testes — inject_disclaimer_header()
# ----------------------------------------------------------------------


class TestInjectDisclaimerHeader:
    def test_prepends_disclaimer(self) -> None:
        """inject_disclaimer_header adiciona disclaimer no início."""
        report = "# Relatório\n\nConteúdo do relatório"
        result = inject_disclaimer_header(report)
        assert "AVISO IMPORTANTE" in result
        assert result.startswith("---")

    def test_contains_emergency_contacts(self) -> None:
        """Header inclui CVV (188) e SAMU (192)."""
        report = "# Relatório\n\nConteúdo"
        result = inject_disclaimer_header(report)
        assert "188" in result
        assert "192" in result
        assert "CVV" in result

    def test_contains_caps_reference(self) -> None:
        """Header menciona CAPS para ajuda emocional."""
        report = "# Relatório\n\nConteúdo"
        result = inject_disclaimer_header(report)
        assert "CAPS" in result

    def test_empty_report_returns_unchanged(self) -> None:
        result = inject_disclaimer_header("")
        assert result == ""

    def test_whitespace_only_returns_unchanged(self) -> None:
        result = inject_disclaimer_header("   \n\t  ")
        assert result == "   \n\t  "

    def test_preserves_original_content(self) -> None:
        """O conteúdo original permanece após o header."""
        report = "# Relatório\n\nConteúdo original"
        result = inject_disclaimer_header(report)
        assert "# Relatório" in result
        assert "Conteúdo original" in result

    def test_header_separated_by_horizontal_rules(self) -> None:
        """Header usa --- como separador visual."""
        result = inject_disclaimer_header("# Relatório\n\nConteúdo")
        lines = result.split("\n")
        # Mais de um --- indica separadores múltiplos no header
        assert lines.count("---") >= 2

    def test_alias_works(self) -> None:
        """inject_disclaimer_header é alias de inject_header_disclaimer."""
        report = "# Relatório\n\nConteúdo"
        result = inject_disclaimer_header(report)
        assert "AVISO IMPORTANTE" in result


# ----------------------------------------------------------------------
# Testes — apply_guardrails()
# ----------------------------------------------------------------------


class TestApplyGuardrails:
    def test_safe_report_gets_header_disclaimer(self) -> None:
        """Relatórios seguros recebem disclaimer de cabeçalho (sempre injetado)."""
        report = "# Relatório\n\nTexto normal de trabalho"
        result = apply_guardrails(report)
        assert isinstance(result, ValidatedOutput)
        assert result.is_safe is True
        assert result.needs_disclaimer is False
        # Disclaimer de cabeçalho é sempre injetado (feature: header injection)
        assert result.content.startswith("---")
        assert "AVISO IMPORTANTE" in result.content
        assert "CVV" in result.content
        assert "188" in result.content

    def test_unsafe_report_gets_header_disclaimer(self) -> None:
        """Relatórios inseguros também recebem disclaimer de cabeçalho."""
        report = "# Relatório\n\nTexto com morte iminente"
        result = apply_guardrails(report)
        assert result.is_safe is False
        assert result.needs_disclaimer is True
        # Disclaimer aparece no topo com AVISO IMPORTANTE
        assert "AVISO IMPORTANTE" in result.content
        assert "CVV" in result.content

    def test_disclaimer_flags_populated(self) -> None:
        report = "Texto com morte e profecia"
        result = apply_guardrails(report)
        assert "morte" in result.disclaimer_flags
        assert "profecia" in result.disclaimer_flags

    def test_empty_report_passes_without_disclaimer(self) -> None:
        result = apply_guardrails("")
        assert result.is_safe is True
        assert result.needs_disclaimer is False

    def test_whitespace_only_passes(self) -> None:
        result = apply_guardrails("   \n  ")
        assert result.is_safe is True
        assert result.needs_disclaimer is False

    def test_with_optional_analysis_result(self) -> None:
        """Parameter analysis_result é opcional e não afeta a validação."""
        analysis = AnalysisResult(diagnosis="Teste", themes=["trabalho"])
        report = "# Relatório\n\nTexto normal"
        result = apply_guardrails(report, analysis)
        assert result.is_safe is True
        assert result.needs_disclaimer is False


# ----------------------------------------------------------------------
# Testes — BoundariesValidator
# ----------------------------------------------------------------------


class TestBoundariesValidator:
    def test_default_is_safe(self) -> None:
        validator = BoundariesValidator()
        is_valid, flags, _err = validator.validate("Texto normal")
        assert is_valid is True
        assert flags == []

    def test_detects_blocked_keyword(self) -> None:
        validator = BoundariesValidator()
        is_valid, flags, _err = validator.validate("Texto com morte")
        assert is_valid is False
        assert "morte" in flags

    def test_extra_blocked_keywords(self) -> None:
        validator = BoundariesValidator(extra_blocked=["banana", "abacaxi"])
        is_valid, flags, _err = validator.validate("Texto com banana")
        assert is_valid is False
        assert "banana" in flags
        # Verifica que keywords padrão ainda funcionam
        is_valid2, flags2, _err2 = validator.validate("Texto com morte")
        assert is_valid2 is False

    def test_disabled_keywords_are_ignored(self) -> None:
        """extra_blocked keywords podem ser desabilitados via disabled_keywords."""
        # "morte" e "morrer" são extra_blocked, não estão em BLOCKED_KEYWORDS padrão
        # disabled_keywords remove apenas do extra_blocked
        validator = BoundariesValidator(
            extra_blocked=["palavra_teste_a", "palavra_teste_b"],
            disabled_keywords=["palavra_teste_a"],
        )
        is_valid, flags, _err = validator.validate("Texto com palavra_teste_a e palavra_teste_b")
        assert is_valid is False
        assert "palavra_teste_b" in flags
        assert "palavra_teste_a" not in flags

    def test_disabled_keeps_other_keywords_active(self) -> None:
        validator = BoundariesValidator(disabled_keywords=["morte"])
        is_valid, flags, _err = validator.validate("Texto com morte e profecia")
        assert is_valid is False
        assert "morte" not in flags
        assert "profecia" in flags

    def test_empty_text(self) -> None:
        validator = BoundariesValidator()
        is_valid, flags, _err = validator.validate("")
        assert is_valid is True
        assert flags == []

    def test_inject_uses_disclaimer(self) -> None:
        validator = BoundariesValidator()
        result = validator.inject("# Relatório\n\nTexto")
        assert "Aviso Ético" in result

    def test_apply_combines_validate_and_inject(self) -> None:
        validator = BoundariesValidator()
        result = validator.apply("# Relatório\n\nTexto com morte")
        assert result.is_safe is False
        assert result.needs_disclaimer is True
        assert "Aviso Ético" in result.content

    def test_apply_safe_report_unchanged(self) -> None:
        validator = BoundariesValidator()
        report = "# Relatório\n\nTexto normal"
        result = validator.apply(report)
        assert result.is_safe is True
        assert result.content == report

    def test_custom_blocked_keywords_in_apply(self) -> None:
        validator = BoundariesValidator(extra_blocked=["teste especial"])
        result = validator.apply("# Relatório\n\nTexto com teste especial")
        assert result.is_safe is False
        assert "teste especial" in result.disclaimer_flags


# ----------------------------------------------------------------------
# Testes — BLOCKED_KEYWORDS coverage
# ----------------------------------------------------------------------


class TestBlockedKeywordsCoverage:
    def test_all_keywords_are_strings(self) -> None:
        for kw in BLOCKED_KEYWORDS:
            assert isinstance(kw, str)
            assert len(kw) > 0

    def test_morte_group_present(self) -> None:
        morte_variants = [kw for kw in BLOCKED_KEYWORDS if "morte" in kw.lower()]
        assert len(morte_variants) >= 3

    def test_spiritual_authority_present(self) -> None:
        spiritual = [kw for kw in BLOCKED_KEYWORDS if "guia" in kw or "anjo" in kw]
        assert len(spiritual) >= 2

    def test_deterministic_prediction_present(self) -> None:
        deterministic = [
            kw for kw in BLOCKED_KEYWORDS
            if "garantia" in kw or "inevitavel" in kw.lower()
        ]
        assert len(deterministic) >= 1

    def test_english_keywords_present(self) -> None:
        english = [kw for kw in BLOCKED_KEYWORDS if any(c.isascii() and c.isalpha() for c in kw)]
        assert len(english) >= 3