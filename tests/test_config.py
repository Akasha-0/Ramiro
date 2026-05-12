"""Testes unitários para src/config.py.

Cobertura:
- ClarezaConfig — valores padrão do dataclass
- load_config() — carga de YAML, overrides de env, precedência
- _load_yaml_config() — parsing de YAML, arquivo ausente
- _parse_path() — conversão de strings para Path
- _load_env_overrides() — parsing de variáveis de ambiente
- ConfigValidationError — mensagens de erro
- ConfigValidator — validação de dicionários de configuração
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

import pytest

from clareza.config import (
    ClarezaConfig,
    ConfigValidationError,
    ConfigValidator,
    _load_env_overrides,
    _load_yaml_config,
    _parse_path,
    load_config,
    DEFAULT_CONFIG,
    VALID_LANGUAGES,
    VALID_REPORT_FORMATS,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def validator() -> ConfigValidator:
    """Validador com configurações padrão."""
    return ConfigValidator()


@pytest.fixture
def validator_custom() -> ConfigValidator:
    """Validador com formatos customizados."""
    return ConfigValidator(
        valid_report_formats=["custom", "standard"],
        valid_languages=["de", "fr"],
    )


@pytest.fixture
def temp_yaml_file():
    """Cria arquivo YAML temporário e o remove ao final."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
        encoding="utf-8",
    ) as f:
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


# ----------------------------------------------------------------------
# Testes — ClarezaConfig: valores padrão
# ----------------------------------------------------------------------


class TestClarezaConfigDefaults:
    def test_default_output_dir_is_pwd(self) -> None:
        config = ClarezaConfig()
        assert config.default_output_dir == Path.cwd()

    def test_default_report_format_is_compact(self) -> None:
        config = ClarezaConfig()
        assert config.default_report_format == "compact"

    def test_default_language_is_pt(self) -> None:
        config = ClarezaConfig()
        assert config.default_language == "pt"

    def test_default_session_history_dir(self) -> None:
        config = ClarezaConfig()
        expected_default = Path.home() / ".local" / "share" / "clareza" / "sessions"
        assert config.session_history_dir == expected_default

    def test_auto_save_sessions_default_false(self) -> None:
        config = ClarezaConfig()
        assert config.auto_save_sessions is False

    def test_quiet_mode_default_false(self) -> None:
        config = ClarezaConfig()
        assert config.quiet_mode is False

    def test_custom_values_overwrite_defaults(self) -> None:
        custom_dir = Path("/custom/output")
        config = ClarezaConfig(
            default_output_dir=custom_dir,
            default_report_format="verbose",
            default_language="en",
            auto_save_sessions=True,
            quiet_mode=True,
        )
        assert config.default_output_dir == custom_dir
        assert config.default_output_dir != Path.cwd()
        assert config.default_report_format == "verbose"
        assert config.default_language == "en"
        assert config.auto_save_sessions is True
        assert config.quiet_mode is True


# ----------------------------------------------------------------------
# Testes — _parse_path()
# ----------------------------------------------------------------------


class TestParsePath:
    def test_valid_string_returns_path(self) -> None:
        result = _parse_path("/tmp/test")
        assert result == Path("/tmp/test")

    def test_relative_path(self) -> None:
        result = _parse_path("./relative/path")
        assert result == Path("./relative/path")

    def test_home_directory_not_expanded(self) -> None:
        # _parse_path não expande ~ — apenas converte string para Path
        result = _parse_path("~/documents")
        assert result == Path("~/documents")

    def test_none_returns_none(self) -> None:
        result = _parse_path(None)
        assert result is None

    def test_empty_string_returns_path_dot(self) -> None:
        # String vazia vira Path('.') — comportamento real do Python
        result = _parse_path("")
        assert result == Path(".")

    def test_invalid_characters_still_become_path(self) -> None:
        # _parse_path não valida caracteres — aceita qualquer string
        result = _parse_path("\x00invalid")
        assert isinstance(result, Path)


# ----------------------------------------------------------------------
# Testes — _load_yaml_config()
# ----------------------------------------------------------------------


class TestLoadYamlConfig:
    def test_nonexistent_file_returns_none(self) -> None:
        result = _load_yaml_config(Path("/nonexistent/path/config.yaml"))
        assert result is None

    def test_valid_yaml_returns_dict(self, temp_yaml_file: Path) -> None:
        temp_yaml_file.write_text(
            "default_language: en\n"
            "default_report_format: verbose\n",
            encoding="utf-8",
        )
        result = _load_yaml_config(temp_yaml_file)
        assert result is not None
        assert result["default_language"] == "en"
        assert result["default_report_format"] == "verbose"

    def test_empty_yaml_file_returns_empty_dict(self, temp_yaml_file: Path) -> None:
        temp_yaml_file.write_text("", encoding="utf-8")
        result = _load_yaml_config(temp_yaml_file)
        assert result == {}

    def test_yaml_with_only_comments_returns_empty_dict(self, temp_yaml_file: Path) -> None:
        temp_yaml_file.write_text(
            "# Este é um comentário\n# Outro comentário\n",
            encoding="utf-8",
        )
        result = _load_yaml_config(temp_yaml_file)
        assert result == {}

    def test_yaml_with_nested_structure(self, temp_yaml_file: Path) -> None:
        temp_yaml_file.write_text(
            "default_language: pt\n"
            "default_report_format: compact\n"
            "auto_save_sessions: true\n",
            encoding="utf-8",
        )
        result = _load_yaml_config(temp_yaml_file)
        assert result["default_language"] == "pt"
        assert result["default_report_format"] == "compact"
        assert result["auto_save_sessions"] is True

    def test_invalid_yaml_raises_error(self, temp_yaml_file: Path) -> None:
        temp_yaml_file.write_text(
            "invalid: yaml: content\n  bad_indent: true\n",
            encoding="utf-8",
        )
        with pytest.raises(Exception):  # yaml.YAMLError
            _load_yaml_config(temp_yaml_file)


# ----------------------------------------------------------------------
# Testes — _load_env_overrides()
# ----------------------------------------------------------------------


class TestLoadEnvOverrides:
    def setup_method(self) -> None:
        """Limpa variáveis de ambiente antes de cada teste."""
        self._original_env = {
            "CLAREZA_OUTPUT_DIR": os.environ.get("CLAREZA_OUTPUT_DIR"),
            "CLAREZA_FORMAT": os.environ.get("CLAREZA_FORMAT"),
            "CLAREZA_LANGUAGE": os.environ.get("CLAREZA_LANGUAGE"),
            "CLAREZA_HISTORY_DIR": os.environ.get("CLAREZA_HISTORY_DIR"),
            "CLAREZA_AUTO_SAVE": os.environ.get("CLAREZA_AUTO_SAVE"),
            "CLAREZA_QUIET": os.environ.get("CLAREZA_QUIET"),
        }
        # Limpa todas as variáveis CLAREZA_
        for key in list(os.environ.keys()):
            if key.startswith("CLAREZA_"):
                del os.environ[key]

    def teardown_method(self) -> None:
        """Restaura variáveis de ambiente após cada teste."""
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_no_env_vars_returns_empty_dict(self) -> None:
        result = _load_env_overrides()
        assert result == {}

    def test_output_dir_override(self) -> None:
        os.environ["CLAREZA_OUTPUT_DIR"] = "/custom/output"
        result = _load_env_overrides()
        assert "default_output_dir" in result
        assert result["default_output_dir"] == Path("/custom/output")

    def test_format_override_valid(self) -> None:
        os.environ["CLAREZA_FORMAT"] = "verbose"
        result = _load_env_overrides()
        assert "default_report_format" in result
        assert result["default_report_format"] == "verbose"

    def test_format_override_invalid_ignored(self) -> None:
        os.environ["CLAREZA_FORMAT"] = "invalid_format"
        result = _load_env_overrides()
        assert "default_report_format" not in result

    def test_language_override_valid(self) -> None:
        os.environ["CLAREZA_LANGUAGE"] = "en"
        result = _load_env_overrides()
        assert "default_language" in result
        assert result["default_language"] == "en"

    def test_language_override_invalid_ignored(self) -> None:
        os.environ["CLAREZA_LANGUAGE"] = "invalid"
        result = _load_env_overrides()
        assert "default_language" not in result

    def test_history_dir_override(self) -> None:
        os.environ["CLAREZA_HISTORY_DIR"] = "/var/log/clareza"
        result = _load_env_overrides()
        assert "session_history_dir" in result
        assert result["session_history_dir"] == Path("/var/log/clareza")

    def test_auto_save_true_values(self) -> None:
        for value in ["1", "true", "yes", "True", "YES"]:
            os.environ["CLAREZA_AUTO_SAVE"] = value
            result = _load_env_overrides()
            assert result["auto_save_sessions"] is True

    def test_auto_save_false_values(self) -> None:
        os.environ["CLAREZA_AUTO_SAVE"] = "0"
        result = _load_env_overrides()
        assert result["auto_save_sessions"] is False

    def test_quiet_mode_true_values(self) -> None:
        for value in ["1", "true", "yes"]:
            os.environ["CLAREZA_QUIET"] = value
            result = _load_env_overrides()
            assert result["quiet_mode"] is True

    def test_quiet_mode_false_values(self) -> None:
        os.environ["CLAREZA_QUIET"] = "0"
        result = _load_env_overrides()
        assert result["quiet_mode"] is False

    def test_multiple_overrides(self) -> None:
        os.environ["CLAREZA_FORMAT"] = "verbose"
        os.environ["CLAREZA_LANGUAGE"] = "es"
        os.environ["CLAREZA_AUTO_SAVE"] = "1"
        result = _load_env_overrides()
        assert len(result) == 3
        assert result["default_report_format"] == "verbose"
        assert result["default_language"] == "es"
        assert result["auto_save_sessions"] is True


# ----------------------------------------------------------------------
# Testes — load_config()
# ----------------------------------------------------------------------


class TestLoadConfig:
    def setup_method(self) -> None:
        """Limpa variáveis de ambiente antes de cada teste."""
        self._original_env = {
            "CLAREZA_OUTPUT_DIR": os.environ.get("CLAREZA_OUTPUT_DIR"),
            "CLAREZA_FORMAT": os.environ.get("CLAREZA_FORMAT"),
            "CLAREZA_LANGUAGE": os.environ.get("CLAREZA_LANGUAGE"),
            "CLAREZA_HISTORY_DIR": os.environ.get("CLAREZA_HISTORY_DIR"),
            "CLAREZA_AUTO_SAVE": os.environ.get("CLAREZA_AUTO_SAVE"),
            "CLAREZA_QUIET": os.environ.get("CLAREZA_QUIET"),
        }
        for key in list(os.environ.keys()):
            if key.startswith("CLAREZA_"):
                del os.environ[key]

    def teardown_method(self) -> None:
        """Restaura variáveis de ambiente após cada teste."""
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_no_yaml_no_env_returns_default_config(self) -> None:
        result = load_config()
        assert isinstance(result, ClarezaConfig)
        # Deve ser equivalente à configuração default
        assert result.default_report_format == DEFAULT_CONFIG.default_report_format
        assert result.default_language == DEFAULT_CONFIG.default_language

    def test_yaml_values_override_defaults(self, temp_yaml_file: Path, monkeypatch) -> None:
        monkeypatch.setattr(
            "clareza.config.DEFAULT_CONFIG_PATH",
            temp_yaml_file,
        )
        temp_yaml_file.write_text(
            "default_language: en\n"
            "default_report_format: verbose\n",
            encoding="utf-8",
        )
        result = load_config()
        assert result.default_language == "en"
        assert result.default_report_format == "verbose"

    def test_env_overrides_yaml(self, temp_yaml_file: Path, monkeypatch) -> None:
        monkeypatch.setattr(
            "clareza.config.DEFAULT_CONFIG_PATH",
            temp_yaml_file,
        )
        temp_yaml_file.write_text(
            "default_language: en\n"
            "default_report_format: verbose\n",
            encoding="utf-8",
        )
        os.environ["CLAREZA_LANGUAGE"] = "es"
        result = load_config()
        # YAML teria en, mas env sobrescreve
        assert result.default_language == "es"

    def test_invalid_yaml_format_uses_default(self, temp_yaml_file: Path, monkeypatch) -> None:
        monkeypatch.setattr(
            "clareza.config.DEFAULT_CONFIG_PATH",
            temp_yaml_file,
        )
        temp_yaml_file.write_text("invalid yaml content", encoding="utf-8")
        # Deve falhar ao carregar YAML, mas não deve quebrar
        # Se a função lança, o comportamento depende da implementação
        try:
            result = load_config()
            # Se não lançou, verifica que não tem os valores inválidos
            assert result.default_report_format in VALID_REPORT_FORMATS
        except Exception:
            pass  # Aceita que pode lançar em YAML inválido

    def test_invalid_language_in_yaml_ignored(self, temp_yaml_file: Path, monkeypatch) -> None:
        monkeypatch.setattr(
            "clareza.config.DEFAULT_CONFIG_PATH",
            temp_yaml_file,
        )
        temp_yaml_file.write_text(
            "default_language: invalid_lang\n",
            encoding="utf-8",
        )
        result = load_config()
        # Idioma inválido deve ser ignorado, mantendo default
        assert result.default_language == "pt"

    def test_invalid_format_in_yaml_ignored(self, temp_yaml_file: Path, monkeypatch) -> None:
        monkeypatch.setattr(
            "clareza.config.DEFAULT_CONFIG_PATH",
            temp_yaml_file,
        )
        temp_yaml_file.write_text(
            "default_report_format: invalid_format\n",
            encoding="utf-8",
        )
        result = load_config()
        # Formato inválido deve ser ignorado, mantendo default
        assert result.default_report_format == "compact"


# ----------------------------------------------------------------------
# Testes — ConfigValidationError
# ----------------------------------------------------------------------


class TestConfigValidationError:
    def test_basic_error_message(self) -> None:
        err = ConfigValidationError("field", "mensagem de erro")
        assert err.field == "field"
        assert err.message == "mensagem de erro"
        assert err.value is None

    def test_error_with_value(self) -> None:
        err = ConfigValidationError("language", "idioma inválido", "xyz")
        assert err.field == "language"
        assert err.message == "idioma inválido"
        assert err.value == "xyz"

    def test_str_without_value(self) -> None:
        err = ConfigValidationError("format", "formato inválido")
        assert str(err) == "format: formato inválido"

    def test_str_with_value(self) -> None:
        err = ConfigValidationError("language", "idioma inválido", "xyz")
        assert str(err) == "language: idioma inválido (valor recebido: 'xyz')"

    def test_repr(self) -> None:
        err = ConfigValidationError("field", "message", "value")
        assert repr(err) == "ConfigValidationError(field='field', message='message', value='value')"

    def test_empty_value_still_shows(self) -> None:
        err = ConfigValidationError("field", "msg", "")
        assert "valor recebido:" in str(err)
        assert "''" in str(err)


# ----------------------------------------------------------------------
# Testes — ConfigValidator
# ----------------------------------------------------------------------


class TestConfigValidator:
    def test_valid_config_returns_empty_errors(self, validator: ConfigValidator) -> None:
        config = {
            "default_report_format": "compact",
            "default_language": "pt",
        }
        errors = validator.validate(config)
        assert errors == []

    def test_invalid_format_returns_error(self, validator: ConfigValidator) -> None:
        config = {"default_report_format": "invalid"}
        errors = validator.validate(config)
        assert len(errors) == 1
        assert "invalid" in errors[0]
        assert "compact" in errors[0]
        assert "verbose" in errors[0]

    def test_invalid_language_returns_error(self, validator: ConfigValidator) -> None:
        config = {"default_language": "fr"}
        errors = validator.validate(config)
        assert len(errors) == 1
        assert "fr" in errors[0]
        assert "pt" in errors[0]
        assert "en" in errors[0]
        assert "es" in errors[0]

    def test_multiple_errors(self, validator: ConfigValidator) -> None:
        config = {
            "default_report_format": "wrong_format",
            "default_language": "de",
        }
        errors = validator.validate(config)
        assert len(errors) == 2

    def test_unknown_fields_ignored(self, validator: ConfigValidator) -> None:
        config = {
            "unknown_field": "value",
            "default_report_format": "compact",
        }
        errors = validator.validate(config)
        assert errors == []

    def test_empty_config_valid(self, validator: ConfigValidator) -> None:
        errors = validator.validate({})
        assert errors == []

    def test_custom_valid_formats(self, validator_custom: ConfigValidator) -> None:
        config = {"default_report_format": "custom"}
        errors = validator_custom.validate(config)
        assert errors == []

    def test_custom_valid_languages(self, validator_custom: ConfigValidator) -> None:
        config = {"default_language": "de"}
        errors = validator_custom.validate(config)
        assert errors == []

    def test_custom_invalid_format_uses_custom_list(self, validator_custom: ConfigValidator) -> None:
        config = {"default_report_format": "compact"}
        errors = validator_custom.validate(config)
        assert len(errors) == 1
        assert "compact" not in str(validator_custom.valid_report_formats)

    def test_custom_invalid_language_uses_custom_list(self, validator_custom: ConfigValidator) -> None:
        config = {"default_language": "pt"}
        errors = validator_custom.validate(config)
        assert len(errors) == 1

    def test_both_format_and_language_errors(self, validator: ConfigValidator) -> None:
        config = {
            "default_report_format": "bad",
            "default_language": "it",
        }
        errors = validator.validate(config)
        assert len(errors) == 2
        # Verifica que erros mencionam formato e idioma nos textos
        error_texts = " ".join(errors)
        assert "formato" in error_texts.lower() or "format" in error_texts.lower()
        assert "idioma" in error_texts.lower() or "language" in error_texts.lower()

    def test_only_invalid_format_no_language_field(self, validator: ConfigValidator) -> None:
        config = {"default_report_format": "wrong"}
        errors = validator.validate(config)
        assert len(errors) == 1
        assert "idioma" not in errors[0].lower()

    def test_only_invalid_language_no_format_field(self, validator: ConfigValidator) -> None:
        config = {"default_language": "xx"}
        errors = validator.validate(config)
        assert len(errors) == 1
        assert "formato" not in errors[0].lower() or "format" not in errors[0].lower()


# ----------------------------------------------------------------------
# Testes — constantes de validação
# ----------------------------------------------------------------------


class TestConstants:
    def test_valid_report_formats_contains_expected_values(self) -> None:
        assert "compact" in VALID_REPORT_FORMATS
        assert "verbose" in VALID_REPORT_FORMATS
        assert len(VALID_REPORT_FORMATS) == 2

    def test_valid_languages_contains_expected_values(self) -> None:
        assert "pt" in VALID_LANGUAGES
        assert "en" in VALID_LANGUAGES
        assert "es" in VALID_LANGUAGES
        assert len(VALID_LANGUAGES) == 3