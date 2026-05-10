"""Loader de templates YAML — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por carregar e validar templates de relatório
a partir de arquivos YAML. Suporta templates personalizados com
seções configuráveis.

Patterns from:
    src/config.py (_load_yaml_config, ConfigValidator)
    src/exceptions.py (TemplateClarezaError)
    src/types.py (ReportTemplate, TemplateSection)
"""

import logging
from pathlib import Path
from typing import Optional

from src.exceptions import TemplateClarezaError
from src.types import ReportTemplate, TemplateSection

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Funções de carga YAML
# ----------------------------------------------------------------------


def _load_template_yaml(template_path: Path) -> Optional[dict]:
    """Carrega template YAML do arquivo especificado.

    Args:
        template_path: Caminho para o arquivo YAML de template.

    Returns:
        Dicionário com dados do YAML, ou None se o arquivo não existir.
    Raises:
        TemplateClarezaError: Se o arquivo existir mas não puder ser parseado.
    """
    import yaml  # Lazy import para permitir uso sem PyYAML quando não necessário

    if not template_path.exists():
        logger.debug("Template não encontrado: %s", template_path)
        return None

    logger.debug("Carregando template de: %s", template_path)
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.warning("Erro ao ler YAML de %s: %s", template_path, e)
        raise TemplateClarezaError(
            "Template YAML inválido",
            details=f"Erro de parse na linha {getattr(e, 'problem_mark', None) or 'desconhecida'}: {e}"
        )


def _parse_template_sections(sections_data: list[dict]) -> list[TemplateSection]:
    """Converte dados de seção cru em objetos TemplateSection.

    Args:
        sections_data: Lista de dicionários com dados de seção.

    Returns:
        Lista de TemplateSection validados.

    Raises:
        TemplateClarezaError: Se os dados forem inválidos.
    """
    if not sections_data:
        return []

    sections: list[TemplateSection] = []
    for i, section_data in enumerate(sections_data):
        # Validar campos obrigatórios
        if "id" not in section_data:
            raise TemplateClarezaError(
                "Seção inválida",
                details=f"Seção {i} missing campo 'id'"
            )
        if "title" not in section_data:
            raise TemplateClarezaError(
                "Seção inválida",
                details=f"Seção '{section_data['id']}' missing campo 'title'"
            )
        if "content_template" not in section_data:
            raise TemplateClarezaError(
                "Seção inválida",
                details=f"Seção '{section_data['id']}' missing campo 'content_template'"
            )

        try:
            section = TemplateSection(
                id=str(section_data["id"]),
                title=str(section_data["title"]),
                order=int(section_data.get("order", i + 1)),
                content_template=str(section_data["content_template"]),
                enabled=bool(section_data.get("enabled", True)),
                required=bool(section_data.get("required", False)),
                placeholder=section_data.get("placeholder"),
            )
            sections.append(section)
        except (ValueError, TypeError) as e:
            raise TemplateClarezaError(
                "Seção inválida",
                details=f"Erro ao processar seção '{section_data.get('id', i)}': {e}"
            )

    # Ordenar por ordem
    sections.sort(key=lambda s: s.order)
    return sections


# ----------------------------------------------------------------------
# Template Loader
# ----------------------------------------------------------------------


class TemplateLoader:
    """Loader de templates de relatório YAML.

    Carrega templates de arquivos YAML, valida estrutura e retorna
    objetos ReportTemplate prontos para uso pelo template engine.

    Attributes:
        default_template: Template padrão usado quando nenhum custom
            template é fornecido (default: built-in).
    """

    # Template padrão built-in (5 seções originais)
    DEFAULT_SECTIONS = [
        TemplateSection(
            id="diagnostico",
            title="Diagnóstico",
            order=1,
            content_template="{diagnosis}",
            required=True,
            placeholder="*Diagnóstico não disponível.*",
        ),
        TemplateSection(
            id="interpretacao",
            title="Interpretação Simbólica",
            order=2,
            content_template="{symbolic_interpretation}",
            required=False,
            placeholder="*Nenhuma interpretação simbólica disponível.*",
        ),
        TemplateSection(
            id="riscos",
            title="Riscos Identificados",
            order=3,
            content_template="{risks}",
            required=False,
            placeholder="*Nenhum risco identificado.*",
        ),
        TemplateSection(
            id="decisoes",
            title="Caminhos de Decisão",
            order=4,
            content_template="{decisions}",
            required=False,
            placeholder="*Nenhum caminho de decisão identificado.*",
        ),
        TemplateSection(
            id="plano",
            title="Plano Prático",
            order=5,
            content_template="{practical_plan}",
            required=False,
            placeholder="*Plano prático não disponível.*",
        ),
    ]

    def __init__(self, default_template: Optional[ReportTemplate] = None) -> None:
        self.default_template = default_template or self._build_default_template()
        logger.debug("TemplateLoader inicializado com template padrão")

    def _build_default_template(self) -> ReportTemplate:
        """Constrói o template padrão built-in.

        Returns:
            ReportTemplate com 5 seções originais do sistema.
        """
        return ReportTemplate(
            template_id="default",
            name="Modelo Padrão",
            description="Template padrão do Sistema Clareza com 5 seções fixas",
            sections=self.DEFAULT_SECTIONS,
            version="1.0",
            metadata={
                "author": "Sistema Clareza",
                "created": "2024-01-01",
            },
        )

    def load_from_file(self, template_path: Path) -> ReportTemplate:
        """Carrega template de um arquivo YAML.

        Args:
            template_path: Caminho para o arquivo YAML de template.

        Returns:
            ReportTemplate com seções carregadas do arquivo.

        Raises:
            TemplateClarezaError: Se o arquivo não existir, for inválido,
                ou se a validação falhar.
        """
        logger.info("Carregando template de: %s", template_path)

        # Carregar YAML
        data = _load_template_yaml(template_path)
        if data is None:
            raise TemplateClarezaError(
                "Template não encontrado",
                details=f"Caminho: {template_path}"
            )

        # Validar estrutura
        validator = TemplateValidator()
        errors = validator.validate(data)
        if errors:
            error_msg = "; ".join(errors)
            raise TemplateClarezaError(
                "Template inválido",
                details=error_msg
            )

        # Construir template
        template = self._build_template_from_data(data)
        logger.info("Template '%s' carregado com %d seções",
                     template.template_id, len(template.sections))

        return template

    def _build_template_from_data(self, data: dict) -> ReportTemplate:
        """Constrói ReportTemplate a partir de dados YAML parseados.

        Args:
            data: Dicionário com dados do YAML.

        Returns:
            ReportTemplate com seções parseadas.

        Raises:
            TemplateClarezaError: Se houver erro na construção.
        """
        # Extrair metadados do template
        template_id = str(data.get("template_id", "custom"))
        name = str(data.get("name", "Template Personalizado"))
        description = data.get("description")
        version = str(data.get("version", "1.0"))
        metadata = data.get("metadata", {})

        # Parsear seções
        sections_data = data.get("sections", [])
        sections = _parse_template_sections(sections_data)

        return ReportTemplate(
            template_id=template_id,
            name=name,
            description=description,
            sections=sections,
            version=version,
            metadata=metadata if isinstance(metadata, dict) else {},
        )

    def get_template(self, custom_path: Optional[Path] = None) -> ReportTemplate:
        """Retorna template para uso.

        Se custom_path for fornecido e o arquivo existir, carrega
        o template customizado. Caso contrário, retorna o template padrão.

        Args:
            custom_path: Caminho opcional para template customizado.

        Returns:
            ReportTemplate a ser usado na geração de relatórios.
        """
        if custom_path and custom_path.exists():
            return self.load_from_file(custom_path)
        logger.debug("Usando template padrão (nenhum custom_path fornecido ou arquivo não encontrado)")
        return self.default_template


# ----------------------------------------------------------------------
# Template Validator
# ----------------------------------------------------------------------


class TemplateValidationError:
    """Erro de validação de template.

    Attributes:
        field: Nome do campo que falhou na validação.
        message: Descrição legível do erro.
        value: Valor inválido fornecido (opcional).
    """

    def __init__(
        self,
        field: str,
        message: str,
        value: Optional[str] = None,
    ) -> None:
        self.field = field
        self.message = message
        self.value = value

    def __repr__(self) -> str:
        return f"TemplateValidationError(field={self.field!r}, message={self.message!r}, value={self.value!r})"

    def __str__(self) -> str:
        if self.value is not None:
            return f"{self.field}: {self.message} (valor recebido: {self.value!r})"
        return f"{self.field}: {self.message}"


class TemplateValidator:
    """Validador de templates de relatório.

    Valida estrutura de templates YAML antes de carregar,
    gerando mensagens de erro claras para valores inválidos.

    Attributes:
        required_fields: Campos obrigatórios no template YAML.
        reserved_section_ids: IDs de seção reservados (não editáveis).
    """

    REQUIRED_FIELDS = ["sections"]
    RESERVED_IDS = {"diagnostico", "interpretacao", "riscos", "decisoes", "plano"}

    def validate(self, template_data: dict) -> list[str]:
        """Valida dados de template.

        Args:
            template_data: Dicionário com dados do template a validar.

        Returns:
            Lista de mensagens de erro para cada problema encontrado.
            Lista vazia significa que o template é válido.
        """
        errors: list[str] = []

        # Validar campos obrigatórios
        for field in self.REQUIRED_FIELDS:
            if field not in template_data:
                errors.append(f"Campo obrigatório ausente: {field}")

        # Validar sections
        if "sections" in template_data:
            sections = template_data["sections"]
            if not isinstance(sections, list):
                errors.append("Campo 'sections' deve ser uma lista")
            elif len(sections) == 0:
                errors.append("Template deve ter pelo menos uma seção")
            else:
                # Validar cada seção
                section_errors = self._validate_sections(sections)
                errors.extend(section_errors)

        # Validar template_id
        if "template_id" in template_data:
            tid = template_data["template_id"]
            if not isinstance(tid, str) or not tid.strip():
                errors.append("Campo 'template_id' deve ser string não vazia")

        # Validar version
        if "version" in template_data:
            version = template_data["version"]
            if not isinstance(version, str) or not version.strip():
                errors.append("Campo 'version' deve ser string não vazia")

        return errors

    def _validate_sections(self, sections: list[dict]) -> list[str]:
        """Valida lista de seções do template.

        Args:
            sections: Lista de dicionários representando seções.

        Returns:
            Lista de mensagens de erro específicas das seções.
        """
        errors: list[str] = []
        seen_ids: set[str] = set()

        for i, section in enumerate(sections):
            if not isinstance(section, dict):
                errors.append(f"Seção {i}: deve ser um objeto")
                continue

            # Validar id
            section_id = section.get("id")
            if not section_id:
                errors.append(f"Seção {i}: campo 'id' é obrigatório")
            elif not isinstance(section_id, str) or not section_id.strip():
                errors.append(f"Seção {i}: campo 'id' deve ser string não vazia")
            elif section_id in seen_ids:
                errors.append(f"Seção {i}: ID duplicado '{section_id}'")
            else:
                seen_ids.add(section_id)

            # Validar title
            title = section.get("title")
            if not title:
                errors.append(f"Seção '{section_id or i}': campo 'title' é obrigatório")
            elif not isinstance(title, str) or not title.strip():
                errors.append(f"Seção '{section_id or i}': campo 'title' deve ser string não vazia")

            # Validar content_template
            content = section.get("content_template")
            if not content:
                errors.append(f"Seção '{section_id or i}': campo 'content_template' é obrigatório")
            elif not isinstance(content, str):
                errors.append(f"Seção '{section_id or i}': campo 'content_template' deve ser string")

            # Validar order (se presente)
            if "order" in section:
                order = section["order"]
                if not isinstance(order, int):
                    errors.append(f"Seção '{section_id or i}': campo 'order' deve ser inteiro")

            # Validar enabled (se presente)
            if "enabled" in section:
                enabled = section["enabled"]
                if not isinstance(enabled, bool):
                    errors.append(f"Seção '{section_id or i}': campo 'enabled' deve ser boolean")

            # Validar required (se presente)
            if "required" in section:
                required = section["required"]
                if not isinstance(required, bool):
                    errors.append(f"Seção '{section_id or i}': campo 'required' deve ser boolean")

        return errors

    def validate_section_order(self, sections: list[dict]) -> list[str]:
        """Valida ordenação de seções do template.

        Args:
            sections: Lista de dicionários representando seções.

        Returns:
            Lista de warnings sobre ordenação (não errors).
        """
        warnings: list[str] = []

        # Verificar se há seções required fora de ordem
        required_sections = [s for s in sections if s.get("required", False)]
        if required_sections:
            # Verificar se seções required estão entre as primeiras
            for i, section in enumerate(sections):
                if not section.get("required", False):
                    required_ids = [s.get("id") for s in required_sections]
                    if section.get("id") in required_ids:
                        warnings.append(
                            f"Seção required '{section['id']}' aparece após seções opcionais"
                        )
                    break

        return warnings