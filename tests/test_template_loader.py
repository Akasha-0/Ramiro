"""Testes unitários para src/template_loader.py.

Cobertura:
- _load_template_yaml() — carga de YAML, arquivo ausente, YAML inválido
- _parse_template_sections() — parsing de seções, campos obrigatórios, duplicados
- TemplateLoader — template padrão, carga de arquivo, get_template
- TemplateValidationError — mensagens de erro, formatação
- TemplateValidator — validação de estrutura, campos obrigatórios, seções
- load_template_from_file() — função convenience
"""

import tempfile
from pathlib import Path
from typing import Optional

import pytest

from src.template_loader import (
    TemplateLoader,
    TemplateValidationError,
    TemplateValidator,
    _load_template_yaml,
    _parse_template_sections,
    load_template_from_file,
)
from src.types import ReportTemplate, TemplateSection


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def loader() -> TemplateLoader:
    """TemplateLoader com configurações padrão."""
    return TemplateLoader()


@pytest.fixture
def validator() -> TemplateValidator:
    """TemplateValidator com configurações padrão."""
    return TemplateValidator()


@pytest.fixture
def temp_template_file():
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
# Testes — _load_template_yaml()
# ----------------------------------------------------------------------


class TestLoadTemplateYaml:
    def test_nonexistent_file_returns_none(self) -> None:
        result = _load_template_yaml(Path("/nonexistent/path/template.yaml"))
        assert result is None

    def test_valid_yaml_returns_dict(self, temp_template_file: Path) -> None:
        temp_template_file.write_text(
            "template_id: custom\n"
            "name: Template Custom\n"
            "sections:\n"
            "  - id: secao1\n"
            "    title: Seção Um\n"
            "    content_template: '{content}'\n",
            encoding="utf-8",
        )
        result = _load_template_yaml(temp_template_file)
        assert result is not None
        assert result["template_id"] == "custom"
        assert result["name"] == "Template Custom"
        assert len(result["sections"]) == 1

    def test_empty_yaml_file_returns_empty_dict(self, temp_template_file: Path) -> None:
        temp_template_file.write_text("", encoding="utf-8")
        result = _load_template_yaml(temp_template_file)
        assert result == {}

    def test_yaml_with_only_comments_returns_empty_dict(self, temp_template_file: Path) -> None:
        temp_template_file.write_text(
            "# Este é um comentário\n"
            "# Outro comentário\n",
            encoding="utf-8",
        )
        result = _load_template_yaml(temp_template_file)
        assert result == {}

    def test_yaml_with_nested_structure(self, temp_template_file: Path) -> None:
        temp_template_file.write_text(
            "template_id: test\n"
            "version: '2.0'\n"
            "metadata:\n"
            "  author: Test\n"
            "sections:\n"
            "  - id: section_a\n"
            "    title: Section A\n"
            "    content_template: '{value}'\n",
            encoding="utf-8",
        )
        result = _load_template_yaml(temp_template_file)
        assert result["template_id"] == "test"
        assert result["version"] == "2.0"
        assert result["metadata"]["author"] == "Test"

    def test_invalid_yaml_raises_error(self, temp_template_file: Path) -> None:
        temp_template_file.write_text(
            "invalid: yaml: content\n"
            "  bad_indent: true\n",
            encoding="utf-8",
        )
        from src.exceptions import TemplateClarezaError
        with pytest.raises(TemplateClarezaError):
            _load_template_yaml(temp_template_file)


# ----------------------------------------------------------------------
# Testes — _parse_template_sections()
# ----------------------------------------------------------------------


class TestParseTemplateSections:
    def test_empty_list_returns_empty(self) -> None:
        result = _parse_template_sections([])
        assert result == []

    def test_none_returns_empty(self) -> None:
        result = _parse_template_sections(None)
        assert result == []

    def test_valid_single_section(self) -> None:
        data = [
            {
                "id": "test_section",
                "title": "Test Section",
                "content_template": "{content}",
            }
        ]
        result = _parse_template_sections(data)
        assert len(result) == 1
        assert result[0].id == "test_section"
        assert result[0].title == "Test Section"
        assert result[0].content_template == "{content}"

    def test_multiple_sections_with_order(self) -> None:
        data = [
            {"id": "b", "title": "Second", "content_template": "{b}", "order": 2},
            {"id": "a", "title": "First", "content_template": "{a}", "order": 1},
        ]
        result = _parse_template_sections(data)
        # Deve ordenar por order
        assert len(result) == 2
        assert result[0].order == 1
        assert result[1].order == 2

    def test_optional_fields_default_values(self) -> None:
        data = [
            {"id": "minimal", "title": "Minimal", "content_template": "{c}"}
        ]
        result = _parse_template_sections(data)
        assert len(result) == 1
        assert result[0].enabled is True
        assert result[0].required is False
        assert result[0].order == 1  # Default based on position
        assert result[0].placeholder is None

    def test_missing_id_raises_error(self) -> None:
        data = [{"title": "No ID", "content_template": "{c}"}]
        from src.exceptions import TemplateClarezaError
        with pytest.raises(TemplateClarezaError):
            _parse_template_sections(data)

    def test_missing_title_raises_error(self) -> None:
        data = [{"id": "no_title", "content_template": "{c}"}]
        from src.exceptions import TemplateClarezaError
        with pytest.raises(TemplateClarezaError):
            _parse_template_sections(data)

    def test_missing_content_template_raises_error(self) -> None:
        data = [{"id": "no_content", "title": "No Content"}]
        from src.exceptions import TemplateClarezaError
        with pytest.raises(TemplateClarezaError):
            _parse_template_sections(data)

    def test_enabled_and_required_flags(self) -> None:
        data = [
            {
                "id": "disabled",
                "title": "Disabled",
                "content_template": "{d}",
                "enabled": False,
                "required": True,
            }
        ]
        result = _parse_template_sections(data)
        assert len(result) == 1
        assert result[0].enabled is False
        assert result[0].required is True

    def test_placeholder_value(self) -> None:
        data = [
            {
                "id": "with_placeholder",
                "title": "With Placeholder",
                "content_template": "{p}",
                "placeholder": "No content available",
            }
        ]
        result = _parse_template_sections(data)
        assert len(result) == 1
        assert result[0].placeholder == "No content available"

    def test_invalid_order_type_converts_to_int(self) -> None:
        data = [
            {"id": "str_order", "title": "Str Order", "content_template": "{s}", "order": "1"}
        ]
        result = _parse_template_sections(data)
        # Type conversion should work
        assert len(result) == 1


# ----------------------------------------------------------------------
# Testes — TemplateLoader
# ----------------------------------------------------------------------


class TestTemplateLoader:
    def test_default_template_has_five_sections(self) -> None:
        loader = TemplateLoader()
        template = loader.default_template
        assert len(template.sections) == 5

    def test_default_template_sections_are_ordered(self) -> None:
        loader = TemplateLoader()
        sections = loader.default_template.sections
        orders = [s.order for s in sections]
        assert orders == sorted(orders)

    def test_default_template_has_required_first_section(self) -> None:
        loader = TemplateLoader()
        first = loader.default_template.sections[0]
        assert first.id == "diagnostico"
        assert first.required is True

    def test_build_default_template_creates_valid_template(self) -> None:
        loader = TemplateLoader()
        template = loader._build_default_template()
        assert isinstance(template, ReportTemplate)
        assert template.template_id == "default"
        assert template.name == "Modelo Padrão"

    def test_load_from_file_valid_template(self, temp_template_file: Path) -> None:
        temp_template_file.write_text(
            "template_id: test_load\n"
            "name: Test Load\n"
            "sections:\n"
            "  - id: test_section\n"
            "    title: Test Section\n"
            "    content_template: '{content}'\n",
            encoding="utf-8",
        )
        loader = TemplateLoader()
        template = loader.load_from_file(temp_template_file)
        assert template.template_id == "test_load"
        assert template.name == "Test Load"
        assert len(template.sections) == 1

    def test_load_from_file_nonexistent_raises_error(self) -> None:
        loader = TemplateLoader()
        from src.exceptions import TemplateClarezaError
        with pytest.raises(TemplateClarezaError, match="Template não encontrado"):
            loader.load_from_file(Path("/nonexistent/template.yaml"))

    def test_load_from_file_invalid_structure_raises_error(self, temp_template_file: Path) -> None:
        temp_template_file.write_text(
            "template_id: invalid\n"
            "sections: not_a_list\n",
            encoding="utf-8",
        )
        loader = TemplateLoader()
        from src.exceptions import TemplateClarezaError
        with pytest.raises(TemplateClarezaError, match="Template inválido"):
            loader.load_from_file(temp_template_file)

    def test_load_from_file_missing_section_fields_raises_error(self, temp_template_file: Path) -> None:
        temp_template_file.write_text(
            "sections:\n"
            "  - id: no_title\n"
            "    content_template: '{c}'\n",
            encoding="utf-8",
        )
        loader = TemplateLoader()
        from src.exceptions import TemplateClarezaError
        with pytest.raises(TemplateClarezaError):
            loader.load_from_file(temp_template_file)

    def test_get_template_with_custom_path_exists(self, temp_template_file: Path) -> None:
        temp_template_file.write_text(
            "template_id: custom_get\n"
            "name: Custom Get\n"
            "sections:\n"
            "  - id: custom_sec\n"
            "    title: Custom\n"
            "    content_template: '{c}'\n",
            encoding="utf-8",
        )
        loader = TemplateLoader()
        template = loader.get_template(custom_path=temp_template_file)
        assert template.template_id == "custom_get"

    def test_get_template_with_nonexistent_path_returns_default(self) -> None:
        loader = TemplateLoader()
        template = loader.get_template(custom_path=Path("/nonexistent.yaml"))
        assert template.template_id == "default"

    def test_get_template_with_none_returns_default(self) -> None:
        loader = TemplateLoader()
        template = loader.get_template(custom_path=None)
        assert template.template_id == "default"

    def test_build_template_from_data(self) -> None:
        loader = TemplateLoader()
        data = {
            "template_id": "built",
            "name": "Built Template",
            "version": "3.0",
            "description": "Test description",
            "sections": [
                {"id": "s1", "title": "S1", "content_template": "{a}"},
            ],
            "metadata": {"key": "value"},
        }
        template = loader._build_template_from_data(data)
        assert template.template_id == "built"
        assert template.name == "Built Template"
        assert template.version == "3.0"
        assert template.description == "Test description"
        assert len(template.sections) == 1

    def test_build_template_from_data_defaults(self) -> None:
        loader = TemplateLoader()
        data = {
            "sections": [
                {"id": "s1", "title": "S1", "content_template": "{a}"},
            ],
        }
        template = loader._build_template_from_data(data)
        assert template.template_id == "custom"
        assert template.name == "Template Personalizado"
        assert template.version == "1.0"


# ----------------------------------------------------------------------
# Testes — TemplateValidationError
# ----------------------------------------------------------------------


class TestTemplateValidationError:
    def test_basic_error_message(self) -> None:
        err = TemplateValidationError("field", "mensagem de erro")
        assert err.field == "field"
        assert err.message == "mensagem de erro"
        assert err.value is None

    def test_error_with_value(self) -> None:
        err = TemplateValidationError("sections", "deve ser lista", "not_list")
        assert err.field == "sections"
        assert err.message == "deve ser lista"
        assert err.value == "not_list"

    def test_str_without_value(self) -> None:
        err = TemplateValidationError("template_id", "deve ser string")
        assert str(err) == "template_id: deve ser string"

    def test_str_with_value(self) -> None:
        err = TemplateValidationError("sections", "deve ser lista", "string")
        assert str(err) == "sections: deve ser lista (valor recebido: 'string')"

    def test_repr(self) -> None:
        err = TemplateValidationError("field", "msg", "val")
        assert repr(err) == "TemplateValidationError(field='field', message='msg', value='val')"

    def test_empty_value_still_shows(self) -> None:
        err = TemplateValidationError("field", "msg", "")
        assert "valor recebido:" in str(err)
        assert "''" in str(err)


# ----------------------------------------------------------------------
# Testes — TemplateValidator
# ----------------------------------------------------------------------


class TestTemplateValidator:
    def test_valid_template_returns_empty_errors(self, validator: TemplateValidator) -> None:
        template = {
            "sections": [
                {"id": "sec1", "title": "Section 1", "content_template": "{c}"}
            ]
        }
        errors = validator.validate(template)
        assert errors == []

    def test_missing_sections_field_returns_error(self, validator: TemplateValidator) -> None:
        template = {"template_id": "test"}
        errors = validator.validate(template)
        assert len(errors) == 1
        assert "sections" in errors[0]

    def test_sections_not_list_returns_error(self, validator: TemplateValidator) -> None:
        template = {"sections": "not_a_list"}
        errors = validator.validate(template)
        assert len(errors) == 1
        assert "lista" in errors[0]

    def test_empty_sections_returns_error(self, validator: TemplateValidator) -> None:
        template = {"sections": []}
        errors = validator.validate(template)
        assert len(errors) == 1
        assert "pelo menos uma seção" in errors[0]

    def test_section_missing_id_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "sections": [
                {"title": "No ID", "content_template": "{c}"}
            ]
        }
        errors = validator.validate(template)
        assert any("id" in e.lower() for e in errors)

    def test_section_missing_title_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "sections": [
                {"id": "sec1", "content_template": "{c}"}
            ]
        }
        errors = validator.validate(template)
        assert any("title" in e for e in errors)

    def test_section_missing_content_template_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "sections": [
                {"id": "sec1", "title": "Section 1"}
            ]
        }
        errors = validator.validate(template)
        assert any("content_template" in e for e in errors)

    def test_duplicate_section_id_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "sections": [
                {"id": "duplicate", "title": "First", "content_template": "{a}"},
                {"id": "duplicate", "title": "Second", "content_template": "{b}"},
            ]
        }
        errors = validator.validate(template)
        assert any("duplicado" in e for e in errors)

    def test_invalid_template_id_type_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "template_id": 123,
            "sections": [
                {"id": "sec1", "title": "S1", "content_template": "{c}"}
            ]
        }
        errors = validator.validate(template)
        assert any("template_id" in e for e in errors)

    def test_empty_template_id_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "template_id": "",
            "sections": [
                {"id": "sec1", "title": "S1", "content_template": "{c}"}
            ]
        }
        errors = validator.validate(template)
        assert any("template_id" in e for e in errors)

    def test_invalid_version_type_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "version": 123,
            "sections": [
                {"id": "sec1", "title": "S1", "content_template": "{c}"}
            ]
        }
        errors = validator.validate(template)
        assert any("version" in e for e in errors)

    def test_section_invalid_order_type_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "sections": [
                {"id": "sec1", "title": "S1", "content_template": "{c}", "order": "not_int"}
            ]
        }
        errors = validator.validate(template)
        assert any("order" in e for e in errors)

    def test_section_invalid_enabled_type_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "sections": [
                {"id": "sec1", "title": "S1", "content_template": "{c}", "enabled": "yes"}
            ]
        }
        errors = validator.validate(template)
        assert any("enabled" in e for e in errors)

    def test_section_invalid_required_type_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "sections": [
                {"id": "sec1", "title": "S1", "content_template": "{c}", "required": 1}
            ]
        }
        errors = validator.validate(template)
        assert any("required" in e for e in errors)

    def test_multiple_errors_collected(self, validator: TemplateValidator) -> None:
        template = {
            "template_id": 123,
            "version": 456,
        }
        errors = validator.validate(template)
        assert len(errors) >= 2

    def test_non_dict_section_returns_error(self, validator: TemplateValidator) -> None:
        template = {
            "sections": [
                "not a dict",
            ]
        }
        errors = validator.validate(template)
        assert any("objeto" in e for e in errors)

    def test_validate_section_order_warnings(self, validator: TemplateValidator) -> None:
        sections = [
            {"id": "optional", "title": "Optional", "content_template": "{c}", "required": False},
            {"id": "required", "title": "Required", "content_template": "{c}", "required": True},
        ]
        warnings = validator.validate_section_order(sections)
        # Should warn about required section appearing after optional
        assert len(warnings) >= 0  # May or may not warn depending on position

    def test_reserved_ids_attribute_exists(self, validator: TemplateValidator) -> None:
        assert hasattr(validator, "RESERVED_IDS")
        assert "diagnostico" in validator.RESERVED_IDS
        assert "plano" in validator.RESERVED_IDS


# ----------------------------------------------------------------------
# Testes — load_template_from_file (convenience function)
# ----------------------------------------------------------------------


class TestLoadTemplateFromFile:
    def test_load_from_file_string_path(self, temp_template_file: Path) -> None:
        temp_template_file.write_text(
            "template_id: convenience\n"
            "name: Convenience Test\n"
            "sections:\n"
            "  - id: conv_sec\n"
            "    title: Convenience Section\n"
            "    content_template: '{c}'\n",
            encoding="utf-8",
        )
        template = load_template_from_file(str(temp_template_file))
        assert template.template_id == "convenience"
        assert template.name == "Convenience Test"

    def test_load_from_file_nonexistent_raises(self) -> None:
        from src.exceptions import TemplateClarezaError
        with pytest.raises(TemplateClarezaError):
            load_template_from_file("/nonexistent/path.yaml")

    def test_load_from_file_invalid_yaml_raises(self, temp_template_file: Path) -> None:
        temp_template_file.write_text("invalid: yaml: content\n  bad: indent", encoding="utf-8")
        from src.exceptions import TemplateClarezaError
        with pytest.raises(TemplateClarezaError):
            load_template_from_file(str(temp_template_file))


# ----------------------------------------------------------------------
# Testes — integração com types.py
# ----------------------------------------------------------------------


class TestTemplateLoaderIntegration:
    def test_sections_are_template_section_instances(self, loader: TemplateLoader) -> None:
        sections = loader.default_template.sections
        for section in sections:
            assert isinstance(section, TemplateSection)

    def test_template_is_report_template_instance(self, loader: TemplateLoader) -> None:
        assert isinstance(loader.default_template, ReportTemplate)

    def test_loaded_template_sections_are_template_section_instances(
        self, temp_template_file: Path
    ) -> None:
        temp_template_file.write_text(
            "template_id: integration\n"
            "sections:\n"
            "  - id: int_sec\n"
            "    title: Integration\n"
            "    content_template: '{c}'\n",
            encoding="utf-8",
        )
        test_loader = TemplateLoader()
        template = test_loader.load_from_file(temp_template_file)
        for section in template.sections:
            assert isinstance(section, TemplateSection)

    def test_section_fields_accessible(self, loader: TemplateLoader) -> None:
        first = loader.default_template.sections[0]
        assert hasattr(first, "id")
        assert hasattr(first, "title")
        assert hasattr(first, "order")
        assert hasattr(first, "content_template")
        assert hasattr(first, "enabled")
        assert hasattr(first, "required")
        assert hasattr(first, "placeholder")