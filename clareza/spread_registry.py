"""Registro de tiragens — Sistema de Clareza Simbólico-Estratégica.

Módulo que gerencia o registro de templates de tiragens, incluindo
templates built-in e templates customizados da comunidade.

Attributes:
    SpreadRegistry: Classe principal para gerenciar templates de tiragens.
    TemplateRegistrationError: Exceção para erros de registro de template.
    DEFAULT_SPREADS_PATH: Caminho padrão para o arquivo de registry.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from clareza.spread_templates import TEMPLATES, SpreadTemplate, get_template, list_templates

logger = logging.getLogger(__name__)

# Path constant for the registry file
DEFAULT_SPREADS_PATH = Path.home() / ".clareza" / "spreads.json"


class TemplateRegistrationError(Exception):
    """Erro ao registrar um novo template.

    Attributes:
        template_name: Nome do template que falhou no registro.
        reason: Motivo do erro.
    """

    def __init__(
        self,
        template_name: str,
        reason: str,
    ) -> None:
        self.template_name = template_name
        self.reason = reason
        super().__init__(f"Erro ao registrar template '{template_name}': {reason}")


@dataclass
class RegistryMetadata:
    """Metadados de um template registrado.

    Attributes:
        template_name: Nome interno do template.
        source: Origem do template ("builtin", "community", "custom").
        author: Autor do template (None para templates built-in).
        created_at: Timestamp de criação (ISO format).
        registered_at: Timestamp de registro no registry.
        version: Versão do template.
        tags: Lista de tags para categorização.
    """

    template_name: str
    source: str = "builtin"
    author: Optional[str] = None
    created_at: Optional[str] = None
    registered_at: Optional[str] = None
    version: str = "1.0"
    tags: list[str] = field(default_factory=list)


class SpreadRegistry:
    """Registro de templates de tiragens.

    Gerencia templates built-in e templates customizados/comunidade.
    Permite registro, recuperação, listagem e validação de templates.

    Attributes:
        _templates: Dicionário de templates registrados (nome -> SpreadTemplate).
        _metadata: Dicionário de metadados (nome -> RegistryMetadata).
    """

    def __init__(
        self,
        include_builtin: bool = True,
    ) -> None:
        """Inicializa o registry de tiragens.

        Args:
            include_builtin: Se True, carrega templates built-in automaticamente.
        """
        self._templates: dict[str, SpreadTemplate] = {}
        self._metadata: dict[str, RegistryMetadata] = {}

        if include_builtin:
            self._load_builtin_templates()

        logger.debug("SpreadRegistry inicializado com %d templates", len(self._templates))

    def _load_builtin_templates(self) -> None:
        """Carrega todos os templates built-in no registry."""
        for name in list_templates():
            template = get_template(name)
            if template is not None:
                self._templates[name] = template
                self._metadata[name] = RegistryMetadata(
                    template_name=name,
                    source="builtin",
                    version="1.0",
                )
        logger.debug("Templates built-in carregados: %s", list(self._templates.keys()))

    def register(
        self,
        template: SpreadTemplate,
        author: Optional[str] = None,
        version: str = "1.0",
        tags: Optional[list[str]] = None,
        created_at: Optional[str] = None,
    ) -> None:
        """Registra um novo template no registry.

        Args:
            template: Template a ser registrado.
            author: Autor do template (None para templates anônimos).
            version: Versão do template.
            tags: Lista de tags para categorização.
            created_at: Timestamp de criação do template.

        Raises:
            TemplateRegistrationError: Se o template já existe ou é inválido.
        """
        if not self._validate_template(template):
            raise TemplateRegistrationError(
                template.name,
                "Template inválido: faltam campos obrigatórios",
            )

        if template.name in self._templates:
            raise TemplateRegistrationError(
                template.name,
                f"Template já registrado (use update() para substituir)",
            )

        source = "community" if author else "custom"

        self._templates[template.name] = template
        self._metadata[template.name] = RegistryMetadata(
            template_name=template.name,
            source=source,
            author=author,
            version=version,
            tags=tags or [],
            created_at=created_at,
            registered_at=self._get_current_timestamp(),
        )

        logger.info(
            "Template '%s' registrado (source=%s, author=%s)",
            template.name,
            source,
            author,
        )

    def _validate_template(self, template: SpreadTemplate) -> bool:
        """Valida um template antes do registro.

        Args:
            template: Template a ser validado.

        Returns:
            True se o template é válido, False caso contrário.
        """
        if not template.name or not template.name.strip():
            return False

        if not template.display_name or not template.display_name.strip():
            return False

        if not template.description or not template.description.strip():
            return False

        if not template.positions or len(template.positions) == 0:
            return False

        # Verificar se todas as posições têm context e description
        for pos in template.positions:
            if not pos.context or not pos.context.strip():
                return False
            if not pos.description or not pos.description.strip():
                return False

        return True

    def _get_current_timestamp(self) -> str:
        """Retorna timestamp atual em formato ISO.

        Returns:
            String com timestamp ISO.
        """
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def get(self, name: str) -> Optional[SpreadTemplate]:
        """Recupera um template pelo nome.

        Args:
            name: Nome interno do template.

        Returns:
            SpreadTemplate correspondente ou None se não existir.
        """
        return self._templates.get(name)

    def get_metadata(self, name: str) -> Optional[RegistryMetadata]:
        """Recupera metadados de um template.

        Args:
            name: Nome interno do template.

        Returns:
            RegistryMetadata correspondente ou None se não existir.
        """
        return self._metadata.get(name)

    def list_names(self, source: Optional[str] = None) -> list[str]:
        """Lista nomes de todos os templates registrados.

        Args:
            source: Filtro por origem ("builtin", "community", "custom").
                    Se None, lista todos.

        Returns:
            Lista de nomes de templates.
        """
        if source is None:
            return list(self._templates.keys())

        return [
            name
            for name, meta in self._metadata.items()
            if meta.source == source
        ]

    def list_by_tag(self, tag: str) -> list[str]:
        """Lista templates que possuem uma tag específica.

        Args:
            tag: Tag a buscar.

        Returns:
            Lista de nomes de templates com a tag.
        """
        return [
            name
            for name, meta in self._metadata.items()
            if tag in meta.tags
        ]

    def unregister(self, name: str) -> bool:
        """Remove um template do registry.

        Args:
            name: Nome do template a remover.

        Returns:
            True se o template foi removido, False se não existia.

        Raises:
            TemplateRegistrationError: Se tentar remover template built-in.
        """
        if name not in self._templates:
            logger.debug("Template '%s' não encontrado para remoção", name)
            return False

        meta = self._metadata.get(name)
        if meta and meta.source == "builtin":
            raise TemplateRegistrationError(
                name,
                "Não é possível remover templates built-in",
            )

        del self._templates[name]
        if name in self._metadata:
            del self._metadata[name]

        logger.info("Template '%s' removido do registry", name)
        return True

    def exists(self, name: str) -> bool:
        """Verifica se um template existe no registry.

        Args:
            name: Nome do template.

        Returns:
            True se existe, False caso contrário.
        """
        return name in self._templates

    def count(self, source: Optional[str] = None) -> int:
        """Conta templates no registry.

        Args:
            source: Filtro por origem ("builtin", "community", "custom").
                    Se None, conta todos.

        Returns:
            Número de templates.
        """
        if source is None:
            return len(self._templates)
        return len([m for m in self._metadata.values() if m.source == source])

    def get_all_with_metadata(self) -> list[tuple[SpreadTemplate, RegistryMetadata]]:
        """Retorna todos os templates com seus metadados.

        Returns:
            Lista de tuplas (SpreadTemplate, RegistryMetadata).
        """
        return [
            (self._templates[name], self._metadata[name])
            for name in self._templates.keys()
            if name in self._metadata
        ]

    def save(self, path: Optional[Path] = None) -> None:
        """Salva o registry em um arquivo JSON.

        Args:
            path: Caminho do arquivo. Se None, usa DEFAULT_SPREADS_PATH.

        Raises:
            TemplateRegistrationError: Se houver erro ao salvar.
        """
        path = path or DEFAULT_SPREADS_PATH

        # Only save non-builtin templates (built-in are hardcoded)
        custom_spreads = []
        for name in self._templates.keys():
            meta = self._metadata.get(name)
            if meta and meta.source != "builtin":
                template = self._templates[name]
                custom_spreads.append({
                    "name": template.name,
                    "display_name": template.display_name,
                    "description": template.description,
                    "positions": [
                        {
                            "position": pos.position,
                            "context": pos.context,
                            "description": pos.description,
                        }
                        for pos in template.positions
                    ],
                    "author": meta.author,
                    "version": meta.version,
                    "tags": meta.tags,
                })

        data = {
            "version": "1.0",
            "spreads": custom_spreads,
        }

        try:
            # Create directory if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Registry salvo em %s (%d templates)", path, len(custom_spreads))
        except OSError as e:
            raise TemplateRegistrationError(
                "registry",
                f"Erro ao salvar arquivo: {e}",
            )

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "SpreadRegistry":
        """Carrega o registry de um arquivo JSON.

        Args:
            path: Caminho do arquivo. Se None, usa DEFAULT_SPREADS_PATH.

        Returns:
            SpreadRegistry com templates carregados do arquivo.

        Raises:
            TemplateRegistrationError: Se o arquivo for inválido.
        """
        path = path or DEFAULT_SPREADS_PATH

        if not path.exists():
            # Return empty registry if file doesn't exist
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise TemplateRegistrationError(
                "registry",
                f"JSON inválido: {e}",
            )
        except OSError as e:
            raise TemplateRegistrationError(
                "registry",
                f"Erro ao ler arquivo: {e}",
            )

        registry = cls()

        # Parse spreads from JSON
        spreads = data.get("spreads", [])
        for spread_data in spreads:
            try:
                positions = [
                    SpreadPosition(
                        position=pos["position"],
                        context=pos["context"],
                        description=pos["description"],
                    )
                    for pos in spread_data.get("positions", [])
                ]

                template = SpreadTemplate(
                    name=spread_data["name"],
                    display_name=spread_data.get("display_name", spread_data["name"]),
                    description=spread_data.get("description", ""),
                    positions=positions,
                )

                author = spread_data.get("author")
                version = spread_data.get("version", "1.0")
                tags = spread_data.get("tags", [])

                registry.register(
                    template,
                    author=author,
                    version=version,
                    tags=tags,
                )
                logger.debug("Template '%s' carregado do registry", template.name)
            except (KeyError, ValueError) as e:
                logger.warning(
                    "Erro ao carregar template '%s': %s",
                    spread_data.get("name", "?"),
                    e,
                )
                continue

        return registry

    @classmethod
    def load_or_empty(cls, path: Optional[Path] = None) -> "SpreadRegistry":
        """Carrega o registry ou retorna um registry vazio em caso de erro.

        Args:
            path: Caminho do arquivo. Se None, usa DEFAULT_SPREADS_PATH.

        Returns:
            SpreadRegistry (carregado ou vazio).
        """
        try:
            return cls.load(path)
        except TemplateRegistrationError:
            # Log warning and return empty registry
            logger.warning("Falha ao carregar registry, retornando vazio")
            return cls()