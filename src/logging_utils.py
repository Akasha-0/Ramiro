"""Utilitários de logging com suporte a cores e configuração verbose.

Módulo para configuração centralizada de logging com:
- Suporte a cores ANSI (respeitando NO_COLOR e TERM=dumb)
- Níveis de logging configuráveis (INFO/DEBUG)
- Funções auxiliares para output formatado

Usage:
    from src.logging_utils import setup_logging, should_use_colors, Color

    # Configurar logging com verbose
    setup_logging(verbose=True)  # DEBUG level

    # Verificar se cores devem ser usadas
    if should_use_colors():
        print(f"{Color.ERROR}Erro: algo falhou{Color.RESET}")
"""

import logging
import os
import sys
from enum import Enum
from typing import Optional


class Color(Enum):
    """Cores ANSI para output terminal.

    Cada cor inclui o código de escape ANSI correspondente.
    Use Color.RESET para restaurar a formatação padrão.
    """

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Cores de texto
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Cores de fundo
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

    # Coresbright
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"


def should_use_colors() -> bool:
    """Verifica se cores ANSI devem ser usadas no terminal.

    Retorna False se qualquer uma das seguintes condições for verdadeira:
    - Variável de ambiente NO_COLOR está definida
    - Variável de ambiente TERM é 'dumb'
    - stdout não é um terminal (tty)

    Returns:
        True se cores devem ser usadas, False caso contrário.
    """
    # Verificar NO_COLOR (convenção padrão)
    if os.environ.get("NO_COLOR"):
        return False

    # Verificar TERM=dumb (terminal sem suporte a cores)
    if os.environ.get("TERM") == "dumb":
        return False

    # Verificar se stdout é um terminal
    if not sys.stdout.isatty():
        return False

    return True


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configura o sistema de logging global.

    Args:
        verbose: Se True, configura nível DEBUG; caso contrário, INFO.

    Returns:
        Logger configurado para o módulo chamador (__name__).
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,  # Permite reconfiguração
    )

    logger = logging.getLogger(__name__)
    if verbose:
        logger.debug("Logging configurado em modo DEBUG")
    else:
        logger.info("Logging configurado em modo INFO")

    return logger


def configure_module_logger(
    module_name: str,
    verbose: bool = False,
) -> logging.Logger:
    """Configura um logger para um módulo específico.

    Args:
        module_name: Nome do módulo para o logger.
        verbose: Se True, configura nível DEBUG; caso contrário, INFO.

    Returns:
        Logger configurado para o módulo especificado.
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    return logger


class ColoredOutput:
    """Helper para output colorido com fallback automático.

    Usage:
        out = ColoredOutput()
        print(out.error("Falha ao processar arquivo"))
        print(out.success("Operação concluída"))
        print(out.warning("Verifique os dados"))
        print(out.info("Processando..."))
    """

    def __init__(self, use_colors: Optional[bool] = None) -> None:
        """Inicializa ColoredOutput.

        Args:
            use_colors: Override para uso de cores. Se None, usa should_use_colors().
        """
        self._use_colors = use_colors if use_colors is not None else should_use_colors()

    @property
    def use_colors(self) -> bool:
        """Retorna se cores devem ser usadas."""
        return self._use_colors

    def _colorize(self, text: str, color: Color) -> str:
        """Aplica cor a um texto.

        Args:
            text: Texto a ser colorido.
            color: Cor a aplicar.

        Returns:
            Texto com código de escape ANSI (se cores ativadas) ou texto original.
        """
        if self._use_colors:
            return f"{color.value}{text}{Color.RESET.value}"
        return text

    def error(self, text: str) -> str:
        """Texto de erro em vermelho."""
        return self._colorize(text, Color.BRIGHT_RED)

    def success(self, text: str) -> str:
        """Texto de sucesso em verde."""
        return self._colorize(text, Color.BRIGHT_GREEN)

    def warning(self, text: str) -> str:
        """Texto de aviso em amarelo."""
        return self._colorize(text, Color.BRIGHT_YELLOW)

    def info(self, text: str) -> str:
        """Texto informativo em ciano."""
        return self._colorize(text, Color.BRIGHT_CYAN)

    def bold(self, text: str) -> str:
        """Texto em negrito."""
        return self._colorize(text, Color.BOLD)

    def dim(self, text: str) -> str:
        """Texto em modo dim (menos destaque)."""
        return self._colorize(text, Color.DIM)


def get_colored_output() -> ColoredOutput:
    """Retorna uma instância de ColoredOutput com configuração atual.

    Returns:
        ColoredOutput configurado com base no ambiente atual.
    """
    return ColoredOutput()