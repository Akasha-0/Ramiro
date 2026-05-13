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

    # Verificar se stdout é um terminal (safe check for mocked stdout in tests)
    stdout_is_tty = getattr(sys.stdout, 'isatty', lambda: False)()
    if not stdout_is_tty:
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


class ProgressIndicator:
    """Indicador de progresso animado para operações de longa duração.

    Exibe um spinner animado ou barra de progresso com porcentagem.
    Suporta output colorido com fallback para ambiente sem cores.

    Usage:
        # Spinner animado (para operações indeterminadas)
        progress = ProgressIndicator(total=0, description="Processando...")
        progress.start()
        # ... trabalho ...
        progress.complete("Concluído com sucesso!")

        # Barra de progresso (para operações determinísticas)
        progress = ProgressIndicator(total=100, description="Baixando")
        for i in range(100):
            progress.update(i + 1)
        progress.complete("Download concluído!")

        # Com cores desativadas (fallback automático)
        progress = ProgressIndicator(total=100, use_colors=False)
        progress.update(50)  # Mostra "50/100 (50%)"
    """

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(
        self,
        total: int = 0,
        description: str = "Processando",
        use_colors: Optional[bool] = None,
        width: int = 40,
    ) -> None:
        """Inicializa o ProgressIndicator.

        Args:
            total: Total de unidades (0 para modo spinner indeterminado).
            description: Texto descritivo da operação.
            use_colors: Override para uso de cores. Se None, usa should_use_colors().
            width: Largura da barra de progresso em caracteres (mode determinístico).
        """
        self._total = total
        self._current = 0
        self._description = description
        self._use_colors = use_colors if use_colors is not None else should_use_colors()
        self._width = width
        self._started = False
        self._completed = False
        self._frame_index = 0
        self._last_output_len = 0

    @property
    def total(self) -> int:
        """Retorna o total de unidades."""
        return self._total

    @property
    def current(self) -> int:
        """Retorna o progresso atual."""
        return self._current

    @property
    def is_deterministic(self) -> bool:
        """Retorna True se o progresso é determinístico (tem total > 0)."""
        return self._total > 0

    def _get_spinner_frame(self) -> str:
        """Retorna o próximo frame do spinner animado."""
        frame = self.SPINNER_FRAMES[self._frame_index]
        self._frame_index = (self._frame_index + 1) % len(self.SPINNER_FRAMES)
        return frame

    def _format_output(self, message: str) -> str:
        """Formata a mensagem com cores (se habilitado).

        Args:
            message: Mensagem a ser formatada.

        Returns:
            Mensagem formatada com códigos ANSI (se cores habilitadas).
        """
        if self._use_colors:
            return f"{Color.CYAN.value}{message}{Color.RESET.value}"
        return message

    def _clear_line(self) -> None:
        """Limpa a linha anterior do terminal."""
        if self._last_output_len > 0:
            sys.stdout.write("\r" + " " * self._last_output_len + "\r")
            sys.stdout.flush()
            self._last_output_len = 0

    def _get_progress_bar(self) -> str:
        """Retorna a barra de progresso formatada.

        Returns:
            Barra de progresso em formato de string.
        """
        if self._total == 0:
            return ""

        filled = int(self._width * self._current / self._total) if self._total > 0 else 0
        bar_width = self._width - 2  # Espaço para brackets
        filled = min(filled, bar_width)
        empty = bar_width - filled

        bar = f"[{'#' * filled}{'-' * empty}]"
        percent = int(100 * self._current / self._total) if self._total > 0 else 0
        return f"{bar} {self._current}/{self._total} ({percent}%)"

    def start(self) -> None:
        """Inicia o indicador de progresso.

        Exibe a mensagem inicial de progresso.
        """
        self._started = True
        self._current = 0
        self._completed = False
        self._frame_index = 0

        if self.is_deterministic:
            message = f"{self._description}: {self._get_progress_bar()}"
        else:
            message = f"{self._get_spinner_frame()} {self._description}"

        output = self._format_output(message)
        sys.stdout.write(output)
        sys.stdout.flush()
        self._last_output_len = len(message)

    def update(self, current: int) -> None:
        """Atualiza o progresso para o valor especificado.

        Args:
            current: Valor atual do progresso.
        """
        if not self._started or self._completed:
            return

        self._current = max(0, min(current, self._total)) if self._total > 0 else current

        self._clear_line()

        if self.is_deterministic:
            message = f"{self._description}: {self._get_progress_bar()}"
        else:
            message = f"{self._get_spinner_frame()} {self._description}"

        output = self._format_output(message)
        sys.stdout.write(output)
        sys.stdout.flush()
        self._last_output_len = len(message)

    def complete(self, message: str = "Concluído!") -> None:
        """Finaliza o indicador de progresso.

        Args:
            message: Mensagem de conclusão.
        """
        self._completed = True
        self._clear_line()

        if self._use_colors:
            output = f"{Color.BRIGHT_GREEN.value}✓{Color.RESET.value} {message}"
        else:
            output = f"[OK] {message}"

        sys.stdout.write(output + "\n")
        sys.stdout.flush()
        self._last_output_len = 0

    def error(self, message: str = "Erro!") -> None:
        """Finaliza o indicador com mensagem de erro.

        Args:
            message: Mensagem de erro.
        """
        self._completed = True
        self._clear_line()

        if self._use_colors:
            output = f"{Color.BRIGHT_RED.value}✗{Color.RESET.value} {message}"
        else:
            output = f"[ERRO] {message}"

        sys.stdout.write(output + "\n")
        sys.stdout.flush()
        self._last_output_len = 0


def create_progress(
    total: int = 0,
    description: str = "Processando",
    use_colors: Optional[bool] = None,
) -> ProgressIndicator:
    """Factory function para criar um ProgressIndicator.

    Args:
        total: Total de unidades (0 para modo spinner indeterminado).
        description: Texto descritivo da operação.
        use_colors: Override para uso de cores. Se None, usa should_use_colors().

    Returns:
        Nova instância de ProgressIndicator configurada.
    """
    return ProgressIndicator(
        total=total,
        description=description,
        use_colors=use_colors,
    )