"""Exceções do Sistema de Clareza Simbólico-Estratégica.

Este módulo define a hierarquia de exceções usada em todo o sistema.
Cada exceção inclui mensagens descritivas em português para melhor
experiência do usuário.

Exceptions hierarchy:
    ClarezaError (base)
    ├── FileNotFoundClarezaError
    ├── ParseClarezaError
    ├── ValidationClarezaError
    ├── TemplateClarezaError
    └── ConfigurationClarezaError
"""

from typing import Optional


class ClarezaError(Exception):
    """Exceção base do sistema Clareza.

    Todas as exceções específicas do sistema herdam desta classe base.
    Fornece atributos comuns para mensagens descritivas e contexto do erro.

    Attributes:
        message: Descrição legível do erro em português.
        details: Detalhes adicionais sobre a causa do erro (opcional).
    """

    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
    ) -> None:
        self.message = message
        self.details = details
        full = message
        if details:
            full = f"{message}: {details}"
        super().__init__(full)


class FileNotFoundClarezaError(ClarezaError):
    """Exceção lançada quando um arquivo não é encontrado.

    Attributes:
        file_path: Caminho do arquivo que não foi encontrado.
        details: Detalhes adicionais sobre o contexto da busca.
    """

    def __init__(
        self,
        file_path: str,
        details: Optional[str] = None,
    ) -> None:
        self.file_path = file_path
        message = "Arquivo não encontrado"
        full_details = f"Caminho: {file_path!r}"
        if details:
            full_details = f"{full_details} — {details}"
        super().__init__(message, full_details)


class ParseClarezaError(ClarezaError):
    """Exceção lançada quando o parse de entrada falha.

    Attributes:
        line: Número da linha onde ocorreu o erro (para CSV, opcional).
        details: Detalhes adicionais sobre a natureza do erro.
    """

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        details: Optional[str] = None,
    ) -> None:
        self.line = line
        full = message
        if line is not None:
            full = f"{message} (linha {line})"
        if details:
            full = f"{full}: {details}"
        super().__init__(message, f"{'(linha ' + str(line) + ') ' if line else ''}{details}" if details else None)


class ValidationClarezaError(ClarezaError):
    """Exceção lançada quando a validação de dados falha.

    Attributes:
        field: Nome do campo que falhou na validação.
        details: Detalhes adicionais sobre a regra violada.
    """

    def __init__(
        self,
        field: str,
        details: Optional[str] = None,
    ) -> None:
        self.field = field
        message = f"Validação falhou para o campo: {field}"
        super().__init__(message, details)


class TemplateClarezaError(ClarezaError):
    """Exceção lançada quando um template não é encontrado ou é inválido.

    Attributes:
        template_name: Nome do template que causou o erro.
        available: Lista de templates disponíveis (opcional).
    """

    def __init__(
        self,
        template_name: str,
        available: Optional[list[str]] = None,
    ) -> None:
        self.template_name = template_name
        self.available = available
        message = "Template não encontrado"
        details = f"Template: {template_name!r}"
        if available:
            details = f"{details}. Templates disponíveis: {', '.join(available)}"
        super().__init__(message, details)


class ConfigurationClarezaError(ClarezaError):
    """Exceção lançada quando há erro de configuração do sistema.

    Attributes:
        config_key: Chave de configuração que causou o erro.
        details: Detalhes adicionais sobre o erro de configuração.
    """

    def __init__(
        self,
        config_key: str,
        details: Optional[str] = None,
    ) -> None:
        self.config_key = config_key
        message = "Erro de configuração"
        full_details = f"Chave: {config_key!r}"
        if details:
            full_details = f"{full_details} — {details}"
        super().__init__(message, full_details)
